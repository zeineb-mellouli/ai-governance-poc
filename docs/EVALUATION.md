# Evaluation

The eval harness is the measurement instrument for every claim about accuracy.
It costs **no API calls** - it scores reports that already exist, so labels and
scoring logic can be iterated for free after a single audit run.

```bash
./venv/bin/python main.py eval --reports reports
./venv/bin/python main.py eval --reports reports --baseline reports_previous   # adds Δ F1
```

## Ground truth

Hand-authored, one YAML file per repository in `evaluation/expected/`, named to
match the repo directory. A repo with no label file is silently excluded from
scoring; `eval` prints which ones those are.

```yaml
repo: FinalProject

expect_violations:            # must fire; not firing is a FALSE NEGATIVE
  - policy: REPO-9
    file: null                # null = repository-level finding
    note: "'FinalProject' does not match {dept}-{resource}-{project}"

expect_clean:                 # must not fire; firing is a FALSE POSITIVE
  - policy: DM-7
    file: null
    note: no gold output and no Dim/Fact table -- nothing for DM-7 to govern

tolerate:                     # either verdict defensible; EXCLUDED from scoring
  - policy: PII-4
    file: sql/create_tables.sql
    note: DDL declares name/email/phone columns but holds no values
```

## How findings are counted

`NON_COMPLIANT` and `NEEDS_REVIEW` both count as **fired**. An undecided verdict
did surface the issue, so it counts for recall, but it is tracked separately in
the `Review` column: a finding routed to a human is a weaker outcome than a
confident finding with a working fix attached.

A finding that fires but appears in **no** bucket is reported as `UNLABELLED`,
not as a false positive. It may be a real violation the labels missed, scoring
it as an error would train the policy set to find less.

`tolerate` entries are excluded from scoring entirely.

## Reading the numbers

`sample_repos/compliant/ops-code-market_rate` is the control: compliant by
construction, so anything flagged there is a false positive.

Two cautions:

1. **Per-policy F1 on 1–2 labelled cases is not meaningful.** Only NAM-5 (30
   instances) and DQ-1 (5) have enough instances to support a conclusion.
2. **Reports are only comparable at the same `k`.** `audit_samples` is recorded
   on every report; at k=1 every confidence is 1.0 by construction.


## The corpus

`sample_repos/` holds 10 repositories across categories chosen to exercise
different failure modes - `compliant/` (precision control), `non_compliant/`,
`adversarial/`, `ambiguous/`, `edge_cases/`, `holistic/` (violations only visible
across files), `not_applicable/`, `realistic/`, and `sdd_generated/`.


