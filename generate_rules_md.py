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
    aw = policy.get("applies_when", "").strip().lower()
    return aw.startswith("every repo")


def format_block(policy: dict) -> str:
    pid       = policy["policy_id"]
    title     = policy["title"]
    severity  = policy["severity"]
    desc      = policy["description"].strip()
    hint      = policy["evaluation_hint"].strip()
    aw        = policy["applies_when"].strip()

    return "\n".join([
        f"### {pid} · {title}  [{severity}]",
        "",
        desc,
        "",
        f"**Applies when:** {aw}",
        "",
        "**How to evaluate:**",
        "",
        hint,
    ])


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
