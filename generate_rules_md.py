"""
generate_rules_md.py
Compiles all governance policies from policies.yaml into rules.md --
the build-time constitution that Copilot reads before generating any code.

Usage:  python generate_rules_md.py
Output: rules.md at the project root (overwritten on every run)
"""

from pathlib import Path
import yaml

POLICIES_PATH = "policies/policies.yaml"
OUTPUT_PATH = "rules.md"

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def is_universal(policy: dict) -> bool:
    """Return True when the policy applies unconditionally to every repo."""
    if policy.get("scope") == "repository":
        return True
    return "**/*" in (policy.get("applies_to") or [])


def format_block(policy: dict) -> str:
    pid      = policy["policy_id"]
    title    = policy["title"]
    severity = policy["severity"]

    applies = policy.get("applies_to") or []
    applies_text = ", ".join(f"`{g}`" for g in applies) if applies else "the repository as a whole"
    excludes = policy.get("excludes") or []

    block = [
        f"### {pid} · {title}  [{severity}]",
        "",
        policy["description"].strip(),
        "",
        f"**Applies to:** {applies_text}",
    ]
    if excludes:
        block.append(f"**Except:** {', '.join(f'`{g}`' for g in excludes)}")
    block += [
        f"**Decided by:** {policy.get('evaluation', 'model')}",
        "",
        "**Rule:**",
        "",
        policy["rule"].strip(),
    ]

    examples = policy.get("examples") or {}
    for label, heading in (("compliant", "Compliant"), ("non_compliant", "Non-compliant")):
        entries = examples.get(label) or []
        if entries:
            block += ["", f"**{heading} examples:**", ""]
            block += [f"- `{e}`" for e in entries]

    return "\n".join(block)


def main() -> None:
    policies = yaml.safe_load(Path(POLICIES_PATH).read_text(encoding="utf-8"))["policies"]

    universal   = sorted(
        [p for p in policies if     is_universal(p)],
        key=lambda p: SEVERITY_ORDER.get(p["severity"], 99),
    )
    conditional = sorted(
        [p for p in policies if not is_universal(p)],
        key=lambda p: SEVERITY_ORDER.get(p["severity"], 99),
    )

    sections = [
        "# Governance Constitution — Data Pipeline Rules",
        "",
        "> Auto-generated from `policies/policies.yaml`.",
        "> **Do not edit manually** — run `python generate_rules_md.py` to regenerate.",
        "",
        "---",
        "",
        "## Part 1 — Hard rules (apply unconditionally to every file in every repo)",
        "",
    ]

    for p in universal:
        sections.append(format_block(p))
        sections.append("")
        sections.append("---")
        sections.append("")

    sections += [
        "## Part 2 — Conditional rules (check `applies_when` before evaluating)",
        "",
    ]

    for p in conditional:
        sections.append(format_block(p))
        sections.append("")
        sections.append("---")
        sections.append("")

    output = "\n".join(sections)
    Path(OUTPUT_PATH).write_text(output, encoding="utf-8")

    print(f"rules.md written — {len(universal)} universal + {len(conditional)} conditional = {len(policies)} total")
    print(f"Output path: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
