"""Compile policies/policies.yaml into rules.md.

rules.md is the build-time constitution -- the document a coding assistant reads
before generating pipeline code, as opposed to the runtime audit that judges what
was written. Run from the repository root; rules.md is overwritten every time.

    python scripts/generate_rules_md.py
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
    pid = policy["policy_id"]
    title = policy["title"]
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

    def by_severity(p: dict) -> int:
        return SEVERITY_ORDER.get(p["severity"], 99)

    universal = sorted([p for p in policies if is_universal(p)], key=by_severity)
    conditional = sorted([p for p in policies if not is_universal(p)], key=by_severity)

    sections = [
        "# Governance Constitution — Data Pipeline Rules",
        "",
        "> Auto-generated from `policies/policies.yaml`.",
        "> **Do not edit manually** — run `python scripts/generate_rules_md.py` to regenerate.",
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
        "## Part 2 — Conditional rules (check `applies_to` before evaluating)",
        "",
    ]

    for p in conditional:
        sections.append(format_block(p))
        sections.append("")
        sections.append("---")
        sections.append("")

    Path(OUTPUT_PATH).write_text("\n".join(sections), encoding="utf-8")
    print(f"{OUTPUT_PATH} written — {len(universal)} universal + "
          f"{len(conditional)} conditional = {len(policies)} policies")


if __name__ == "__main__":
    main()
