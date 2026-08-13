"""Structural check on policies/policies.yaml -- run before rebuilding ChromaDB.

Catches the mistakes the schema makes possible: a policy with no rule, a
file-scoped policy with no applies_to (which would silently never be evaluated),
or a scope/evaluation value the auditor does not understand.
"""

import sys

import yaml

REQUIRED = ("policy_id", "title", "description", "rule", "severity", "scope", "evaluation")
VALID_SCOPES = {"file", "repository"}
VALID_EVALUATIONS = {"model", "deterministic", "hybrid"}
VALID_SEVERITIES = {"HIGH", "MEDIUM", "LOW"}

with open("policies/policies.yaml") as f:
    policies = yaml.safe_load(f)["policies"]

print(f"{len(policies)} policies loaded\n")

problems = 0
for p in policies:
    issues = [f"missing {k}" for k in REQUIRED if k not in p]

    if p.get("severity") not in VALID_SEVERITIES:
        issues.append(f"bad severity {p.get('severity')!r}")
    if p.get("scope") not in VALID_SCOPES:
        issues.append(f"bad scope {p.get('scope')!r}")
    if p.get("evaluation") not in VALID_EVALUATIONS:
        issues.append(f"bad evaluation {p.get('evaluation')!r}")

    # A file-scoped policy the model judges but that matches no path would be
    # silently dead -- never offered, never reported, never missed.
    if (
        p.get("scope") == "file"
        and p.get("evaluation") in {"model", "hybrid"}
        and not p.get("applies_to")
    ):
        issues.append("file-scoped model policy with an empty applies_to (would never fire)")

    problems += bool(issues)
    status = "; ".join(issues) if issues else "OK"
    print(f"  {p.get('policy_id', '?'):<10} {p.get('severity', '?'):<6} "
          f"{p.get('scope', '?'):<10} {p.get('evaluation', '?'):<13} "
          f"{p.get('title', '?')}  [{status}]")

ids = [p.get("policy_id") for p in policies]
duplicates = {i for i in ids if ids.count(i) > 1}
if duplicates:
    problems += 1
    print(f"\nDuplicate policy_id(s): {', '.join(sorted(duplicates))}")

print(f"\n{problems} policy/policies with problems")
sys.exit(1 if problems else 0)
