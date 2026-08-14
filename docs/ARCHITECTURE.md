# Architecture

## What this is

An orchestrated workflow with two grounded LLM steps — not an autonomous
multi-agent system. Three of the four stages are deterministic Python; the model
is called only where a judgement requires reading and interpreting code.

```
Repository Agent ──> Auditor Agent ──> Remediation Agent ──> Report
  file I/O only      rules + LLM        fix generation       JSON / MD / HTML
```

Naming the stages "agents" describes their role in the pipeline, not autonomy.
Nothing here plans, chooses its own tools, or loops until satisfied.

## Stages

### Repository Agent — `agents/repository_agent.py`

Pure file I/O, no model calls. Walks a local path and returns a
`RepositorySnapshot`: the repo name, whether a root README exists, and one
`FileRecord` per recognised file.

Two exclusion mechanisms, and the difference matters:

- `SKIP_DIRS` — matched by **directory name** anywhere in the tree. Build output
  and vendored dependencies (`bin/`, `node_modules/`, `.venv/`, …).
- `SKIP_PATH_PREFIXES` — matched by **position** from the repo root. Spec-driven
  development scaffolding (`specs/`, `.github/agents/`, …).

The second exists because `agents/` and `prompts/` are ordinary source folder
names — this project keeps its own pipeline in `agents/`. Putting them in
`SKIP_DIRS` would silently exclude real code. `.github/` itself stays walkable so
`.github/workflows/` remains visible to GIT-8.

File content is capped at `MAX_CONTENT_CHARS` (6000). CSV files contribute only
their header plus a **value-shape profile** — labels like `email-like` or
`placeholder` sampled from the first five rows. Literal cell values are never
read into the snapshot, so they cannot reach a prompt or the report.

### Auditor Agent — `agents/auditor_agent.py`

Runs three passes over the snapshot.

**1. Deterministic checks.** No model call, confidence 1.0.

| Policy | Check |
|---|---|
| REPO-9 | repo root name against `^(aud\|fin\|gfp\|ops\|tax)-(code\|sql\|synapse)-[a-z][a-z0-9_]*$` |
| NAM-5 | file/folder naming grammar, one verdict per file, plus root README presence |
| REPRO-13 | dependency pinning, by parsing `requirements*.txt` / `environment.yml` / `pyproject.toml` / lockfiles |

These are regex- or parser-decidable. Leaving them to a model produced
inconsistent verdicts on byte-identical inputs, and REPRO-13 in particular was
the pipeline's largest false-positive source.

**2. Per-file LLM pass.** One call per file (× k samples).

Which policies a file is judged against is decided **in code** from the policy's
`applies_to` / `excludes` globs — not by asking the model whether a policy is
relevant. A policy that does not match is never offered, so the model cannot
volunteer a verdict on it. A file that no policy covers costs no call at all.

**3. Whole-repository (holistic) LLM pass.** One call (× k samples).

Scoped to what a per-file pass structurally cannot see: something required being
absent from the repository entirely, or an inconsistency visible only across two
or more files. Repository-scoped policies (DM-7) are marked
`[WHOLE-REPOSITORY ONLY]` and evaluated **only** here, because no other pass
covers them.

Results are merged by `_dedupe_holistic`, which neutralises duplicate verdicts to
`NOT_APPLICABLE` rather than deleting rows — see *Fixed grid* below.

### Remediation Agent — `agents/remediation_agent.py`

Attaches a fix to each `NON_COMPLIANT` finding, or records why there isn't one.
Fixes the Auditor already derived deterministically (renames, README scaffold)
are not re-sent to the model. Findings below `CONFIDENCE_THRESHOLD` (0.6) get no
fix at all — an uncertain verdict must not yield a runnable command.

Every generated fix passes a **safety net** (`_reject_fix`) that refuses commands
which would truncate or delete a data file, rename a branch instead of the
target, or are no-ops. A rejected fix leaves the violation standing, marked
`UNSAFE_FIX_REJECTED`.

### Orchestrator — `agents/orchestrator.py`

Sequences the three stages and renders reports. Each stage is wrapped so a
failure is recorded in `report.errors` rather than crashing the run. A failure in
the Repository Agent is fatal (nothing downstream can run without a snapshot); a
failure in one file, or in the holistic pass, is not.

## Retrieval

Policies live in ChromaDB (`chroma_db/`, built by `scripts/setup_chromadb.py`). The
corpus is small — 14 policies — so retrieval **ranks** every policy per file
rather than truncating to a top-k subset. Ranking fuses a semantic query and a
keyword scan via reciprocal rank fusion (`RRF_K = 60`).

The scores are used **for citation only** (`retrieval_chunk_id`,
`retrieval_score`). Policies are presented to the model in fixed policy-file
order. Since nothing is truncated, ordering by score could only change which
policies the model sees first — a real effect on output, for no gain in recall.

## Reproducibility contract

Four mechanisms, each addressing a different source of drift:

1. **One chokepoint.** Every model call goes through `llm_client.chat_json`,
   which fixes `temperature` and `seed`. Setting them per call site is how they
   drift apart.
2. **`seed` plus `system_fingerprint`.** `temperature=0` alone is not
   determinism — on a batched backend, greedy decoding still varies with request
   grouping. The fingerprint is recorded on every report; if it changes between
   runs, the serving backend moved and output differences are expected rather
   than a bug in the prompts.
3. **Fixed grid.** The model must return exactly one verdict per candidate
   policy, including `"applies": false`. Letting it omit non-applicable policies
   made the *number of findings* a model decision, so two runs of one repo
   produced different-sized reports and no rate had a stable denominator.
4. **Sorted walk.** `os.walk` yields entries in filesystem order, which is
   neither sorted nor stable. The holistic pass fills a fixed character budget in
   that order and drops what no longer fits, so an unsorted walk would decide
   which files that pass can even see.

**The invariant:** a report's finding count is a pure function of the repo's file
list, independent of model output. Two runs of one repo differing in
`total_findings` means an API call failed — check `errors`, not the prompts.


## How a verdict is derived

The model never states a status. It answers two booleans and supplies a quote:

| Model output | Derived status |
|---|---|
| `applies: false` | `NOT_APPLICABLE` |
| `violation_present: false` | `COMPLIANT` |
| `violation_present: true` + quote found in the file | `NON_COMPLIANT` |
| `violation_present: true` + quote **not** found | `NEEDS_REVIEW` |
| `violation_present` unset while the policy applies | `NEEDS_REVIEW` |

## Confidence

Confidence is **measured, not self-reported**. A model asked to rate its own
certainty answers near-identically to everything, which carries no information.

Each prompt is sampled `k` times (`--samples/-k`, default 3) at
`VOTE_TEMPERATURE = 0.3` over a fixed seed sequence, so the *set* of samples is
itself reproducible. The verdict is the majority; confidence is the fraction that
agreed. A tie becomes `NEEDS_REVIEW`. The losing samples' argument is preserved
in `dissent` — a check that passed 2-1 is only reviewable if you can read the
other side.

At `k=1` no disagreement is measurable, so every confidence is 1.0 and the
remediation confidence gate never fires. `audit_samples` is recorded on each
report: **two reports are only comparable if it matches.**

## Scoring

```
rate = weight of passing checks / weight of (passing + failing) checks
HIGH = 3    MEDIUM = 2    LOW = 1
```

`NOT_APPLICABLE` is excluded from the denominator — a check correctly skipped is
not a check passed, and counting them would let a repository score well by having
little the policies cover. `NEEDS_REVIEW` is excluded from both sides and
reported separately; an undecided verdict is not evidence either way.

## Data contracts

`agents/schemas.py` holds the Pydantic models shared across stages, and is the
only definition of the report format — `machine_report.json` is whatever
`ComplianceReport.model_dump_json()` produces.

A consumer that needs a JSON Schema for it can generate one on demand:

```bash
./venv/bin/python -c "import json; from agents.schemas import ComplianceReport; \
print(json.dumps(ComplianceReport.model_json_schema(), indent=2))"
```
