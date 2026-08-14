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
| `AZURE_OPENAI_API_VERSION` | no | The version's date |
| `AGA_AUDIT_SAMPLES` | no | Default k. `--samples/-k` overrides it |

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


## Output

```
reports/
├── index.html                    # batch dashboard, self-contained
└── <repo-name>/
    ├── machine_report.json       # the source of truth for every other view
    └── draft_report.md           # human-readable
```

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


## Changing policies

`policies/policies.yaml` is the source of truth. After editing — see
[POLICIES.md](POLICIES.md) for the rules of engagement:

```bash
./venv/bin/python scripts/validate_policies.py     # schema check, non-zero on problems
./venv/bin/python scripts/setup_chromadb.py        # REBUILD the vector store — not optional
./venv/bin/python scripts/generate_rules_md.py     # regenerate rules.md
```

