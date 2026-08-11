# Agentic Governance for Data Pipelines — 60 minute session

Audience: data engineers and data scientists who have never seen this project.
Budget: **~40 min presented · ~20 min questions**. Five slides came out, so
there is more room for the demo and the discussion than the section timings below
suggest.

**The deck:** `resources/slides.html` — open in a browser, press `F` for full
screen. `N` toggles the speaker note for the current slide, `P` prints to PDF.
Regenerate with `python generate_slides.py` after changing policies or reports.
This file is the script; the deck is the visual. Slide numbers below match.

The through-line, stated once at the start and returned to at the end:

> **Governance has two moments: before the code exists, and after it lands.
> Most tools pick one. This does both, from a single policy library.**

---

## 1 · The file everyone in the room recognises — 4 min  ·  slides 1–2

Do **not** open with "governance matters". Open with code on screen:
`sample_repos/non_compliant/FinalProject/final_v2_ACTUAL.py`

Read four lines out loud:

```python
connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db..."   # prod credential
api_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"
df = pd.read_csv("bronze/EthanolMarketRate_20240701.csv")
df.to_csv("bronze/EthanolMarketRate_20240701.csv")                      # overwrites its own source
print(customers)                                                         # names, emails, phones
X_train, X_test, y_train, y_test = train_test_split(X, y)                # no seed
```

Then the question that makes it *their* problem, not yours:

> Every one of us has written this file. The question is not whether it exists —
> it's how you find all of them across two hundred repositories, and how you stop
> the next one being written.

Say the filename out loud: `final_v2_ACTUAL.py`. It gets a laugh and it earns
attention.

---

## 2 · Two moments to intervene — 3 min  ·  slide 3

One slide, the architecture diagram (`resources/governance_architecture.svg`).

Walk it left to right, exactly once:

- **One source.** `policies/policies.yaml` — 14 policies. The only place a rule
  is ever written.
- **It compiles two ways.** `rules.md` for the AI that writes code.
  `chroma_db` for the agent that audits code. Same rules, two audiences.
- **Left lane — build time. Prevention.** Governance is an *input* to code
  generation.
- **Right lane — run time. Detection.** Governance is a *check* on code that
  already exists.
- **The loop.** A wrong finding is a policy defect. You fix the YAML, and both
  halves change together.

Say what is out of scope before anyone asks: **live Azure/Databricks config
auditing.** The deployed state, as opposed to the code that describes it. The
contracts accommodate a fourth agent; it isn't built.

Then move on. Do not return to this slide.

---

## 3 · Build time — from vibe coding to spec — 10 min  ·  slides 4–8

This is the half nobody in the room will have seen, so give it the most time.

### The framing (2 min)

> **Vibe coding**: you prompt, you get code, you read it, you fix it, you prompt
> again. The specification lives in a chat window and is gone tomorrow.
>
> **Spec-driven development**: you write the intent down. The AI generates from
> the written spec. The spec is reviewable, diffable, and it survives.

**GitHub Spec Kit** is the toolkit — open-source, installs a set of slash
commands into Copilot. Show `.github/prompts/` in `code-polymer`: ten commands,
`speckit.specify`, `speckit.plan`, `speckit.tasks`, `speckit.implement`.

### What I actually wrote (4 min)

Open `sample_repos/sdd_generated/code-polymer/specs/001-polymer-pricing-etl/`
and show the real files, in order:

| file | what it holds |
|---|---|
| `spec.md` | requirements in business language — no code |
| `plan.md` | the architecture the AI chose |
| `data-model.md` | tables, columns, **grain** |
| `tasks.md` | the ordered build steps |
| `contracts/` | the SQL DDL and the pipeline interface |

Show one paragraph of `spec.md` on screen. The point to land:

> Nowhere in here did I write Python. I wrote what the pipeline must be true of.

### The constitution (2 min)

`rules.md` — 350 lines, auto-generated from `policies.yaml`. Copilot reads it
alongside the spec. This is the bridge between the two halves: **the same policy
file that audits the code also instructs the AI that writes it.**

### What came out (2 min)

Open `code-polymer/pipeline/01_IngestData.py`. Point at three things:

- a `pandera` schema validated before the write
- `os.environ` for every credential
- `bronze/` → `silver/` → `gold/`, in that order

> Nobody told the developer to do this. It came out of the generator that way,
> because the constitution was an input.

---

## 4 · The policy library — 4 min  ·  slides 9–10

One slide, the table. Don't read it out — let them scan it while you talk.

| | policy | sev | decided by |
|---|---|---|---|
| DQ-1 | data quality validation present | HIGH | model |
| SEC-3 | no hardcoded secrets | HIGH | model |
| PII-4 | no raw PII in outputs | HIGH | model |
| ARCH-12 | medallion architecture | HIGH | model |
| OPS-2 | logging and monitoring | MED | model |
| REPRO-6 | random seeds fixed | MED | model |
| REPRO-14 | raw data not modified in place | MED | model |
| DM-7 | output table grain documented | MED | model |
| GIT-8 | branch and commit standards | MED | model |
| SQL-10 | SQL object naming | MED | model |
| **REPO-9** | repository naming | MED | **code** |
| **REPRO-13** | dependency versions pinned | LOW | **code** |
| **NAM-5** | file and folder naming | LOW | **hybrid** |
| SQL-11 | SQL column naming | LOW | model |

The only sentence that matters here:

> Three of these never reach a language model. A repository name either matches
> the regex or it doesn't; a package either has `==` or it doesn't. Asking a
> model to decide that is slower, more expensive, and less reliable.

Then show one policy's YAML so they see the shape — `rule`, `applies_to`,
`excludes`, `examples`. Mention that `applies_to` is a glob evaluated **in code**,
so a `README.md` is never even offered the SQL naming policy.

---

## 5 · How I tested it — the corpus — 5 min  ·  slide 11

Ten repositories, each built to break the auditor in a specific way. This slide
is what separates a demo from an evaluation.

| category | repo | what it is designed to prove |
|---|---|---|
| **compliant** | `ops-code-market_rate` | clean by construction — **anything flagged here is a false positive** |
| **non_compliant** | `FinalProject` | maximally broken — a miss here is a clear false negative |
| **realistic** | `fin-code-var_risk_model` | mostly sound, with the violations that appear under incident pressure |
| **ambiguous** | `fin-code-credit_scoring_model` | `np.random.seed(42)` globally, no `random_state` — is that a violation? |
| **adversarial** | `fin-code-collateral_management` | a fake "COMPLIANCE OVERRIDE" docstring claiming pre-approval |
| **edge_cases** | `fin-code-liquidity_forecast` | correct and incorrect date suffixes on otherwise identical files |
| **holistic** | `fin-code-fx_exposure_report` | no single file looks broken; the repo as a whole has no validation anywhere |
| **not_applicable** | `fin-code-filing_deadline_tracker` | a small utility — do policies correctly *not* apply? |
| **sdd_generated** | `code-polymer`, `ops-code-customer_churn` | the build-time output, audited by the run-time half |

Spend your time on three of them:

- **compliant** — the control. Explain why a clean repo is the most valuable
  test you have.
- **adversarial** — show the fake override docstring in the file. The auditor's
  system prompt treats file content as data, never as instructions. It still
  reported the violation.
- **holistic** — no single file is wrong. This is why there is a whole-repository
  pass in addition to the per-file one.

---

## 6 · Run time — the agents — 5 min  ·  slide 12

Three agents, sequential, each with one job:

1. **Repository Agent** — walks the repo, reads files. No model call. Skips
   generated output (`bin/`, `node_modules/`, `.venv/`) and spec scaffolding.
2. **Auditor Agent** — the deterministic checks run in code. Everything needing
   judgement goes to the model, grounded in the policy retrieved from ChromaDB.
3. **Remediation Agent** — writes a fix, or records why a person is needed.

Then the four design decisions that make it trustworthy. **This is the slide
engineers will judge you on** — don't rush it:

- **Every check runs `k` times** and the verdict is the majority. Confidence is
  the share of runs that agreed — *measured*, not the model's opinion of itself.
- **Evidence must be quoted verbatim from the file.** If the quote isn't in the
  file, the finding is routed to review instead of reported. This is the
  anti-hallucination control.
- **The model never states a verdict.** It answers `applies` / `violation_present`
  and supplies a quote. The status is derived. A verdict that contradicts its own
  evidence is unrepresentable.
- **Every file gets every applicable policy**, so the report is the same shape on
  every run. A difference between two runs is a changed verdict, not a changed
  report.

---

## 7 · How I evaluated it — 5 min  ·  slide 13

The slide shows the **method**, not a score. Deliberately: 0.98 precision on a
corpus I built, labelled myself, against policies I wrote is a regression
signal, not a benchmark. Say that yourself before anyone in the room says it
for you.

Walk the three buckets:

- **expect_violations (61)** — must fire. Not firing is a false negative.
- **expect_clean (128)** — must not fire. Firing is a false positive.
- **tolerate (11)** — either verdict is defensible. Excluded from scoring, and
  each entry marks a place the policy is genuinely underspecified.

Then the two rules that keep it honest:

- A finding that fires but appears in no bucket is reported as **unlabelled**,
  never as a false positive. Scoring it as an error would train the policy set
  to find *less*.
- The control repository is compliant by construction, so anything flagged
  there is a false positive by definition.

Close the slide on what the number is for: *"it tells me a policy change made
things worse. It is not a claim about accuracy on your repositories."*

If someone asks for the figure: **precision and recall both around 0.98**, and
the honest caveat above.

---

## 8 · Live demo — 5 min  ·  slide 14 (last)

**Repository:** `sample_repos/non_compliant/FinalProject` — 9 model calls at
k=1, under a minute, and the most dramatic output in the corpus.

**Say before you click:** *"Production runs use k=3 — three samples per check.
I'm using k=1 here so we're not watching a progress bar."*

Sequence:

1. Sidebar → **Audit a repository** → paste the path → k = 1 → **Run audit**.
   Talk over the progress bar: it is auditing file by file.
2. It lands on the new report. **41% weighted pass rate, 6 high severity.**
3. Open the **SEC-3** finding. Show the quoted credential — *the line, from the
   file*. This is the moment that converts sceptics.
4. Open **NAM-5** on a data file. Show the **computed fix** — `git mv` derived
   by a function, not written by a model.
5. Open the **Not certain** tab. Find a row reading
   `2/3 runs said clean · 1 said NON_COMPLIANT`, expand it, read the dissenting
   argument.

> The tool tells you when it isn't sure, and shows you the argument it rejected.

**Rehearse step 5 on `reports_v4` beforehand.** Know the repo and the finding.
Hunting for it live is the one thing that can flatten this.

---

## 9 · What doesn't work — spoken, no slide

No slide for this any more. Say it over the demo, or hold it for the first
question. It is still the material that wins an engineering audience, so do not
drop it entirely.

- **Self-consistency is not correctness.** Every false negative in the last run
  was at 100% agreement. A wrong policy produces the same wrong answer three
  times, confidently. Voting catches ambiguity, never systematic error.
- **`k=3` damps run-to-run variance but does not remove it.** One finding flipped
  between two runs on identical policy text.
- **The `tolerate` bucket** — 11 labels marking places the policy is genuinely
  underspecified. Recorded rather than forced into an answer.
- **Live configuration auditing is out of scope.** Code is not deployment.
- **The severity weighting is a judgement, not a measurement.** DQ-1 is HIGH
  because unvalidated data feeding a credit model is a real exposure — but that
  is my call, and it is one line of YAML to change.

The deck ends on the demo. Close verbally on the through-line: one policy
library, enforced before the code exists and after it lands, and when a rule
turns out to be wrong you fix one file and both halves change together.
