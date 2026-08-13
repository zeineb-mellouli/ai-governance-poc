# Production readiness

This is a proof of concept. It works end to end, but the list below is what
stands between it and production. Nothing here is a surprise waiting to be
discovered — it is the known ledger.

Ordered by how much it should worry you.

---

## 1. Reports contain the secrets they find

**Verified, and it affects the CI examples in [OPERATIONS.md](OPERATIONS.md).**

Evidence grounding requires the model to quote **verbatim** from the file. When
SEC-3 finds a hardcoded credential, that credential is copied into
`finding.evidence`, and therefore into `machine_report.json` and
`draft_report.md`. The bundled `reports/FinalProject/machine_report.json`
contains a literal `sk-prod-…` API key.

The CI snippets publish the report directory as a **build artifact**, which in
most CI systems is readable by anyone who can see the build.

Before shipping, choose one:

- Redact matched secret values before writing the report (keep enough of the
  quote to locate the line — e.g. first 4 characters plus length).
- Treat the report directory as a secret: restricted artifact storage, short
  retention.
- Emit two reports — a redacted one for artifacts, a full one for a controlled
  destination.

Related, and lower risk: the Repository Agent already withholds CSV cell values
from prompts, sending only value **shape** labels (`email-like`, `placeholder`).
That protection covers data files, not source code.

## 2. No concurrency

`auditor_agent.audit` iterates files in a plain `for` loop; `main.py batch`
iterates repositories the same way. Every call is sequential.

The bundled 10-repository corpus is 414 audit calls at the default k=3. On a
real monorepo this is the difference between a CI step and a CI timeout.

Parallelising per file is straightforward — the calls are independent and the
verdict grid is assembled by policy id, not by arrival order. Two constraints:
respect the deployment's rate limit, and keep `fingerprints` append-safe.

## 3. ChromaDB is a local file store with a runtime model download

`chroma_db/` is a `PersistentClient` directory on local disk. It is gitignored,
so **every CI run rebuilds it** — that is why `scripts/setup_chromadb.py` appears in both
pipeline examples.

The collection uses Chroma's `DefaultEmbeddingFunction`, which downloads an ONNX
MiniLM model on first use. In CI that is an unpinned network dependency and a
cold-start cost on every run, in a step that otherwise looks instant.

Options: bake the store into a container image, cache the model directory, or
declare the embedding function explicitly and pin it.

Note also that the store is **not rebuilt automatically** when
`policies/policies.yaml` changes. Editing a policy and re-running an audit
without `scripts/setup_chromadb.py` silently retrieves against the old text.

## 4. Retry and rate-limit behaviour is whatever the SDK defaults to

`llm_client.chat_json` calls the OpenAI SDK directly with no explicit retry
configuration, so it inherits the SDK default (2 retries). There is no tuned
backoff, no 429 handling for sustained load, and no circuit breaker.

A failed call is recorded in `report.errors` rather than lost, so a degraded run
is at least visible to anyone who reads them. But at production request volumes
the default is unlikely to be enough, and nothing currently stops a run that
failed on most of its files from being read as a clean report.

## 5. Coverage limits from truncation

Two caps, both silent in the report body:

- `MAX_CONTENT_CHARS = 6000` per file. Longer files are truncated with a marker.
- `MAX_REPO_CONTEXT_CHARS = 30000` for the holistic pass. Files that no longer
  fit are listed as omitted in the prompt and are not evaluated by that pass.

The first interacts badly with the anti-fabrication control: evidence grounding
is **skipped** for a truncated file, because a genuine quote may sit in the part
that was cut. So the fabrication check is weakest exactly where the model has
seen least. Large files are the case to watch.

## 6. The Config Agent does not exist

A fourth stage covering live Azure/Databricks resources was designed and cut for
lack of credentials. The runtime path is **Git-only**.

It is not stubbed and not referenced anywhere in the code — there is nothing to
switch on. Anything that requires inspecting deployed infrastructure (as opposed
to the code that defines it) is out of scope today.

## 7. Prompt injection is mitigated by instruction, not structurally

All three prompts instruct the model to treat file content as data and to ignore
embedded claims of prior approval or exemption. `sample_repos/adversarial/`
exercises this.

It is a mitigation, not a guarantee. The structural protections are what actually
carry the weight: applicability is decided in code from globs, status is derived
from booleans the model sets rather than stated by it, and a violation needs a
quote that really appears in the file. A repository whose content is fully
untrusted deserves a stronger threat model than "we asked it not to".

## 8. Operational gaps

- **No auth on the dashboard.** `main.py dashboard` runs Streamlit unauthenticated
  on localhost. Do not expose it without putting something in front of it.
- **Everything must run from the repository root.** `policies/policies.yaml`,
  `chroma_db/` and sample paths are all cwd-relative.
- **No structured logging.** Errors are plain strings on `report.errors`; there
  are no metrics, traces, or per-call timings.
- **No caching between runs.** An unchanged file costs the same on every audit.
  Content-hash caching is the obvious win if cost becomes the binding constraint.
- **Reports are not versioned against policy changes.** A report does not record
  which policy revision produced it, so two reports from different policy
  versions look comparable and are not. `audit_samples` and
  `model_fingerprints` are recorded; a policy hash is not.

## 9. There is no automated test suite

The pipeline has no unit or integration tests. Verification is manual: run an
audit against `sample_repos/` with real API calls and read the output.

That covers prompt quality and whether findings are correct — which tests could
not have told you anyway — but it leaves three gaps:

- **Pure logic is unverified.** The NAM-5 naming grammar, `_suggest_name`, the
  dependency-pinning parser, the weighted-score arithmetic, `_vote`, and the
  walker's exclusion rules are all deterministic functions whose correctness a
  real run does not demonstrate; you would have to read a report and reason
  backwards.
- **A regression is indistinguishable from model drift.** At k=3 a real run
  varies between runs by design. If a change makes the auditor drop rows, the
  report gets smaller — but reports also shrink for legitimate reasons, so
  eyeballing output cannot separate the two.
- **Error paths cannot be reached on purpose.** Making exactly one file's API
  call fail, or making the model return a fabricated quote to confirm evidence
  grounding rejects it, is not something a real run lets you arrange.

If this goes to production, a small suite around the deterministic half is the
cheapest thing to add: those functions need no API access and no fixtures beyond
the sample repositories already in the tree.

## 10. Evaluation is small and self-labelled

Ground truth is hand-authored by one person against policies written by the same
person, across 10 repositories. Only NAM-5 (30 instances) and DQ-1 (5) have
enough labelled instances for per-policy F1 to mean anything.

This is adequate for a PoC and not adequate to make a claim about accuracy on
someone else's code. Before trusting it as a merge control on real repositories,
label a sample of those repositories and re-measure. See
[EVALUATION.md](EVALUATION.md).

---

## What is genuinely solid

So the ledger above is read in proportion:

- The reproducibility contract holds by construction. Finding count is a pure
  function of the file list, so report-size drift means a failed call, not a
  changed opinion.
- Status is derived from structured booleans, not parsed out of prose. A verdict
  that contradicts its own evidence is unrepresentable.
- Confidence is measured agreement across k samples, not a number the model
  asserts about itself.
- Deterministic checks (REPO-9, NAM-5, REPRO-13) never reach a model and cannot
  drift.
- Remediation cannot silently rewrite an Auditor verdict, and generated fixes
  pass a safety net that refuses data-destroying commands.
- Partial failure is contained: one bad file does not abort a run, and every
  failure is recorded on the report.
