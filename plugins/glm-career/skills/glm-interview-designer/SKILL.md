---
name: glm-interview-designer
metadata:
  author: Z.AI
  version: "1.0.0"
description: >
  Design evidence-based structured interviews from the interviewer side:
  define the A-player Scorecard before reading any resume, run a forensic
  scan for Red Flags and Green Signals (Too Good To Be True, Passenger vs
  Driver, First Principles heuristics), then design pressure-test and
  future-simulation questions that cannot be memorized. Outputs a targeted
  interview guide from the bundled template. Combines Geoff Smart's
  Topgrading, Lou Adler's performance-based hiring and Daniel Kahneman's
  bias control. Use when designing interview questions for a role, building
  a structured interview guide, or assessing candidates as the hiring side:
  设计面试题, 结构化面试, 面试指南, 出一套面试题, 招聘评估, 候选人评估,
  面试官视角, 压力测试题, scorecard, red flags, green signals, future
  simulation, interview guide. Pure documentation skill: no scripts, no
  network, no SDK - the guide template fills in directly; resume input via
  paste / pdftotext / python-docx local equivalents.
license: MIT. LICENSE.txt has complete terms
---

# Interview Designer Skill

> **Core Mission**: Elevate interview planning from "glancing at resume and asking questions" to "evidence-based investigation and projection."
> **Operating Mechanism**: Define Scorecard (set standards) → Forensic Scan (evidence gathering) → Future Simulation (performance prediction).
> **Prompt Strategy**: This skill uses \<Chain of Thought\>. When executing, maintain an "Objective Evaluator" perspective, seeking both Red Flags and Green Signals.

## Codex Deployment Notes

This skill ships as a Codex plugin. Path conventions:

- Plugin install root: `~/.codex/plugins/glm-career/`
- Skill directory: `~/.codex/plugins/glm-career/skills/glm-interview-designer/`
- `references/`, `templates/` below refer to subdirectories of that skill directory.
- **Host-form equivalents**:
  - Host pdf / docx skill resume parsing → local equivalents (pick one):
    user pastes resume text (preferred); `pdftotext resume.pdf -` (poppler)
    for text; .docx via python-docx one-liner (`uv run --with python-docx`).
    If none available, ask the user to paste the resume.
  - Host chat-artifact rendering → the guide is a plain markdown file
    written to the **user working directory** (Codex startup cwd); the
    plugin directory is read-only.
- **References on demand**: `references/design_rationale.md` (simulated
  expert critique panel) and `references/upstream-README.md` (upstream
  project background / version / license) open only when needed - keep
  small local model contexts lean.
- Dependency discipline: pure documentation skill - no scripts, no
  network, no SDK, no API key.

## 1. Dynamic War Room (Expert Panel)

Dynamically summon the most matching **best minds** into the war room based on **candidate's role attributes**:

*   **Geoff Smart (Who)**: Responsible for **Define & Verify**.
    *   *Principle*: Scorecard First. Before looking at any resume, clarify what the standard for an "A Player" is.
*   **Lou Adler (Performance-based)**: Responsible for **Predict**.
    *   *Principle*: Past performance predicts future performance *only if* the context is similar. Must design simulations for future scenarios.
*   **Daniel Kahneman (Bias Control)**: Responsible for **De-bias**.
    *   *Principle*: Beware of "confirmation bias." If concerns are found, also seek counter-evidence; if highlights are found, verify their replicability.
*   **Domain Expert**: Responsible for **Depth**.

## 2. Core Execution Workflow

### Step 1: Scorecard Definition - *Smart's Priority*
**Don't look at the resume first!** Based on JD or role requirements, define A Player standards for this position:
*   **Mission**: One sentence - why does this role exist?
*   **Outcomes**: 3-5 specific, measurable results that must be achieved within 12 months.
*   **Competencies**: Hard/soft skills required to achieve the above outcomes.

### Step 2: Forensic Resume Scan - *Smart's Forensic*
Use Step 1 standards to scan the resume, looking for **Gaps (discrepancies)** and **High Points (highlights)**:
*   **The "Too Good To Be True" Heuristic**: Logical gaps behind perfect data.
*   **The "Passenger vs Driver" Heuristic**: Individual's true contributions under big company halo.
*   **The "First Principles" Heuristic**: Principle understanding behind technical jargon.

### Step 3: Pressure Test & Future Simulation - *Adler's Prediction*
Design two types of questions:
1.  **Pressure Test Scripts (for past)**: Design Forensic STAR follow-ups targeting Step 2 concerns (originally "torpedo questions," but more objective).
2.  **Future Simulation (for future)**: Design a specific Performance Problem.
    *   *Example*: "We're entering this new market next year, and the biggest obstacle is X. If you join, how would you analyze this problem in your first week?"

## 3. Question Design Principles

1.  **Cannot Be Memorized**: Forces candidates to think on the spot (Simulation) or recall painful memories (Pressure Test).
2.  **Forced Trade-offs**: Choose between two "correct" options to test values.
3.  **Detail Granularity**: Must be able to probe down to "what diagram did you draw" or "what exact words did you say."

## 4. Output Format

Generate the report directly from the bundled template:
`~/.codex/plugins/glm-career/skills/glm-interview-designer/templates/interview_guide_template.md`.
**Note**: When generating the guide, include both **[Red Flags] (concerns)** and **[Green Signals] (highlight verification)** to maintain objectivity in assessment.

---

## Routing (与其他 skill 的协作)

This skill stays on the **interviewer / hiring side**: designing questions,
scorecards and guides to assess a candidate.

- Candidate preparing for an interview → glm-interview-prep plugin (same
  batch; if absent, follow its source-skill logic manually).
- Candidate tailoring a resume to a JD → glm-jd-resume-tailor /
  glm-resume-builder plugins (already delivered).
- Job-direction profiling and application tracking → glm-job-intent-tracker
  plugin (already delivered).
