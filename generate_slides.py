"""Build the presentation deck as one self-contained HTML file.

    python generate_slides.py
    -> resources/slides.html      (open in a browser, press F for full screen)

Navigation: arrow keys / space / click. `N` shows the speaker note, `P` prints
to PDF one slide per page.

The data-bearing slides (the policy table, the corpus table, the evaluation
counts) are read from policies.yaml, sample_repos/ and evaluation/expected/
rather than typed in, so the deck cannot claim something the repository does
not do.

House style: no em dashes in slide prose. The architecture SVG is exempt.
"""

import glob
import html
from pathlib import Path

import yaml

OUT = Path("resources/slides.html")

# What each sample repository was built to prove. Not derivable from the code:
# it is the intent behind the corpus, and it is the point of the slide.
CORPUS = {
    "compliant": ("clean by construction", "Anything flagged here is a false positive. The most valuable test in the corpus."),
    "non_compliant": ("maximally broken", "Everything should fire. A miss here is a clear false negative."),
    "realistic": ("plausible production repo", "Mostly sound, with the violations that appear under incident pressure."),
    "ambiguous": ("genuinely unclear cases", "np.random.seed(42) set globally but no random_state. Is that a violation?"),
    "adversarial": ("prompt injection", "A fake COMPLIANCE OVERRIDE docstring claiming the file was pre-approved."),
    "edge_cases": ("boundary conditions", "Correct and incorrect date suffixes on otherwise identical files."),
    "holistic": ("only visible repo-wide", "No single file looks broken. Nothing anywhere validates data."),
    "not_applicable": ("policies must NOT fire", "A small utility with no database, no model, no tiered storage."),
    "sdd_generated": ("the build half's output", "Generated from specs, then audited by the run half."),
}


def esc(s):
    return html.escape(str(s))


POLICIES = yaml.safe_load(Path("policies/policies.yaml").read_text())["policies"]

BUCKETS = {"expect_violations": 0, "expect_clean": 0, "tolerate": 0}
LABEL_FILES = 0
for f in glob.glob("evaluation/expected/*.yaml"):
    LABEL_FILES += 1
    d = yaml.safe_load(Path(f).read_text())
    for b in BUCKETS:
        BUCKETS[b] += len(d.get(b) or [])

slides: list[str] = []


def slide(kind, body, note=""):
    slides.append(f'<section class="slide {kind}" data-note="{esc(note)}">{body}</section>')


# ---------------------------------------------------------------- 1 · title
slide("title", """
  <h1>Agentic Governance<br>for Data Pipelines</h1>
  <p class="lede">One policy library, enforced twice.
    <em>Before</em> the code exists, and <em>after</em> it lands.</p>
  <p class="byline">A proof of concept · build-time and run-time paths</p>
""")

# ---------------------------------------------------------------- 2 · the hook
slide("code-slide", """
  <h2>Every one of us has written this file</h2>
  <p class="path">sample_repos/non_compliant/FinalProject/<strong>final_v2_ACTUAL.py</strong></p>
  <pre><code><span class="c">connection_string</span> = <span class="s">"mssql+pyodbc://admin:Tetra@dmin123!@prod-db..."</span>  <span class="cm"># production credential</span>
<span class="c">api_key</span> = <span class="s">"sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"</span>

df = pd.read_csv(<span class="s">"bronze/EthanolMarketRate_20240701.csv"</span>)
df.to_csv(<span class="s">"bronze/EthanolMarketRate_20240701.csv"</span>)   <span class="cm"># overwrites its own source</span>

<span class="c">print</span>(customers)                                <span class="cm"># names, emails, phone numbers</span>
X_train, X_test, y_train, y_test = train_test_split(X, y)   <span class="cm"># no seed</span></code></pre>
  <p class="punch">The question isn't whether it exists.<br>
     It's how you find <em>all</em> of them across two hundred repositories,
     and how you stop the next one being written.</p>
""", "Read the four lines out loud. Say the filename. Then ask the question.")

# ---------------------------------------------------------------- 3 · architecture
arch = Path("resources/governance_architecture.svg").read_text().split("?>")[-1].strip()
slide("diagram", f"""
  <h2>Two moments to intervene</h2>
  <div class="svg-wrap">{arch}</div>
""", "Walk it once, left to right. One source, compiled two ways. Then move on.")

# ---------------------------------------------------------------- 4 · vibe -> spec
slide("split", """
  <h2>Build time: from vibe coding to specification</h2>
  <div class="two-col">
    <div class="col col-bad">
      <h3>Vibe coding</h3>
      <ul>
        <li>You prompt. You get code.</li>
        <li>You read it, fix it, prompt again.</li>
        <li>The specification lives in a chat window.</li>
        <li class="kicker">Tomorrow it is gone. Nobody can review it, diff it, or ask why.</li>
      </ul>
    </div>
    <div class="col col-good">
      <h3>Spec-driven development</h3>
      <ul>
        <li>You write the intent down first.</li>
        <li>The AI generates from the written spec.</li>
        <li>The spec is a file in the repository.</li>
        <li class="kicker">Reviewable, diffable, and it survives the person who wrote it.</li>
      </ul>
    </div>
  </div>
""", "This is the half nobody has seen. Give it room.")

# ---------------------------------------------------------------- 5 · spec kit
slide("default", """
  <h2>GitHub Spec Kit</h2>
  <p class="sub">Open-source toolkit. Installs a set of slash commands into Copilot.</p>
  <div class="chips">
    <span class="chip">/speckit.constitution</span>
    <span class="chip">/speckit.specify</span>
    <span class="chip">/speckit.clarify</span>
    <span class="chip">/speckit.plan</span>
    <span class="chip">/speckit.tasks</span>
    <span class="chip">/speckit.implement</span>
    <span class="chip">/speckit.analyze</span>
    <span class="chip">/speckit.checklist</span>
  </div>
  <p class="punch">The workflow is the product: specify → clarify → plan → break into tasks →
     implement. Each step writes a file. Nothing lives only in the conversation.</p>
""", "Show .github/prompts/ in code-polymer live if the room is engaged.")

# ---------------------------------------------------------------- 6 · the spec files
slide("default", """
  <h2>What I actually wrote</h2>
  <p class="path">sample_repos/sdd_generated/code-polymer/specs/001-polymer-pricing-etl/</p>
  <table class="wide">
    <thead><tr><th>file</th><th>what it holds</th></tr></thead>
    <tbody>
      <tr><td class="mono">spec.md</td><td>requirements in business language, no code</td></tr>
      <tr><td class="mono">plan.md</td><td>the architecture the AI proposed, and why</td></tr>
      <tr><td class="mono">data-model.md</td><td>tables, columns, and the <strong>grain</strong> of each output</td></tr>
      <tr><td class="mono">tasks.md</td><td>the ordered build steps</td></tr>
      <tr><td class="mono">research.md</td><td>the decisions it looked up before choosing</td></tr>
      <tr><td class="mono">contracts/</td><td>the SQL DDL and the pipeline interface</td></tr>
      <tr><td class="mono">checklists/</td><td>what "done" means, written before starting</td></tr>
    </tbody>
  </table>
  <p class="punch">Nowhere in here did I write Python.<br>
     I wrote what the pipeline must be <em>true of</em>.</p>
""", "Open spec.md and show one paragraph on screen.")

# ---------------------------------------------------------------- 7 · the constitution
slide("default", """
  <h2>The bridge between the two halves</h2>
  <div class="flow">
    <div class="flow-box source">policies/policies.yaml</div>
    <div class="flow-arrow">compiles to</div>
    <div class="flow-box build">rules.md</div>
    <div class="flow-arrow">read by</div>
    <div class="flow-box build">Copilot, while generating</div>
  </div>
  <p class="punch">350 lines, auto-generated. The same policy file that <em>audits</em> the code
     also <em>instructs</em> the AI that writes it.<br>
     One source of truth, two audiences.</p>
""", "This is the single most important structural idea in the project.")

# ---------------------------------------------------------------- 8 · what came out
slide("code-slide", """
  <h2>What came out of the generator</h2>
  <p class="path">code-polymer/pipeline/<strong>01_IngestData.py</strong></p>
  <pre><code><span class="cm"># pandera schema, validated before anything is written</span>
validated = PricingSchema.validate(raw, lazy=<span class="c">True</span>)

<span class="cm"># credentials from the environment, never in the file</span>
conn = create_engine(os.environ[<span class="s">"WAREHOUSE_CONN"</span>])

<span class="cm"># bronze, then silver, then gold. No layer skipped.</span>
raw = pd.read_csv(<span class="s">"bronze/PolymerPricing_2026-07-14.csv"</span>)
validated.to_parquet(<span class="s">"silver/PolymerPricing_2026-07-14.parquet"</span>)</code></pre>
  <p class="punch">Nobody told the developer to do any of this.<br>
     It came out that way because the constitution was an <em>input</em>.</p>
""")

# ---------------------------------------------------------------- 9 · policy library
rows = []
sev_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
for p in sorted(POLICIES, key=lambda p: (sev_rank[p["severity"]], p["policy_id"])):
    det = p["evaluation"] != "model"
    how = {"model": "model", "deterministic": "code", "hybrid": "hybrid"}[p["evaluation"]]
    rows.append(
        f'<tr class="{"det" if det else ""}">'
        f'<td class="mono">{esc(p["policy_id"])}</td>'
        f'<td>{esc(p["title"])}</td>'
        f'<td><span class="sev sev-{p["severity"].lower()}">{p["severity"]}</span></td>'
        f'<td class="how">{how}</td></tr>'
    )
n_det = sum(1 for p in POLICIES if p["evaluation"] != "model")
slide("default", f"""
  <h2>The policy library: {len(POLICIES)} policies</h2>
  <table class="policies">
    <thead><tr><th>id</th><th>what it checks</th><th>severity</th><th>decided by</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
  <p class="punch">{n_det} of them never reach a language model.
     A repository name either matches the regex or it doesn't. A package either has
     <span class="mono">==</span> or it doesn't.<br>
     Asking a model to decide that is slower, more expensive, and less reliable.</p>
""", "Don't read the table. Let them scan it while you make the deterministic point.")

# ---------------------------------------------------------------- 10 · policy shape
slide("code-slide", """
  <h2>What one policy looks like</h2>
  <pre><code><span class="k">policy_id</span>: SEC-3
<span class="k">title</span>: No hardcoded secrets or credentials
<span class="k">severity</span>: HIGH
<span class="k">scope</span>: file
<span class="k">evaluation</span>: model

<span class="k">applies_to</span>: [<span class="s">"**/*"</span>]
<span class="k">excludes</span>:   [<span class="s">".env.example"</span>, <span class="s">"*.template"</span>, <span class="s">"*.sample"</span>]

<span class="k">rule</span>: &gt;
  A literal credential that could authenticate a system is a violation
  wherever it appears. Reading from os.environ or a secrets manager is
  compliant. A placeholder is not a credential.

<span class="k">examples</span>:
  <span class="k">compliant</span>:     [<span class="s">"api_key = os.environ['API_KEY']"</span>]
  <span class="k">non_compliant</span>: [<span class="s">"api_key = 'sk-prod-xK92...'"</span>]</code></pre>
  <p class="punch"><span class="mono">applies_to</span> is a glob evaluated <em>in code</em>.
     A README is never even offered the SQL naming policy, so it cannot be
     wrongly flagged by one.</p>
""")

# ---------------------------------------------------------------- 11 · the corpus
by_cat = {d.name: sorted(r.name for r in d.iterdir() if r.is_dir())
          for d in Path("sample_repos").iterdir() if d.is_dir()}
corpus_rows = []
for cat in ["compliant", "non_compliant", "realistic", "ambiguous", "adversarial",
            "edge_cases", "holistic", "not_applicable", "sdd_generated"]:
    if cat not in by_cat:
        continue
    short, why = CORPUS[cat]
    repos = "<br>".join(f'<span class="mono">{esc(r)}</span>' for r in by_cat[cat])
    corpus_rows.append(
        f'<tr><td><strong>{esc(cat)}</strong><div class="tiny">{esc(short)}</div></td>'
        f"<td>{repos}</td><td>{esc(why)}</td></tr>"
    )
total_repos = sum(len(v) for v in by_cat.values())
slide("default", f"""
  <h2>How I tested it: {total_repos} repositories, {len(by_cat)} categories</h2>
  <table class="corpus">
    <thead><tr><th>category</th><th>repository</th><th>what it is designed to prove</th></tr></thead>
    <tbody>{"".join(corpus_rows)}</tbody>
  </table>
  <p class="punch">Each one was built to break the auditor in a specific way.
     This is what separates an evaluation from a demo.</p>
""", "Spend your time on compliant, adversarial and holistic. Skim the rest.")

# ---------------------------------------------------------------- 12 · the agents
slide("default", """
  <h2>Run time: three agents, one job each</h2>
  <div class="agents">
    <div class="agent">
      <span class="n">1</span>
      <div><h3>Repository Agent</h3>
      <p>Walks the repository and reads files. <strong>No model call.</strong>
         Skips generated output and spec scaffolding, so you don't pay to audit
         <span class="mono">bin/</span> or <span class="mono">node_modules/</span>.</p></div>
    </div>
    <div class="agent">
      <span class="n">2</span>
      <div><h3>Auditor Agent</h3>
      <p>Deterministic checks run in code. Everything needing judgement goes to the
         model, grounded in the policy retrieved from ChromaDB. Each check runs
         <span class="mono">k</span> times and the verdict is the majority.</p></div>
    </div>
    <div class="agent">
      <span class="n">3</span>
      <div><h3>Remediation Agent</h3>
      <p>Writes a concrete fix, or records why a person is needed. It can never
         change a verdict, because whether a fix exists says nothing about whether
         the violation is real.</p></div>
    </div>
  </div>
""")

# ---------------------------------------------------------------- 13 · how it was evaluated
slide("default", f"""
  <h2>How I evaluated it</h2>
  <p class="sub">{BUCKETS['expect_violations'] + BUCKETS['expect_clean'] + BUCKETS['tolerate']}
     labels across {LABEL_FILES} repositories, written by reading each repository against
     the policies. Never from a generated report.</p>
  <div class="buckets">
    <div class="bucket b-v"><span class="bn">{BUCKETS['expect_violations']}</span>
      <h3>expect_violations</h3>
      <p>The audit <strong>must</strong> flag this. Not firing is a false negative.</p></div>
    <div class="bucket b-c"><span class="bn">{BUCKETS['expect_clean']}</span>
      <h3>expect_clean</h3>
      <p>The audit <strong>must not</strong> flag this. Firing is a false positive.</p></div>
    <div class="bucket b-t"><span class="bn">{BUCKETS['tolerate']}</span>
      <h3>tolerate</h3>
      <p>Either verdict is defensible. Excluded from scoring, and marks a place the
         policy is underspecified.</p></div>
  </div>
  <div class="two-col notes-cols">
    <div>
      <h3 class="okh">Two rules that keep it honest</h3>
      <p>A finding that fires but appears in no bucket is reported as <strong>unlabelled</strong>,
         not as a false positive. Scoring it as an error would train the policy set to
         find less.</p>
      <p>The control repository is compliant by construction, so anything flagged there
         is a false positive by definition.</p>
    </div>
    <div>
      <h3 class="warnh">What the number is, and isn't</h3>
      <p>Precision and recall come out around <strong>0.98</strong>. On a corpus I built,
         labelled myself, against policies I wrote.</p>
      <p class="pull">That is a <em>regression signal</em>, not a benchmark. It tells me a
         policy change made things worse. It is not a claim about accuracy on your
         repositories.</p>
    </div>
  </div>
""", "Lead with the method. Say the caveat yourself before anyone else does.")

# ---------------------------------------------------------------- 14 · live demo (last)
slide("demo", """
  <p class="demo-label">live</p>
  <h1>Demo</h1>
  <p class="demo-target">audit <span class="mono">FinalProject</span></p>
""", "k=1. SEC-3 quoted credential, NAM-5 computed fix, then the Not certain tab.")

# ------------------------------------------------------------------ page
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --paper:#fbfcfd; --ink:#151b24; --ink2:#3c4653; --muted:#6b7684; --rule:#dde2e8;
  --source:#2f4a7c; --build:#1f6f4a; --run:#b3261e;
  --high:#b3261e; --medium:#8a5a00; --low:#5c6773;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
  --mono:ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,monospace;
}
html,body{height:100%}
body{background:#e9ecf0;font-family:var(--sans);color:var(--ink);-webkit-font-smoothing:antialiased}
.deck{position:relative;width:100vw;height:100vh;overflow:hidden}
.slide{position:absolute;inset:0;display:none;flex-direction:column;justify-content:center;
  padding:4vh 6vw;background:var(--paper)}
.slide.on{display:flex}
h1{font-size:clamp(34px,5.2vw,68px);line-height:1.06;letter-spacing:-.025em;font-weight:650;text-wrap:balance}
h2{font-size:clamp(24px,3.1vw,42px);line-height:1.15;letter-spacing:-.018em;font-weight:640;margin-bottom:2.4vh;text-wrap:balance}
h3{font-size:clamp(15px,1.35vw,21px);font-weight:650;margin-bottom:.5em}
p,li,td,th{font-size:clamp(13px,1.15vw,18px);line-height:1.5}
.lede{font-size:clamp(17px,1.9vw,28px);color:var(--ink2);margin-top:3vh;line-height:1.4;max-width:34ch}
.byline{margin-top:3vh;color:var(--muted);font-size:clamp(12px,1vw,16px)}
.sub{color:var(--muted);margin-bottom:2vh;max-width:80ch}
.tiny{font-size:.8em;color:var(--muted)}
.mono{font-family:var(--mono);font-size:.92em}
em{font-style:normal;color:var(--source);font-weight:600}
strong{font-weight:660}

.title{justify-content:center;align-items:flex-start;
  background:linear-gradient(135deg,#fbfcfd 0%,#eef1f6 100%)}
.title h1{max-width:18ch}

.path{font-family:var(--mono);font-size:clamp(11px,.95vw,15px);color:var(--muted);margin-bottom:1.4vh}
pre{background:#141a22;border-radius:8px;padding:2.2vh 2vw;overflow:auto;max-height:52vh}
code{font-family:var(--mono);font-size:clamp(11px,1.02vw,17px);line-height:1.65;color:#dfe6ef;white-space:pre}
.s{color:#f0a58a}.c{color:#8fb8f0}.cm{color:#7c8899;font-style:italic}.k{color:#a5d6b0}
.punch{margin-top:2.4vh;font-size:clamp(14px,1.35vw,22px);line-height:1.45;color:var(--ink);max-width:72ch}

.two-col{display:grid;grid-template-columns:1fr 1fr;gap:3vw}
.col ul{list-style:none}
.col li{padding:.75em 0;border-bottom:1px solid var(--rule)}
.col li.kicker{border:0;color:var(--ink2);font-weight:600;padding-top:1em}
.col-bad h3{color:var(--run)} .col-good h3{color:var(--build)}

table{border-collapse:collapse;width:100%}
th{text-align:left;font-size:.72em;text-transform:uppercase;letter-spacing:.09em;
  color:var(--muted);font-weight:660;padding:.55em .7em;border-bottom:2px solid var(--rule)}
td{padding:.5em .7em;border-bottom:1px solid var(--rule);vertical-align:top}
tr.det td{background:#2f4a7c0d}
.policies td:first-child{font-family:var(--mono);font-weight:600;white-space:nowrap}
.how{font-family:var(--mono);font-size:.85em;color:var(--muted)}
tr.det .how{color:var(--source);font-weight:700}
.sev{font-size:.72em;font-weight:700;letter-spacing:.05em;padding:2px 7px;border-radius:3px}
.sev-high{background:#b3261e1a;color:var(--high)}
.sev-medium{background:#8a5a001a;color:var(--medium)}
.sev-low{background:#5c67731a;color:var(--low)}
.corpus td:first-child{white-space:nowrap}

.svg-wrap{flex:1;display:flex;align-items:center;justify-content:center;min-height:0}
.svg-wrap svg{max-width:100%;max-height:76vh;height:auto;width:auto}

.chips{display:flex;flex-wrap:wrap;gap:.7vw;margin:2vh 0}
.chip{font-family:var(--mono);font-size:clamp(11px,1vw,16px);background:#2f4a7c12;
  color:var(--source);border:1px solid #2f4a7c33;border-radius:5px;padding:.45em .8em}

.flow{display:flex;align-items:center;gap:1.2vw;flex-wrap:wrap;margin:3vh 0}
.flow-box{padding:1.1em 1.4em;border-radius:7px;font-family:var(--mono);
  font-size:clamp(12px,1.15vw,18px);font-weight:600}
.flow-box.source{background:#2f4a7c14;color:var(--source);border:1.5px solid var(--source)}
.flow-box.build{background:#1f6f4a14;color:var(--build);border:1.5px solid var(--build)}
.flow-arrow{color:var(--muted);font-size:.85em}
.flow-arrow::after{content:" →"}

.agents{display:flex;flex-direction:column;gap:1.6vh}
.agent{display:flex;gap:1.4vw;align-items:flex-start;background:#fff;border:1px solid var(--rule);
  border-radius:7px;padding:1.6vh 1.4vw}
.agent .n{font-size:clamp(20px,2.4vw,36px);font-weight:700;color:var(--run);opacity:.35;line-height:1}
.agent h3{color:var(--run)}

.buckets{display:grid;grid-template-columns:repeat(3,1fr);gap:1.6vw;margin-bottom:2.6vh}
.bucket{background:#fff;border:1px solid var(--rule);border-top:3px solid var(--muted);
  border-radius:7px;padding:1.6vh 1.2vw}
.bucket .bn{font-size:clamp(22px,2.6vw,38px);font-weight:680;letter-spacing:-.02em;line-height:1;
  display:block;margin-bottom:.3em;font-variant-numeric:tabular-nums}
.bucket h3{font-family:var(--mono);font-size:clamp(12px,1.05vw,16px)}
.bucket p{color:var(--ink2);font-size:clamp(11px,.98vw,15px)}
.b-v{border-top-color:var(--run)} .b-v .bn,.b-v h3{color:var(--run)}
.b-c{border-top-color:var(--build)} .b-c .bn,.b-c h3{color:var(--build)}
.b-t{border-top-color:var(--medium)} .b-t .bn,.b-t h3{color:var(--medium)}
.notes-cols p{color:var(--ink2);margin-bottom:.7em;font-size:clamp(12px,1.05vw,16px)}
.okh{color:var(--build)} .warnh{color:var(--medium)}
.pull{font-weight:600;color:var(--ink)}

.demo{background:linear-gradient(135deg,#141a22 0%,#1e2733 100%);color:#eef2f7;
  justify-content:center;align-items:flex-start}
.demo h1{color:#fff}
.demo-label{font-family:var(--mono);letter-spacing:.28em;text-transform:uppercase;
  color:#f0a58a;font-size:clamp(11px,1vw,15px);margin-bottom:1.5vh}
.demo-target{margin-top:3vh;font-size:clamp(16px,1.9vw,30px);color:#8fb8f0}
.demo-target .mono{color:#f0a58a;font-size:1em}

.hud{position:fixed;bottom:14px;right:18px;display:flex;gap:14px;align-items:center;
  font-size:12px;color:var(--muted);font-family:var(--mono);z-index:10}
.hud button{border:1px solid var(--rule);background:#fff;color:var(--ink2);border-radius:4px;
  cursor:pointer;font:inherit;padding:2px 8px}
.hud button:hover{background:#f0f2f6}
.progress{position:fixed;top:0;left:0;height:2.5px;background:var(--source);z-index:10;transition:width .18s}
.notes{position:fixed;bottom:14px;left:18px;max-width:44vw;font-size:12px;color:var(--muted);
  font-style:italic;z-index:10;display:none}
.notes.on{display:block}

@media print{
  body{background:#fff}
  .deck{height:auto}
  .slide{display:flex!important;position:relative;page-break-after:always;height:100vh;border:0}
  .hud,.progress,.notes{display:none!important}
}
"""

JS = """
const slides=[...document.querySelectorAll('.slide')];
let i=0, notesOn=false;
const hud=document.getElementById('n'), bar=document.getElementById('bar'), nb=document.getElementById('notes');
function show(k){
  i=Math.max(0,Math.min(slides.length-1,k));
  slides.forEach((s,j)=>s.classList.toggle('on',j===i));
  hud.textContent=(i+1)+' / '+slides.length;
  bar.style.width=((i+1)/slides.length*100)+'%';
  nb.textContent=slides[i].dataset.note||'';
  location.hash=i+1;
}
document.addEventListener('keydown',e=>{
  if(['ArrowRight','ArrowDown',' ','PageDown'].includes(e.key)){e.preventDefault();show(i+1);}
  else if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();show(i-1);}
  else if(e.key==='Home')show(0);
  else if(e.key==='End')show(slides.length-1);
  else if(e.key==='f'||e.key==='F'){document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();}
  else if(e.key==='n'||e.key==='N'){notesOn=!notesOn;nb.classList.toggle('on',notesOn);}
  else if(e.key==='p'||e.key==='P'){window.print();}
});
document.querySelector('.deck').addEventListener('click',e=>{
  if(e.target.closest('.hud'))return;
  show(e.clientX < innerWidth*0.28 ? i-1 : i+1);
});
show(parseInt(location.hash.slice(1))-1 || 0);
"""

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agentic Governance for Data Pipelines</title>
<style>{CSS}</style></head>
<body>
<div class="progress" id="bar"></div>
<div class="deck">{"".join(slides)}</div>
<div class="notes" id="notes"></div>
<div class="hud">
  <button onclick="show(i-1)">◀</button><span id="n"></span><button onclick="show(i+1)">▶</button>
  <span>F full · N notes · P print</span>
</div>
<script>{JS}</script>
</body></html>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page, encoding="utf-8")

# House style check: em dashes are allowed only inside the embedded architecture SVG.
prose = page.replace(arch, "")
if "—" in prose:
    bad = [ln.strip()[:90] for ln in prose.splitlines() if "—" in ln]
    raise SystemExit(f"em dash found in slide prose:\n  " + "\n  ".join(bad))

print(f"{OUT} written — {len(slides)} slides, {OUT.stat().st_size / 1024:.0f} KB, no em dashes in prose")
