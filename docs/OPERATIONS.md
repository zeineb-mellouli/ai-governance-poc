# Operations

## Setup

```bash
python -m venv venv && ./venv/bin/pip install -r requirements.txt
cp .env.example .env          # fill in the Azure OpenAI values
./venv/bin/python scripts/setup_chromadb.py
```

**Run every command from the repository root.** `policies/policies.yaml`,
`chroma_db/` and the sample repo paths are all resolved relative to the working
directory.

### Environment

| Variable | Required | Purpose |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | yes | `https://<resource>.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | yes | — |
| `AZURE_OPENAI_DEPLOYMENT` | yes | The **deployment** name, not the model name |
| `AZURE_OPENAI_API_VERSION` | no | Defaults to `2024-10-21` |
| `AGA_AUDIT_SAMPLES` | no | Default k. `--samples/-k` overrides it |

The client is Azure-only (`agents/llm_client.py`). Plain `OPENAI_API_KEY` is not
read; pointing this at non-Azure OpenAI means editing `get_client`.

The deployed model must support **JSON mode** and the **`seed`** parameter.
Without `seed`, runs stop being reproducible and `system_fingerprint` becomes the
only drift signal.

## Commands

| Command | What it does | API calls |
|---|---|---|
| `main.py audit --repo PATH` | Audit one repo and write its report | yes |
| `main.py batch --root DIR` | Audit every repo under `DIR/<category>/<repo>/` | yes |
| `main.py html --reports DIR` | Re-render the static dashboard | **no** |
| `main.py dashboard --reports DIR` | Open the Streamlit dashboard | only if you audit from it |
| `main.py eval --reports DIR` | Score reports against ground truth | **no** |

Everything downstream of an audit reads `machine_report.json`, so report layout,
the dashboard and the eval harness can all be iterated on for free after a single
run.

The dashboard is the one exception: viewing costs nothing, but its sidebar has an
**Audit a repository** panel that runs a real audit at up to k=5. That is why it
loads `.env` — it needs the Azure credentials, not just the report files.

Useful flags:

```bash
--samples/-k N            # self-consistency samples; cost is linear in N
--category compliant      # batch: restrict to one category subfolder
--open                    # audit: launch the dashboard afterwards
--baseline DIR            # eval: compare against a second reports directory
```

Exit codes are `0` throughout, except `batch`, which returns `1` if a repository
crashed during the run.

## Output

```
reports/
├── index.html                    # batch dashboard, self-contained
└── <repo-name>/
    ├── machine_report.json       # the source of truth for every other view
    └── draft_report.md           # human-readable
```

## Running in CI

The pipeline reports; it does not decide. `audit` exits `0` whether or not it
found violations, so a CI step runs it for the report and publishes that report
as an artifact. `batch` exits `1` only if a repository crashed outright — that is
a broken run, not a compliance verdict.

If you need a build to block on findings, read `machine_report.json` in a
following step and decide there. The counts you would branch on are
`summary.non_compliant_by_severity` and `compliance_score.weighted_pass_rate`.

### Azure Pipelines

```yaml
- script: |
    python -m pip install -r requirements.txt
    python scripts/setup_chromadb.py
    python main.py audit --repo "$(Build.SourcesDirectory)" \
      --out "$(Build.ArtifactStagingDirectory)/audit"
  displayName: Governance audit
  env:
    AZURE_OPENAI_ENDPOINT:   $(AZURE_OPENAI_ENDPOINT)
    AZURE_OPENAI_API_KEY:    $(AZURE_OPENAI_API_KEY)
    AZURE_OPENAI_DEPLOYMENT: $(AZURE_OPENAI_DEPLOYMENT)

- task: PublishBuildArtifacts@1
  condition: always()          # publish the report even if the audit failed
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
    python scripts/setup_chromadb.py
    python main.py audit --repo . --out audit

- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: governance-audit
    path: audit/
```

`condition: always()` / `if: always()` matters: without it the report is not
published on the run where you most need to read it.

## Cost model

```
audit calls = (files with ≥1 candidate policy + 1 holistic pass) × k
remediation calls = NON_COMPLIANT findings with no deterministic fix   (k does not apply)
```

Deterministic checks (REPO-9, NAM-5 naming, REPRO-13) cost nothing. A file no
policy's globs cover costs nothing.

Measured on the bundled `sample_repos/` corpus (10 repositories, 128 files):

| k | Audit calls |
|---|---|
| 1 | 138 |
| 3 (default) | 414 |

Per repository that is roughly 7–27 calls at k=1. Remediation adds one call per
model-decided violation on top.

**Cost control levers,** in the order worth reaching for:

1. `-k 1` — cuts audit calls by two thirds. You lose measured confidence.
2. Tighten `applies_to` globs so fewer files are candidates.
3. Extend `SKIP_DIRS` for repository shapes that carry a lot of vendored code.

## Failure modes

**Reports of different sizes across two runs of the same repo.** An API call
failed. Read `report.errors`; do not go looking at prompts. Finding count is a
pure function of the file list.

**`system_fingerprint` changed between runs.** The serving backend moved. Output
differences are expected — this is the signal that distinguishes "our pipeline is
non-deterministic" from "the model underneath us changed".

**Everything is `NEEDS_REVIEW`.** Usually evidence grounding: the model is
producing quotes that do not appear in the file. Check whether content is being
truncated at `MAX_CONTENT_CHARS`, or whether `ENFORCE_EVIDENCE_GROUNDING` is
rejecting legitimately re-wrapped quotes.

**Confidence is 1.0 everywhere.** You ran at `k=1`. Check `audit_samples` on the
report.

**A report looks clean on an obviously broken repo.** Check `errors`. A run that
failed on most of its files produces few findings and a flattering pass rate.

**ChromaDB errors, or policy edits having no effect.** The vector store is stale.
Re-run `scripts/setup_chromadb.py`; it is not automatic.

## Changing policies

`policies/policies.yaml` is the source of truth. After editing — see
[POLICIES.md](POLICIES.md) for the rules of engagement:

```bash
./venv/bin/python scripts/validate_policies.py     # schema check, non-zero on problems
./venv/bin/python scripts/setup_chromadb.py        # REBUILD the vector store — not optional
./venv/bin/python scripts/generate_rules_md.py     # regenerate rules.md
```

## Verifying a change

There is no automated test suite. To check that a change to `agents/` did not
break anything, run an audit and compare against a known-good report:

```bash
./venv/bin/python main.py batch --root sample_repos --out reports_new -k 1
./venv/bin/python main.py eval --reports reports_new --baseline reports
```

`-k 1` keeps it to 138 calls instead of 414, and the `eval` Δ F1 column shows any
policy whose accuracy moved. Two things to check by hand afterwards, because
nothing checks them for you:

- **Finding counts per repository should be unchanged.** They are a function of
  the file list, not of model output, so a change in `total_findings` means
  either an API call failed (check `errors`) or the fixed-grid rules were broken.
- **The verdict split should be stable.** Compare `by_status` between runs; large
  movement without a policy change points at the auditor, not the model.

See [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) §9 for what this does and
does not cover.
