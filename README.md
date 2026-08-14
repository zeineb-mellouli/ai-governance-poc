# ai-governance-poc

An agentic governance pipeline: it reads a repository, checks it against a policy
library, scores it, and proposes fixes.

```
Repository Agent  ->  Auditor Agent  ->  Remediation Agent  ->  Report
   (file I/O)         (rules + LLM)      (fix generation)      (JSON / MD / HTML)
```

Checks decidable by pattern (repository naming, file naming, dependency pinning)
run in code at confidence 1.0 and never reach a model. Everything that needs
reading and interpreting code is delegated to the LLM, grounded in policy text
retrieved from ChromaDB.

## Quick start

```bash
python -m venv venv && ./venv/bin/pip install -r requirements.txt
cp .env.example .env          # then fill in the Azure OpenAI values
./venv/bin/python scripts/setup_chromadb.py

./venv/bin/python main.py audit --repo sample_repos/compliant/ops-code-market_rate
./venv/bin/python main.py batch --root sample_repos --out reports
```

Run every command from the repository root.

## Commands

| Command | What it does | API calls |
|---|---|---|
| `main.py audit --repo PATH` | Audit one repository and write its report | yes |
| `main.py batch --root DIR` | Audit every repo under `DIR/<category>/<repo>/` | yes |
| `main.py html --reports DIR` | Re-render the static dashboard | no |
| `main.py dashboard --reports DIR` | Open the Streamlit dashboard | only if you audit from it |
| `main.py eval --reports DIR` | Score reports against ground truth | no |

The pipeline reports rather than deciding: an audit exits `0` whether or not it
found violations. To block a build on findings, read `machine_report.json` in a
following CI step — see [docs/OPERATIONS.md](docs/OPERATIONS.md).

## Documentation

| Document | Read it when |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | You need to know how a verdict is produced and why the design is shaped this way |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | You are running it, wiring it into CI, or debugging a run |
| [docs/POLICIES.md](docs/POLICIES.md) | You are adding or changing a policy — **read the tuning discipline first** |
| [docs/EVALUATION.md](docs/EVALUATION.md) | You are measuring accuracy or changed a rule and need to prove it helped |
| [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md) | You are the one shipping this. Start here |

## Layout

```
main.py          CLI entrypoint — audit, batch, html, dashboard, eval
dashboard.py     Streamlit dashboard (main.py launches it)

agents/          the pipeline: repository -> auditor -> remediation, plus the HTML report
policies/        policies.yaml — the single source of truth for every rule
scripts/         one-off build steps: setup_chromadb, validate_policies, generate_rules_md
evaluation/      scoring harness and hand-authored ground truth
sample_repos/    10 labelled fixture repositories across 9 categories
docs/            architecture, operations, policies, evaluation, production readiness

reports/         audit output, one folder per repository — reference only, run at k=1
rules.md         generated from policies.yaml — do not edit by hand
chroma_db/       the vector store, gitignored — rebuild it with scripts/setup_chromadb.py
```

The root holds only what you run directly. Everything under `scripts/` derives an
artifact from `policies/policies.yaml` and runs from the repository root.

Three files are **generated, never edited by hand**: `rules.md`, `chroma_db/`,
and `reports/`. All three come from `policies/policies.yaml` plus an audit run.

## Three things that will bite you

**The vector store is not rebuilt automatically.** Edit `policies/policies.yaml`
and you must re-run `scripts/setup_chromadb.py`, or the audit silently retrieves
against the old policy text — no error, just stale rules.

**Reports quote the secrets they find.** Evidence grounding requires verbatim
quotes, so a hardcoded credential caught by SEC-3 ends up in
`machine_report.json`. Treat report output as sensitive — see
[docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md).

**The dashboard can spend money.** Its sidebar has an *Audit a repository* panel
that runs a real audit at up to k=5. Viewing existing reports costs nothing; that
button does not.

## Handing this over

There is **no automated test suite** — verification is a real audit run against
`sample_repos/`. Before changing anything in `agents/`, read the reproducibility
contract in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); before changing a
policy, read the tuning discipline in [docs/POLICIES.md](docs/POLICIES.md). Both
describe rules that are easy to break by accident and produce no error when you
do. The known gaps are catalogued in
[docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md).

## Licence

See [LICENSE](LICENSE).
