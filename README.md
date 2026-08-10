# ai-governance-poc

An agentic governance pipeline: it reads a repository, checks it against a
policy library, grades it, and proposes or applies fixes.

```
Repository Agent  ->  Auditor Agent  ->  Remediation Agent  ->  Report + Gate
   (file I/O)         (rules + LLM)      (fix generation)      (JSON / MD / exit code)
```

Checks that are decidable by pattern (repository naming, file naming, dependency
pinning) run in code at confidence 1.0 and never reach a model. Everything that
needs reading and interpreting code is delegated to the LLM, grounded in the
policy text retrieved from ChromaDB.

## Quick start

```bash
python -m venv venv && ./venv/bin/pip install -r requirements.txt
cp .env.example .env          # then fill in the Azure OpenAI values
./venv/bin/python setup_chromadb.py

./venv/bin/python main.py audit --repo sample_repos/compliant/ops-code-market_rate
./venv/bin/python main.py batch --root sample_repos --out reports
```

## The CI gate

By default the audit only reports. Add a threshold and it returns a non-zero
exit code, which is what turns it from a script into a merge control.

| Flag | Blocks when |
|---|---|
| `--fail-on {LOW,MEDIUM,HIGH}` | any NON_COMPLIANT finding at that severity **or above** |
| `--fail-on-grade {PASS,NEEDS_WORK,FAIL}` | the repository's grade is that **or worse** |
| `--fail-on-error` | the audit had partial failures |

All three are off unless set, and they combine — every threshold that trips is
reported. Exit code is `0` when the gate passes and `1` when it does not.

`--fail-on-error` deserves a word. The other two thresholds are only meaningful
if the audit actually ran: a run that errors on most of its files produces few
findings, a flattering pass rate, and a green build. A gate that passes because
the audit crashed is worse than no gate. In `batch`, a repository that crashes
outright always fails the gate regardless of thresholds — there is no verdict to
pass.

```bash
# no secrets may merge
./venv/bin/python main.py audit --repo . --fail-on HIGH

# stricter: the repo must clear the bar overall, and the audit must complete
./venv/bin/python main.py batch --root repos --fail-on HIGH --fail-on-grade FAIL --fail-on-error
```

Output on failure names what tripped it, worst first, so a truncated CI log is
still actionable:

```
Gate: FAIL   --fail-on HIGH
  HIGH 1  ·  MEDIUM 1  ·  LOW 9  ·  grade FAIL  ·  undecided 1  ·  errors 0

  ✗ 1 NON_COMPLIANT finding(s) at severity HIGH or above
      SEC-3     [HIGH]  final_v2_ACTUAL.py  hardcoded api_key and connection_string
```

### Azure Pipelines

```yaml
- script: |
    python -m pip install -r requirements.txt
    python setup_chromadb.py
    python main.py audit --repo "$(Build.SourcesDirectory)" --out "$(Build.ArtifactStagingDirectory)/audit" \
      --fail-on HIGH --fail-on-error
  displayName: Governance audit
  env:
    AZURE_OPENAI_ENDPOINT:   $(AZURE_OPENAI_ENDPOINT)
    AZURE_OPENAI_API_KEY:    $(AZURE_OPENAI_API_KEY)
    AZURE_OPENAI_DEPLOYMENT: $(AZURE_OPENAI_DEPLOYMENT)

- task: PublishBuildArtifacts@1
  condition: always()          # publish the report even when the gate fails
  inputs:
    pathToPublish: $(Build.ArtifactStagingDirectory)/audit
    artifactName: governance-audit
```

### GitHub Actions

```yaml
- name: Governance audit
  env:
    AZURE_OPENAI_ENDPOINT:   ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_API_KEY:    ${{ secrets.AZURE_OPENAI_API_KEY }}
    AZURE_OPENAI_DEPLOYMENT: ${{ secrets.AZURE_OPENAI_DEPLOYMENT }}
  run: |
    python -m pip install -r requirements.txt
    python setup_chromadb.py
    python main.py audit --repo . --out audit --fail-on HIGH --fail-on-error

- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: governance-audit
    path: audit/
```

`condition: always()` / `if: always()` matters: without it the report is not
published on the run where you most need to read it.

## Grading

Each repository gets a severity-weighted pass rate over its *applicable* checks
(NOT_APPLICABLE is excluded — a check correctly skipped is not a check passed;
NEEDS_REVIEW is excluded from both sides and reported separately), plus a
severity gate so one HIGH finding cannot drown in hundreds of passing checks.

| | |
|---|---|
| any HIGH violation | capped at `FAIL` |
| 3+ MEDIUM violations | capped at `NEEDS_WORK` |
| otherwise | `PASS` ≥ 98%, `NEEDS_WORK` ≥ 90%, else `FAIL` |

Thresholds live in `agents/schemas.py` (`PASS_RATE_THRESHOLD`,
`NEEDS_WORK_RATE_THRESHOLD`, `MEDIUM_FAILURES_BEFORE_CAP`).

## Confidence

Confidence is measured, not self-reported. Each prompt is sampled `k` times
(`--samples/-k`, default 3) and the verdict is the majority; the confidence is
the fraction of samples that agreed. A split vote becomes NEEDS_REVIEW.

`-k 1` is cheapest but measures no disagreement, so every confidence is 1.0 and
the remediation confidence gate never fires. The value used is recorded on each
report as `audit_samples` — two reports are only comparable if it matches.

## Changing policies

`policies/policies.yaml` is the source of truth. After editing it:

```bash
./venv/bin/python validate_policies.py     # schema check, non-zero on problems
./venv/bin/python setup_chromadb.py        # REBUILD the vector store — not optional
./venv/bin/python generate_rules_md.py     # regenerate rules.md
./venv/bin/python -m pytest tests/ -q      # several tests read policies.yaml directly
```

If you add, remove, or rename a `policy_id`, also update the ground truth in
`evaluation/expected/*.yaml` — it keys on `(policy_id, file)`, so a rename shows
up as a false negative plus an unlabelled finding.

## Evaluation

`evaluation/expected/*.yaml` holds hand-authored ground truth.
`evaluation/score.py` reports precision/recall per policy against it and costs
no API calls — it scores reports that already exist, so labels and scoring logic
can be iterated for free after a single run.

`sample_repos/compliant/ops-code-market_rate` is the control: compliant by
construction, so anything flagged there is a false positive. It is the single
most important precision signal in the corpus.
