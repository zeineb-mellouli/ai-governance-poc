# Policies

`policies/policies.yaml` is the single source of truth. `rules.md` and the
ChromaDB collection are both generated from it — never edit either by hand.

## The library

14 policies. 

| ID | Severity | Scope | Evaluation | Covers |
|---|---|---|---|---|
| DQ-1 | HIGH | file | model | Data quality validation present |
| OPS-2 | MEDIUM | file | model | Logging and monitoring |
| SEC-3 | HIGH | file | model | No hardcoded secrets |
| PII-4 | HIGH | file | model | No raw PII in outputs |
| NAM-5 | LOW | file | hybrid | File/folder naming convention |
| REPRO-6 | MEDIUM | file | model | Random seeds fixed |
| DM-7 | MEDIUM | repository | model | Output table grain documented |
| GIT-8 | MEDIUM | file | model | Git branching and commit standards |
| REPO-9 | MEDIUM | repository | deterministic | Repository naming convention |
| SQL-10 | MEDIUM | file | model | SQL table/object naming |
| SQL-11 | LOW | file | model | SQL column naming |
| ARCH-12 | HIGH | file | model | Medallion architecture |
| REPRO-13 | LOW | repository | deterministic | Dependency versions pinned |
| REPRO-14 | MEDIUM | file | model | Raw source data not modified in place |

## Schema

```yaml
- policy_id: DQ-1                    # stable identifier; renaming breaks ground truth
  title: Data quality validation present
  severity: HIGH                     # HIGH | MEDIUM | LOW  -> scoring weight 3 | 2 | 1
  scope: file                        # file | repository
  evaluation: model                  # model | deterministic | hybrid
  description: >                     # context for the reader and for embedding
    Before data is written downstream ...
  applies_to:                        # globs; file-scoped model policies need at least one
    - '**/*.py'
    - '**/*.ipynb'
  excludes:                          # globs; wins over applies_to
    - 'test_*.py'
    - 'conftest.py'
  rule: >                            # THE authority. What the model is told to apply.
    Data that is loaded and then used further must pass a quality check ...
  examples:
    compliant:
      - "schema.validate(df)  # pandera"
    non_compliant:
      - "df = pd.read_csv(...); df.to_sql(...)"
```

### Field semantics

**`scope`** — `file` policies are judged per file. `repository` policies are
judged only by the whole-repo pass and are marked `[WHOLE-REPOSITORY ONLY]` in
that prompt.

**`evaluation`** —

- `deterministic`: decided in Python, no model call, confidence 1.0. Adding one
  means writing the check in `auditor_agent.py`; the YAML entry alone does
  nothing.
- `model`: sent to the LLM.
- `hybrid`: partly both. NAM-5's naming grammar is deterministic; its column-name
  rule is a per-file model question, which is why its `applies_to` is only
  `**/*.csv` and `**/*.parquet`.

**`applies_to` / `excludes`** — applicability is decided **in code**, before the
model is called. A policy whose globs do not match is never offered, so the model
cannot volunteer a verdict on it. Matching is case-insensitive and tested against
both the full repo-relative path and the bare filename; a leading `**/` is
tolerated.

**`rule`** — the only text the model is told is authoritative. It is also what
the Remediation Agent is shown so its fix satisfies the rule it is repairing.

**`examples`** — appended to the prompt as `compliant example:` /
`non_compliant example:` lines. This is the safest place to steer behaviour,
because an example does not change how the rule generalises. Prefer adding an
example to sharpening rule text.

## Changing a policy

```bash
./venv/bin/python scripts/validate_policies.py     # schema check, non-zero on problems
./venv/bin/python scripts/setup_chromadb.py        # REBUILD the vector store — not optional
./venv/bin/python scripts/generate_rules_md.py     # regenerate rules.md
```

`scripts/validate_policies.py` catches the mistakes the schema makes possible: a missing
`rule`, an invalid `scope`/`evaluation`/`severity`, a duplicate `policy_id`, and
a file-scoped model policy with an empty `applies_to`.

If you add, remove, or rename a `policy_id`, update `evaluation/expected/*.yaml`
too. Ground truth keys on `(policy_id, file)`, so a rename shows up as a false
negative plus an unlabelled finding.

