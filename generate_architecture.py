"""Draw the system architecture as an SVG.

    python generate_architecture.py
    -> resources/governance_architecture.svg

Generated rather than drawn by hand for the same reason rules.md is: the diagram
is a claim about what the code does, and a claim maintained by hand drifts from
the code within a week.

Scope is the two lanes and nothing else. The report's consumers (CI gate,
dashboard, evaluation harness), the feedback loop, and the out-of-scope note all
came off: each is a slide of its own in the deck, and a diagram that tries to
carry the whole story carries none of it.

Every connector is orthogonal -- straight down, straight across, straight in.
Diagonals across a lane boundary read as noise at projector distance.
"""

from pathlib import Path

OUT = Path("resources/governance_architecture.svg")

W, H = 1480, 720

INK = "#151b24"
MUTED = "#6b7684"
RULE = "#c9d0d9"
SOURCE = "#2f4a7c"       # the policy source
BUILD = "#1f6f4a"        # build time: prevention
RUN = "#b3261e"          # run time: detection

FONT = ("-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,"
        "'Helvetica Neue',Arial,sans-serif")
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"

parts: list[str] = []

# Column geometry. Both lanes are the same width and equidistant from the
# centre line, so every vertical connector in the diagram shares an x with the
# box above and below it.
BOX_W = 400
LX, RX = 320, 1160                      # lane centres
CX = W / 2                              # centre line


def box(x, y, w, h, title, subtitle="", colour=MUTED, mono=False):
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
        f'fill="{colour}12" stroke="{colour}" stroke-width="1.5"/>'
    )
    ty = y + (h / 2 - 6 if subtitle else h / 2 + 5)
    parts.append(
        f'<text x="{x + w / 2}" y="{ty}" text-anchor="middle" '
        f'font-family="{MONO if mono else FONT}" font-size="{14 if mono else 15.5}" '
        f'font-weight="600" fill="{colour}">{title}</text>'
    )
    for i, line in enumerate(subtitle.split("|") if subtitle else []):
        parts.append(
            f'<text x="{x + w / 2}" y="{ty + 18 + i * 15}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="12" fill="{MUTED}">{line}</text>'
        )


def down(x, y1, y2, colour):
    """A straight vertical connector."""
    parts.append(
        f'<path d="M{x},{y1} L{x},{y2}" stroke="{colour}" stroke-width="1.8" '
        f'fill="none" marker-end="url(#a)"/>'
    )


def tee(x_from, y_from, x_to, y_to, colour, label=""):
    """Down, across, then down again -- three straight segments, no diagonal."""
    mid = y_from + (y_to - y_from) / 2
    parts.append(
        f'<path d="M{x_from},{y_from} L{x_from},{mid} L{x_to},{mid} L{x_to},{y_to}" '
        f'stroke="{colour}" stroke-width="1.8" fill="none" marker-end="url(#a)"/>'
    )
    if label:
        parts.append(
            f'<text x="{(x_from + x_to) / 2}" y="{mid - 9}" text-anchor="middle" '
            f'font-family="{FONT}" font-size="12" fill="{MUTED}">{label}</text>'
        )


def text(x, y, s, size=12, colour=MUTED, weight="400", family=None):
    parts.append(
        f'<text x="{x}" y="{y}" text-anchor="middle" font-family="{family or FONT}" '
        f'font-size="{size}" font-weight="{weight}" fill="{colour}">{s}</text>'
    )


# --- header ------------------------------------------------------------------
text(CX, 40, "Agentic Governance for Data Pipelines", 24, INK, "600")
text(CX, 64, "One policy library, enforced twice: before the code exists, and after it lands", 14)

# --- the single source -------------------------------------------------------
box(CX - 175, 92, 350, 60, "policies/policies.yaml",
    "14 policies · severity · applies_to globs|the only place a rule is written",
    SOURCE, mono=True)

# One source compiles two ways. Orthogonal so the split reads as a fork.
tee(CX, 152, LX, 202, SOURCE)
tee(CX, 152, RX, 202, SOURCE)

box(LX - BOX_W / 2, 202, BOX_W, 54, "rules.md",
    "what the AI reads while writing code", SOURCE, mono=True)
box(RX - BOX_W / 2, 202, BOX_W, 54, "chroma_db",
    "what the auditor retrieves while checking code", SOURCE, mono=True)

# --- lane divider and headers ------------------------------------------------
parts.append(f'<line x1="{CX}" y1="286" x2="{CX}" y2="660" stroke="{RULE}" '
             f'stroke-width="1" stroke-dasharray="3 7"/>')
text(LX, 300, "BUILD TIME  ·  PREVENT", 14, BUILD, "700")
text(LX, 320, "governance is an input to code generation", 12)
text(RX, 300, "RUN TIME  ·  DETECT", 14, RUN, "700")
text(RX, 320, "governance is a check on code that exists", 12)

# --- build lane --------------------------------------------------------------
box(LX - BOX_W / 2, 344, BOX_W, 64, "GitHub Spec Kit",
    "spec.md · plan.md · tasks.md · data-model.md|the engineer writes intent, not code", BUILD)
down(LX, 408, 440, BUILD)
box(LX - BOX_W / 2, 440, BOX_W, 60, "Copilot generates the pipeline",
    "reads the spec and rules.md together", BUILD)
down(LX, 500, 532, BUILD)
box(LX - BOX_W / 2, 532, BOX_W, 60, "Pipeline repository",
    "medallion layers · pandera checks · env-var secrets", BUILD)
text(LX, 620, "Compliant by construction — not by correction", 13, BUILD, "600")

# --- run lane ----------------------------------------------------------------
box(RX - BOX_W / 2, 344, BOX_W, 54, "Repository Agent",
    "walks the repo · no model call", RUN)
down(RX, 398, 424, RUN)
box(RX - BOX_W / 2, 424, BOX_W, 92, "Auditor Agent",
    "deterministic in code: repo name, file names, pinning|"
    "model + RAG: everything needing judgement|"
    "k samples → majority vote · evidence quoted verbatim", RUN)
down(RX, 516, 542, RUN)
box(RX - BOX_W / 2, 542, BOX_W, 54, "Remediation Agent",
    "writes a fix, or hands it to a person", RUN)
down(RX, 596, 622, RUN)
box(RX - BOX_W / 2, 622, BOX_W, 44, "Compliance report", "", MUTED)

# The bridge: what build time produces is what run time inspects. Routed below
# the build lane's last box and straight up into the run lane's first.
parts.append(
    f'<path d="M{LX},592 L{LX},684 L{RX},684 L{RX},666" stroke="{MUTED}" '
    f'stroke-width="1.8" fill="none" stroke-dasharray="6 4"/>'
)
text(CX, 700, "every repository the build half produces is a repository the run half audits", 12)

# --- legend ------------------------------------------------------------------
text(CX, 268, "blue = policy source        green = build time        red = run time", 12)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/>
  </marker>
</defs>
<rect width="{W}" height="{H}" fill="#ffffff"/>
{chr(10).join(parts)}
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print(f"{OUT} written ({OUT.stat().st_size / 1024:.0f} KB)")
