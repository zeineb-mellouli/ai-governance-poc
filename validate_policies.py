import yaml

with open("policies/policies.yaml") as f:
    data = yaml.safe_load(f)

policies = data["policies"]
print(f"{len(policies)} policies loaded\n")
for p in policies:
    missing = [k for k in ("policy_id","title","description","evaluation_hint","severity","applies_when") if k not in p]
    status = "MISSING: " + ", ".join(missing) if missing else "OK"
    print(f"  {p['policy_id']:<8} {p['severity']:<6}  {p['title']}  [{status}]")
