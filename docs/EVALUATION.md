# Evaluation

The eval harness is the measurement instrument for every claim about accuracy.
It costs **no API calls** — it scores reports that already exist, so labels and
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

Labels key on `(policy_id, file_path)`. Two entries may share a key when one file
carries two concerns under one policy — the notes are joined rather than
overwritten.

## How findings are counted

`NON_COMPLIANT` and `NEEDS_REVIEW` both count as **fired**. An undecided verdict
did surface the issue, so it counts for recall, but it is tracked separately in
the `Review` column: a finding routed to a human is a weaker outcome than a
confident finding with a working fix attached.

A finding that fires but appears in **no** bucket is reported as `UNLABELLED`,
not as a false positive. It may be a real violation the labels missed — scoring
it as an error would train the policy set to find less. Triage these into a
bucket rather than leaving them to accumulate.

`tolerate` entries are excluded from scoring entirely. The count is printed
because **each one marks a policy that is underspecified** — a rising tolerated
count is a signal, not a clean bill of health.

## Reading the numbers

`sample_repos/compliant/ops-code-market_rate` is the control: compliant by
construction, so anything flagged there is a false positive. It is the single
most important precision signal in the corpus.

Three cautions:

1. **Per-policy F1 on 1–2 labelled cases is an anecdote.** Only NAM-5 (30
   instances) and DQ-1 (5) have enough instances to support a conclusion.
2. **Reports are only comparable at the same `k`.** `audit_samples` is recorded
   on every report; at k=1 every confidence is 1.0 by construction.
3. **k=3 damps run-to-run variance but does not remove it.** SQL-11 has flipped
   between runs on identical policy text. A single-point F1 move on a
   low-instance policy is noise until it reproduces.

## The corpus

`sample_repos/` holds 10 repositories across categories chosen to exercise
different failure modes — `compliant/` (precision control), `non_compliant/`,
`adversarial/`, `ambiguous/`, `edge_cases/`, `holistic/` (violations only visible
across files), `not_applicable/`, `realistic/`, and `sdd_generated/`.

Fixtures are deliberately annotated with which policy each violation maps to. Use
them rather than synthetic repos — the labels only mean something against known
content.

## Workflow for a policy change

1. Run `main.py eval` and keep the current reports directory as a baseline.
2. Change **one** thing in `policies/policies.yaml` — see the tuning discipline
   in [POLICIES.md](POLICIES.md).
3. `scripts/validate_policies.py`, then `scripts/setup_chromadb.py` (the vector store is not
   rebuilt automatically).
4. Re-run the batch audit into a **new** directory.
5. `main.py eval --reports new --baseline old` and read Δ F1 across **every**
   policy, not just the one you changed.

Step 5 is the one that catches the regression. Both documented rule-sharpening
failures improved nothing and damaged an adjacent policy.
