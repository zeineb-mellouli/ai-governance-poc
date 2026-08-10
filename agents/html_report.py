"""Render a batch of compliance reports as one self-contained HTML page.

Why one page for the whole batch rather than a page per repository: the thing a
reader needs first is the comparison -- which repositories are in trouble and how
badly -- and that only exists across repositories. A per-repo page would put the
comparison nowhere.

Two information-design decisions drive the layout:

1. 87% of the rows in a run are not violations (302 passing + 153 not-applicable
   against 69 violations, on the reference corpus). Those rows matter for the
   denominator and nobody reads them, so they are reported as counts and the
   page leads with the violations.

2. Evidence is rendered as code, in monospace, verbatim. It is the element that
   turns "a language model said so" into "here is the line, judge it yourself",
   which is the whole argument for trusting the tool. Everything else on the
   page is chrome around it.

No external requests: styles are inline and there are no scripts, so the file
works from disk, over email, and inside a CI artifact viewer.
"""

import ast
import html
import re
from datetime import datetime, timezone

from agents.schemas import ComplianceReport, Finding, FindingStatus

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

# The auditor packs the quoted line and any routing annotation into the evidence
# string. Split them back out so each can be styled for what it is.
_ANNOTATION_RE = re.compile(r"\s{2}(\[[^\]]*\])\s*$")
_QUOTED_RE = re.compile(r"\s{2}Quoted:\s(.+)$", re.DOTALL)


def _split_evidence(evidence: str) -> tuple[str, str | None, str | None]:
    """Return (sentence, quoted_line, annotation) from a packed evidence string."""
    annotation = None
    match = _ANNOTATION_RE.search(evidence)
    if match:
        annotation = match.group(1)
        evidence = evidence[: match.start()]

    quote = None
    match = _QUOTED_RE.search(evidence)
    if match:
        raw = match.group(1).strip()
        try:
            quote = ast.literal_eval(raw)          # the auditor stores it as a repr
        except (ValueError, SyntaxError):
            quote = raw
        evidence = evidence[: match.start()]

    return evidence.strip(), quote, annotation


def _esc(text: object) -> str:
    return html.escape(str(text), quote=True)


# --- pieces ------------------------------------------------------------------


def _stat(value: str, label: str, tone: str = "") -> str:
    cls = f"stat {tone}".strip()
    return (
        f'<div class="{cls}"><span class="stat-value">{_esc(value)}</span>'
        f'<span class="stat-label">{_esc(label)}</span></div>'
    )


def _severity_pill(high: int, medium: int, low: int) -> str:
    """Counts by severity, in place of the pass/fail verdict that used to sit here.
    A fact about the repository rather than an opinion about it."""
    parts = []
    for count, name in ((high, "high"), (medium, "medium"), (low, "low")):
        if count:
            parts.append(f'<span class="pill sev-{name}">{count} {name}</span>')
    return "".join(parts) or '<span class="pill sev-none">no violations</span>'


def _rate_bar(rate: float | None, high: int) -> str:
    """The bar is tinted by whether any high-severity violation exists -- an
    observed property, not a graded one."""
    if rate is None:
        return '<span class="muted">—</span>'
    tone = "has-high" if high else "no-high"
    return (
        f'<div class="rate"><div class="rate-track">'
        f'<div class="rate-fill {tone}" style="width:{rate * 100:.4f}%"></div>'
        f'</div><span class="rate-num">{rate:.1%}</span></div>'
    )


def _finding_card(finding: Finding) -> str:
    sentence, quote, annotation = _split_evidence(finding.evidence)
    severity = finding.severity
    parts = [f'<article class="finding sev-{_esc(severity.lower())}">']
    parts.append(
        '<header class="finding-head">'
        f'<span class="chip sev-chip">{_esc(severity)}</span>'
        f'<span class="policy">{_esc(finding.policy_id)}</span>'
        f'<span class="policy-title">{_esc(finding.title)}</span>'
        f'<code class="loc">{_esc(finding.file_path or "repository-level")}</code>'
        "</header>"
    )
    if sentence:
        parts.append(f'<p class="verdict">{_esc(sentence)}</p>')
    if quote:
        parts.append(
            '<div class="evidence"><span class="evidence-label">evidence</span>'
            f'<pre><code>{_esc(quote)}</code></pre></div>'
        )
    if finding.remediation:
        # Every NAM-5 file rename is computed from the filename by a total
        # function and re-checked before it is offered; everything else was
        # written by the model and is unverified. Saying which is which stops the
        # page implying the same confidence in both.
        computed = finding.policy_id == "NAM-5" and finding.confidence_score == 1.0
        label = "computed fix" if computed else "suggested fix"
        parts.append(
            f'<div class="fix {"fix-computed" if computed else ""}">'
            f'<span class="fix-label">{label}</span>'
            f'<p class="fix-desc">{_esc(finding.remediation.description)}</p>'
            f"<pre><code>{_esc(finding.remediation.fix)}</code></pre></div>"
        )
    if finding.confidence_score < 1.0 or annotation:
        note = annotation or f"[{finding.confidence_score:.0%} sample agreement]"
        parts.append(f'<p class="agreement">{_esc(note.strip("[]"))}</p>')
    parts.append("</article>")
    return "".join(parts)


def _repo_section(report: ComplianceReport, open_by_default: bool) -> str:
    score = report.compliance_score
    summary = report.summary
    findings = report.findings

    violations = sorted(
        (f for f in findings if f.status == FindingStatus.NON_COMPLIANT),
        key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), -f.confidence_score, f.policy_id),
    )
    # The uncertainty section holds two things a reviewer can act on: verdicts
    # the samples could not settle, and *passes* the samples disagreed about --
    # a check that two of three runs called clean and one called a violation is
    # a near miss worth a second look.
    #
    # It deliberately excludes NOT_APPLICABLE (39 of the 56 sub-unanimous rows on
    # the reference corpus): disagreeing about whether a policy even applies to a
    # file is not a finding, and burying 15 real near-misses under it defeats the
    # section. Violations are excluded too -- they are already listed above, with
    # their agreement rate shown on the card.
    undecided = [f for f in findings if f.status == FindingStatus.NEEDS_REVIEW]
    near_misses = [
        f for f in findings
        if f.status == FindingStatus.COMPLIANT and f.confidence_score < 1.0
    ]
    passed = summary["by_status"].get("COMPLIANT", 0)
    skipped = summary["by_status"].get("NOT_APPLICABLE", 0)

    out = [f'<details class="repo" {"open" if open_by_default else ""}>']
    out.append(
        '<summary class="repo-head">'
        f'<span class="repo-name">{_esc(report.repo_name)}</span>'
        f"{_severity_pill(score['high_failures'], score['medium_failures'], score['low_failures'])}"
        f"{_rate_bar(score['weighted_pass_rate'], score['high_failures'])}"
        f'<span class="repo-counts">'
        f'<b>{len(violations)}</b> violations · {passed} passed · {skipped} n/a'
        "</span></summary>"
    )
    out.append('<div class="repo-body">')

    if violations:
        current = None
        for finding in violations:
            if finding.severity != current:
                if current is not None:
                    out.append("</div>")
                current = finding.severity
                count = sum(1 for f in violations if f.severity == current)
                out.append(
                    f'<div class="sev-group"><h4 class="sev-head sev-{_esc(current.lower())}">'
                    f"{_esc(current)} <span class=\"muted\">· {count}</span></h4>"
                )
            out.append(_finding_card(finding))
        out.append("</div>")
    else:
        out.append('<p class="clean">No violations. Every applicable check passed.</p>')

    if undecided or near_misses:
        detail = []
        if undecided:
            detail.append(f"{len(undecided)} the samples could not settle")
        if near_misses:
            detail.append(f"{len(near_misses)} passed, but not unanimously")
        out.append(
            '<div class="unsure-block"><h4 class="unsure-head">Where the audit was not certain</h4>'
            f'<p class="unsure-intro">Each check is run {report.audit_samples} times and the '
            f"verdict is the majority — {', '.join(detail)}.</p>"
        )
        for finding in undecided + near_misses:
            out.append(_finding_card(finding))
        out.append("</div>")

    if report.errors:
        out.append('<div class="errors"><h4>Partial failures during the run</h4><ul>')
        out.extend(f"<li>{_esc(e)}</li>" for e in report.errors)
        out.append("</ul></div>")

    out.append("</div></details>")
    return "".join(out)


def _overview_row(report: ComplianceReport) -> str:
    score = report.compliance_score
    counts = report.summary["by_status"]
    violations = counts.get("NON_COMPLIANT", 0)
    return (
        "<tr>"
        f'<td class="repo-cell">{_esc(report.repo_name)}</td>'
        f"<td class=\"rate-cell\">{_rate_bar(score['weighted_pass_rate'], score['high_failures'])}</td>"
        f'<td class="num {"has-viol" if score["high_failures"] else ""}">{score["high_failures"] or "—"}</td>'
        f'<td class="num {"has-viol" if violations else ""}">{violations}</td>'
        f'<td class="num muted">{counts.get("COMPLIANT", 0)}</td>'
        f'<td class="num muted">{counts.get("NOT_APPLICABLE", 0)}</td>'
        f'<td class="num">{report.summary["needs_human_attention"] or "—"}</td>'
        "</tr>"
    )


# --- page --------------------------------------------------------------------


def render_batch_html(reports: list[ComplianceReport], title: str = "Governance audit") -> str:
    # Worst first: most high-severity violations, then lowest pass rate.
    ordered = sorted(
        reports,
        key=lambda r: (-r.compliance_score["high_failures"],
                       r.compliance_score["weighted_pass_rate"] or 0.0),
    )

    total_violations = sum(r.summary["by_status"].get("NON_COMPLIANT", 0) for r in reports)
    total_checks = sum(r.summary["applicable_checks"] for r in reports)
    high = sum(r.compliance_score["high_failures"] for r in reports)
    clean = sum(1 for r in reports if not r.summary["by_status"].get("NON_COMPLIANT", 0))
    samples = sorted({r.audit_samples for r in reports})
    fingerprints = sorted({fp for r in reports for fp in r.model_fingerprints})

    stats = "".join([
        _stat(str(len(reports)), "repositories"),
        _stat(str(total_violations), "violations", "tone-bad" if total_violations else "tone-good"),
        _stat(str(high), "high severity", "tone-bad" if high else "tone-good"),
        _stat(f"{clean}/{len(reports)}", "with no violations", "tone-good" if clean else ""),
        _stat(str(total_checks), "applicable checks"),
    ])

    meta = [f"k = {', '.join(str(s) for s in samples)}"]
    if fingerprints:
        meta.append("backend " + ", ".join(fingerprints))
    meta.append(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    body = [
        '<div class="wrap">',
        "<header class=\"masthead\">",
        f"<h1>{_esc(title)}</h1>",
        f'<p class="meta">{" · ".join(_esc(m) for m in meta)}</p>',
        "</header>",
        f'<section class="stats">{stats}</section>',
        '<section class="overview"><h2>Repositories</h2>',
        '<div class="table-scroll"><table>',
        "<thead><tr><th>Repository</th><th>Weighted pass rate</th>"
        '<th class="num">High</th><th class="num">Violations</th><th class="num">Passed</th>'
        '<th class="num">N/A</th><th class="num">To action</th></tr></thead><tbody>',
        "".join(_overview_row(r) for r in ordered),
        "</tbody></table></div>",
        '<p class="footnote">Not-applicable checks are excluded from the pass rate — '
        "a check correctly skipped is not a check passed. Undecided verdicts are excluded "
        "from both sides and shown per repository below.</p>",
        "</section>",
        '<section class="detail"><h2>Findings</h2>',
    ]
    body.extend(_repo_section(r, open_by_default=(i == 0)) for i, r in enumerate(ordered))
    body.append("</section></div>")

    return _PAGE.format(title=_esc(title), styles=_STYLES, body="".join(body))


_STYLES = """
:root{
  --paper:#f5f6f8; --surface:#ffffff; --surface-2:#eef1f5;
  --ink:#151b24; --ink-2:#3c4653; --muted:#6b7684; --rule:#dfe3e9;
  --accent:#2f4a7c;
  --high:#b3261e; --medium:#8a5a00; --low:#4a5568; --good:#1f6f4a;
  --high-bg:#fdeceb; --medium-bg:#fbf3e2; --low-bg:#eef0f3; --good-bg:#e7f3ec;
  --code-bg:#f0f2f6;
  --sans:ui-sans-serif,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,"JetBrains Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){
  :root{
    --paper:#10141a; --surface:#171d26; --surface-2:#1e2530;
    --ink:#e6eaf0; --ink-2:#c2cad5; --muted:#8d99a8; --rule:#28313d;
    --accent:#8fb0e8;
    --high:#f2887f; --medium:#e0b262; --low:#9aa7b6; --good:#68c295;
    --high-bg:#2a1614; --medium-bg:#2a2113; --low-bg:#1e2530; --good-bg:#12261d;
    --code-bg:#0d1116;
  }
}
:root[data-theme="dark"]{
  --paper:#10141a; --surface:#171d26; --surface-2:#1e2530;
  --ink:#e6eaf0; --ink-2:#c2cad5; --muted:#8d99a8; --rule:#28313d;
  --accent:#8fb0e8;
  --high:#f2887f; --medium:#e0b262; --low:#9aa7b6; --good:#68c295;
  --high-bg:#2a1614; --medium-bg:#2a2113; --low-bg:#1e2530; --good-bg:#12261d;
  --code-bg:#0d1116;
}
:root[data-theme="light"]{
  --paper:#f5f6f8; --surface:#ffffff; --surface-2:#eef1f5;
  --ink:#151b24; --ink-2:#3c4653; --muted:#6b7684; --rule:#dfe3e9;
  --accent:#2f4a7c;
  --high:#b3261e; --medium:#8a5a00; --low:#4a5568; --good:#1f6f4a;
  --high-bg:#fdeceb; --medium-bg:#fbf3e2; --low-bg:#eef0f3; --good-bg:#e7f3ec;
  --code-bg:#f0f2f6;
}

*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:var(--sans);font-size:15px;line-height:1.55;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:40px 24px 96px;
  display:flex;flex-direction:column;gap:38px}
h1,h2,h3,h4{margin:0;text-wrap:balance;font-weight:600}
h1{font-size:1.75rem;letter-spacing:-.015em}
h2{font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);
  padding-bottom:10px;border-bottom:1px solid var(--rule)}
.muted{color:var(--muted)}
.num,.rate-num,td.num{font-variant-numeric:tabular-nums}

.masthead{display:flex;flex-direction:column;gap:6px}
.meta{margin:0;font-family:var(--mono);font-size:.75rem;color:var(--muted)}

.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:1px;
  background:var(--rule);border:1px solid var(--rule);border-radius:3px;overflow:hidden}
.stat{background:var(--surface);padding:16px 18px;display:flex;flex-direction:column;gap:3px}
.stat-value{font-size:1.7rem;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat-label{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.tone-bad .stat-value{color:var(--high)}
.tone-good .stat-value{color:var(--good)}

.overview{display:flex;flex-direction:column;gap:14px}
.table-scroll{overflow-x:auto;border:1px solid var(--rule);border-radius:3px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:.875rem}
th{text-align:left;font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;
  color:var(--muted);font-weight:600;padding:11px 14px;border-bottom:1px solid var(--rule);
  white-space:nowrap;background:var(--surface-2)}
td{padding:11px 14px;border-bottom:1px solid var(--rule);vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
th.num,td.num{text-align:right}
.repo-cell{font-family:var(--mono);font-size:.82rem}
td.has-viol{color:var(--high);font-weight:600}
.footnote{margin:0;font-size:.78rem;color:var(--muted);max-width:68ch}

.pill{display:inline-block;padding:2px 9px;border-radius:2px;font-size:.68rem;
  font-weight:600;letter-spacing:.06em;text-transform:uppercase;white-space:nowrap}
.pill.sev-high{background:var(--high-bg);color:var(--high)}
.pill.sev-medium{background:var(--medium-bg);color:var(--medium)}
.pill.sev-low{background:var(--low-bg);color:var(--low)}
.pill.sev-none{background:var(--good-bg);color:var(--good)}

.rate{display:flex;align-items:center;gap:9px;min-width:150px}
.rate-track{flex:1;height:5px;background:var(--surface-2);border-radius:3px;overflow:hidden}
.rate-fill{height:100%;border-radius:3px}
.rate-fill.has-high{background:var(--high)}
.rate-fill.no-high{background:var(--good)}
.rate-num{font-size:.8rem;color:var(--ink-2);min-width:48px;text-align:right}

.detail{display:flex;flex-direction:column;gap:10px}
.repo{border:1px solid var(--rule);border-radius:3px;background:var(--surface);overflow:hidden}
.repo-head{cursor:pointer;padding:14px 16px;display:flex;align-items:center;gap:8px;
  flex-wrap:wrap;list-style:none;background:var(--surface)}
.repo-head::-webkit-details-marker{display:none}
.repo-head:hover{background:var(--surface-2)}
.repo[open] .repo-head{border-bottom:1px solid var(--rule)}
.repo-name{font-family:var(--mono);font-size:.85rem;font-weight:600;flex:1;min-width:210px}
.repo-counts{font-size:.78rem;color:var(--muted);font-variant-numeric:tabular-nums}
.repo-body{padding:18px 16px 22px;display:flex;flex-direction:column;gap:20px}
.gate-reason{margin:0;font-size:.83rem;color:var(--high);
  background:var(--high-bg);padding:9px 12px;border-radius:3px}
.clean{margin:0;color:var(--good);font-size:.9rem}

.sev-group{display:flex;flex-direction:column;gap:10px}
.sev-head{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em}
.sev-head.sev-high{color:var(--high)}
.sev-head.sev-medium{color:var(--medium)}
.sev-head.sev-low{color:var(--low)}

.finding{border:1px solid var(--rule);border-left:3px solid var(--low);
  border-radius:3px;padding:13px 15px;display:flex;flex-direction:column;gap:9px;
  background:var(--surface)}
.finding.sev-high{border-left-color:var(--high)}
.finding.sev-medium{border-left-color:var(--medium)}
.finding-head{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
.chip{font-size:.6rem;font-weight:700;letter-spacing:.09em;padding:2px 6px;border-radius:2px}
.sev-high .sev-chip{background:var(--high-bg);color:var(--high)}
.sev-medium .sev-chip{background:var(--medium-bg);color:var(--medium)}
.sev-low .sev-chip{background:var(--low-bg);color:var(--low)}
.policy{font-family:var(--mono);font-size:.8rem;font-weight:600}
.policy-title{font-size:.82rem;color:var(--ink-2)}
.loc{font-family:var(--mono);font-size:.74rem;color:var(--muted);margin-left:auto}
.verdict{margin:0;font-size:.88rem;color:var(--ink-2);max-width:74ch}

.evidence,.fix{display:flex;flex-direction:column;gap:5px}
.evidence-label,.fix-label{font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;
  color:var(--muted);font-weight:600}
.fix-computed .fix-label{color:var(--good)}
.fix-desc{margin:0;font-size:.82rem;color:var(--ink-2);max-width:74ch}
pre{margin:0;background:var(--code-bg);border:1px solid var(--rule);border-radius:3px;
  padding:10px 12px;overflow-x:auto}
code{font-family:var(--mono);font-size:.78rem;line-height:1.5;white-space:pre-wrap;
  word-break:break-word}
.evidence pre{border-left:2px solid var(--accent)}
.agreement{margin:0;font-size:.74rem;color:var(--medium);font-family:var(--mono)}

.unsure-block{display:flex;flex-direction:column;gap:10px;padding-top:16px;
  border-top:1px dashed var(--rule)}
.unsure-head{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--medium)}
.unsure-intro{margin:0;font-size:.8rem;color:var(--muted);max-width:74ch}
.errors{font-size:.8rem;color:var(--high)}
.errors ul{margin:6px 0 0;padding-left:18px}

summary:focus-visible,a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
@media (max-width:640px){
  .wrap{padding:24px 14px 64px}
  .loc{margin-left:0;width:100%}
  .rate{min-width:120px}
}
"""

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{styles}</style>
</head>
<body>{body}</body>
</html>
"""
