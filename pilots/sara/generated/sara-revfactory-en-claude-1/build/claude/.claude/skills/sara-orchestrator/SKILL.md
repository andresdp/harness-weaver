---
name: sara-orchestrator
description: "Runs the SARA four-stage architecture-design process (requirements & drivers → solution design → alternative evaluation → architecture decision) on a supplied project description and functional requirements, and produces a traceable architecture_decision.json with an ADR, a Mermaid component diagram, and a register of assumptions and unresolved gaps. Use when the user asks to design/derive/recommend a software architecture, evaluate architecture alternatives, or produce an ADR and architecture diagram from requirements. Also use for follow-ups: re-run, run again, update, fix, supplement, redo only stage N / only the ADR / only the diagram, re-evaluate the alternatives, based on the previous results, improve the results. Not for reviewing an existing ADR text alone or for drawing arbitrary diagrams."
---

# SARA Architecture-Design Orchestrator

## Execution mode: Workflow coordination (fallback: sequential sub-agent delegation)

SARA fixes the order of stages and tasks, the artifact handoffs, and the completion checks in advance, so control
flow belongs in code rather than in moment-to-moment judgment. Loading this skill counts as consent to call the
`Workflow` tool. The default run uses 10 agent calls (4 stages + 4 reviews + package + package review), plus at
most one repair and re-review per stage. If the `Workflow` tool is not available in the session, run the same
steps with the `Agent` tool as described in "Fallback" — the prompts, order, and gates are identical.

## Agent composition

| Step | `agentType` | Skills | Writes (`_workspace/artifacts/`) | Returns (`schema`) |
|------|-------------|--------|----------------------------------|--------------------|
| Stage 1 | `sara-requirements-analyst` | requirements-cross-analysis, quality-attribute-identification, driver-identification, assumptions-gap-register | requirements_analysis.json, quality_attributes.json, drivers.json, stage1_assumptions_gaps.json | `STAGE_STATUS` |
| Stage 2 | `sara-solution-designer` | pattern-candidate-identification, patterns-compatibility, alternative-generation, assumptions-gap-register | pattern_candidates.json, pattern_compatibility.json, alternatives.json, stage2_assumptions_gaps.json | `STAGE_STATUS` |
| Stage 3 | `sara-alternative-evaluator` | alternative-evaluation, trade-off-analysis, alternative-selection, assumptions-gap-register | alternative_evaluation.json, trade_off_analysis.json, alternative_selection.json, stage3_assumptions_gaps.json | `STAGE_STATUS` |
| Stage 4 | `sara-decision-documenter` | adr-generation, architecture-diagram, assumptions-gap-register | adr.md, architecture_diagram.mmd, stage4_assumptions_gaps.json | `STAGE_STATUS` |
| Review (after each stage, and package) | `sara-contract-reviewer` | sara-artifact-review | nothing (read-only) | `REVIEW` |
| Package | `sara-decision-packager` | architecture-decision-packaging | `output/architecture_decision.json`, `output/adr.md`, `output/architecture_diagram.mmd`, `output/assumptions_and_gaps.json` | `DECISION` (the output contract) |

Models are set in each agent's frontmatter (opus for Stages 1–3, sonnet for Stage 4, review, and packaging).

## Work procedure

### Step 0: Check existing work

1. If `_workspace/` does not exist → fresh run from Step 1.
2. If `_workspace/` exists and the user supplied **new** inputs → move it to `_workspace_{YYYYMMDD-HHMMSS}/`
   (timestamp from `date +%Y%m%d-%H%M%S`) and also move `output/` the same way, then fresh run.
3. If `_workspace/` exists and the user asks to fix or redo part of the run → partial re-run:
   - Map the request to the earliest affected stage: requirements/quality attributes/drivers → 1;
     patterns/compatibility/alternatives → 2; evaluation/trade-offs/selection → 3; ADR/diagram → 4;
     packaging only → 5.
   - Pass `startStage` = that number and `feedback` = the user's request. Stages before `startStage` are reused;
     that stage and **every later stage** re-run, because each stage reads its predecessors' artifacts.
   - If `_workspace/run_meta.json` has a `runId` and nothing upstream changed, prefer
     `resumeFromRunId` with the same script — unchanged `agent()` calls return cached results.
4. Record `runId`, start time, `startStage`, input file names and the outcome in `_workspace/run_meta.json`.

### Step 1: Intake (main agent, before the workflow)

1. Obtain the two input ports. They may arrive as pasted text, file paths, or one document containing both.
   - `project_description` → write verbatim to `_workspace/00_input/project_description.md`
   - `functional_requirements` → write verbatim to `_workspace/00_input/functional_requirements.md`
2. If either is missing, ask the user for it before starting. Do not synthesize requirements. This is input
   intake, not a mid-run review gate; once the workflow starts there is no human gate until the end.
3. If one document contains both, split it only at an explicit boundary (a heading or label). If no clear boundary
   exists, ask the user rather than guessing.
4. Do not read or depend on any case-specific material other than what the user supplied.

### Step 2: Run the workflow

Call `Workflow` with the script below and `args`:
`{ "workspace": "_workspace", "outputDir": "output", "startStage": 1, "feedback": "" }`.
Wait for the completion notification; do not presume results.

```javascript
export const meta = {
  name: 'sara-architecture-run',
  description: 'Runs the four SARA stages in order with a contract review after each, then packages the architecture decision',
  phases: [
    { title: 'stage1-requirements-drivers', detail: 'requirements cross-analysis, quality attributes, drivers' },
    { title: 'stage2-solution-design', detail: 'pattern candidates, compatibility, alternatives' },
    { title: 'stage3-alternative-evaluation', detail: 'evaluation, trade-offs, selection' },
    { title: 'stage4-architecture-decision', detail: 'ADR and Mermaid component diagram' },
    { title: 'package', detail: 'architecture_decision.json and sidecars, final contract review' },
  ],
}

const W = args.workspace || '_workspace'
const OUT = args.outputDir || 'output'
const START = args.startStage || 1
const FEEDBACK = args.feedback || ''
const ART = `${W}/artifacts`

const STAGE_STATUS = { type: 'object', required: ['stage', 'artifacts', 'self_verified', 'gap_entries', 'notes'],
  properties: {
    stage: { type: 'integer' },
    artifacts: { type: 'array', items: { type: 'object', required: ['path', 'exists', 'valid'],
      properties: { path: { type: 'string' }, exists: { type: 'boolean' }, valid: { type: 'boolean' } } } },
    self_verified: { type: 'boolean' },
    gap_entries: { type: 'integer' },
    notes: { type: 'string' } } }

const REVIEW = { type: 'object', required: ['stage', 'verdict', 'blocking', 'findings'],
  properties: {
    stage: { type: 'integer' },
    verdict: { type: 'string', enum: ['pass', 'pass_with_findings', 'fail'] },
    blocking: { type: 'array', items: { type: 'string' } },
    findings: { type: 'array', items: { type: 'object', required: ['severity', 'artifact', 'issue'],
      properties: { severity: { type: 'string', enum: ['blocking', 'major', 'minor'] },
        artifact: { type: 'string' }, issue: { type: 'string' }, evidence: { type: 'string' } } } } } }

// Same shape as references/architecture-decision.schema.json (the required output contract).
const DECISION = { type: 'object', additionalProperties: false,
  required: ['selected_alternative_id', 'selection_rationale', 'adr_markdown', 'architecture_diagram_mermaid'],
  properties: {
    selected_alternative_id: { type: 'string', minLength: 1 },
    selection_rationale: { type: 'string', minLength: 1 },
    adr_markdown: { type: 'string', minLength: 80, pattern: '^# ADR:' },
    architecture_diagram_mermaid: { type: 'string', minLength: 20,
      pattern: '^(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|erDiagram|C4Context|C4Container|C4Component|C4Dynamic)' } } }

const STAGES = [
  { n: 1, phase: 'stage1-requirements-drivers', agentType: 'sara-requirements-analyst', title: 'Requirements & Drivers' },
  { n: 2, phase: 'stage2-solution-design', agentType: 'sara-solution-designer', title: 'Solution Design' },
  { n: 3, phase: 'stage3-alternative-evaluation', agentType: 'sara-alternative-evaluator', title: 'Alternative Evaluation' },
  { n: 4, phase: 'stage4-architecture-decision', agentType: 'sara-decision-documenter', title: 'Architecture Decision & Modeling' },
]

const stagePrompt = s => [
  `Run SARA Stage ${s.n} (${s.title}) as defined in your agent definition.`,
  `Workspace root: ${W}. Inputs: ${W}/00_input/. Artifacts directory: ${ART}/.`,
  `Execute your ordered tasks one at a time; before each task Read its .claude/skills/<task>/SKILL.md.`,
  `Write each artifact, read it back, verify it, then continue. Finish with the stage gap register.`,
  s.n === START && FEEDBACK ? `This is a re-run requested by the user. Their feedback: ${FEEDBACK}. Existing artifacts of this stage may be revised in place.` : '',
  `Return the status object for stage ${s.n}.`,
].filter(Boolean).join('\n')

const reviewPrompt = s => `Review SARA stage ${s} artifacts in ${ART}/ (inputs in ${W}/00_input/) using the sara-artifact-review checklist for stage ${s}. Return the review object with stage=${s}.`

const repairPrompt = (s, review) => [
  `The contract reviewer failed your Stage ${s.n} artifacts in ${ART}/. Findings:`,
  JSON.stringify(review),
  `Fix only what the findings name. Re-run from the earliest affected task through the end of the stage (including the gap register), editing in place. Return the status object for stage ${s.n}.`,
].join('\n')

const reviewStage = async (n, phaseTitle, label) => {
  let r = await agent(reviewPrompt(n), { agentType: 'sara-contract-reviewer', phase: phaseTitle, label, schema: REVIEW })
  if (!r) r = await agent(reviewPrompt(n), { agentType: 'sara-contract-reviewer', phase: phaseTitle, label: `${label}-retry`, schema: REVIEW })
  return r
}

const reviews = []
const carried = []
for (const s of STAGES) {
  if (s.n < START) { log(`Stage ${s.n} reused from previous run (startStage=${START}).`); continue }
  phase(s.phase)
  let status = await agent(stagePrompt(s), { agentType: s.agentType, phase: s.phase, label: `stage${s.n}`, schema: STAGE_STATUS })
  if (!status) status = await agent(stagePrompt(s), { agentType: s.agentType, phase: s.phase, label: `stage${s.n}-retry`, schema: STAGE_STATUS })
  if (!status) return { ok: false, error: `Stage ${s.n} agent failed twice; no status returned.`, failedStage: s.n, reviews }

  let review = await reviewStage(s.n, s.phase, `review${s.n}`)
  if (review && review.verdict === 'fail') {
    log(`Stage ${s.n} review failed (${review.blocking.length} blocking). Sending back once for repair.`)
    const repaired = await agent(repairPrompt(s, review), { agentType: s.agentType, phase: s.phase, label: `stage${s.n}-repair`, schema: STAGE_STATUS })
    if (repaired) review = await reviewStage(s.n, s.phase, `review${s.n}-after-repair`)
  }
  if (!review) {
    log(`Stage ${s.n} could not be reviewed; continuing on the stage's self-verification only.`)
    reviews.push({ stage: s.n, verdict: 'not_reviewed', blocking: [], findings: [] })
    carried.push({ stage: s.n, severity: 'major', artifact: `stage ${s.n}`, issue: 'Contract review unavailable; stage relied on self-verification only.' })
    continue
  }
  reviews.push(review)
  if (review.verdict === 'fail') {
    return { ok: false, error: `Stage ${s.n} still fails review after one repair; later stages were not run.`, failedStage: s.n, reviews }
  }
  review.findings.filter(f => f.severity !== 'blocking').forEach(f => carried.push({ stage: s.n, ...f }))
}

phase('package')
const packagePrompt = [
  `Package the SARA run. Artifacts: ${ART}/. Output directory: ${OUT}/.`,
  `Follow .claude/skills/architecture-decision-packaging/SKILL.md exactly.`,
  `Non-blocking review findings to carry into assumptions_and_gaps.json (review_findings_carried):`,
  JSON.stringify(carried),
  `Return the exact object written to ${OUT}/architecture_decision.json.`,
].join('\n')
let decision = await agent(packagePrompt, { agentType: 'sara-decision-packager', phase: 'package', label: 'package', schema: DECISION })
if (!decision) decision = await agent(packagePrompt, { agentType: 'sara-decision-packager', phase: 'package', label: 'package-retry', schema: DECISION })
if (!decision) return { ok: false, error: 'Packaging failed twice; architecture_decision.json may be missing or non-conforming.', reviews, carried }

const finalReview = await reviewStage(5, 'package', 'review-package')
if (!finalReview) log('Package review unavailable; report it as unverified.')
return {
  ok: !finalReview || finalReview.verdict !== 'fail',
  selected_alternative_id: decision.selected_alternative_id,
  outputs: [`${OUT}/architecture_decision.json`, `${OUT}/adr.md`, `${OUT}/architecture_diagram.mmd`, `${OUT}/assumptions_and_gaps.json`],
  reviews, finalReview, carried,
}
```

### Step 3: Report (main agent)

1. Read `output/architecture_decision.json` yourself and confirm it has exactly the four contract keys, and that
   `selected_alternative_id` matches `_workspace/artifacts/alternative_selection.json`.
2. Save the returned `reviews`, `finalReview` and `carried` to `_workspace/review_findings.json`; update
   `_workspace/run_meta.json` with the outcome.
3. Tell the user: the selected alternative and one-sentence rationale; the output file paths; the count of open
   assumptions/gaps (`status: open` or `relied_upon`) with the top few; any `pass_with_findings`, `not_reviewed`
   or failed stage. If the run stopped early, say which stage and why, and list which artifacts exist.
4. Keep `_workspace/` for traceability. Do not delete intermediate artifacts.

## Fallback: sequential sub-agent delegation (no `Workflow` tool)

Run the same sequence with the `Agent` tool, one call at a time and in the foreground (`run_in_background: false`),
because every step depends on the previous one:

1. For each stage from `startStage` to 4: `Agent(subagent_type: <stage agentType>, prompt: <stagePrompt text>)`;
   then `Agent(subagent_type: "sara-contract-reviewer", prompt: <reviewPrompt text>)`. On `fail`, send one repair
   prompt to a new call of the same stage agent, re-review, and stop if it still fails.
2. Write the non-blocking findings to `_workspace/review_findings.json`, then call `sara-decision-packager`, then the
   package review (stage 5).
3. Report as in Step 3. Note in `run_meta.json` that the fallback was used (no schema-checked return values).

## Error handling

| Situation | Response |
|-----------|----------|
| A stage agent returns `null` | Retry once (built into the script). A second failure stops the run: later stages need its artifacts. |
| Review `fail` | One repair by the owning stage agent, then re-review. Still failing → stop, report blocking findings, keep artifacts. |
| Review unavailable | Continue on the stage's own read-back verification, mark the stage `not_reviewed`, carry it as a finding. |
| Packaging `null` or schema mismatch | Retry once; then report that the final contract was not met and point to the Stage 4 artifacts. |
| Usage limit, expired auth, denied permission | Do not retry or resume. Inspect `_workspace/artifacts/` to see how far the run got, write `_workspace/run_meta.json` with the stop point, tell the user (and when a usage limit resets). Resume later with `resumeFromRunId`. |
| Empty or suspicious results | Check the workflow journal and the files themselves before calling the run successful. |
| Conflicting content between stages | Do not delete either side; it stays in the artifacts and is reported as a finding. |
| Main agent filling a gap | Record only facts you checked directly; never author stage judgments (selection, evaluations, ADR text) yourself. |

## Test scenarios

### Normal flow
1. The user pastes a project description and a list of functional requirements with IDs.
2. Intake writes both files; the workflow runs stages 1–4, each review returns `pass` or `pass_with_findings`.
3. Expected: `output/architecture_decision.json` with exactly four keys (ADR string starts `# ADR:`, diagram string
   starts `flowchart`), `output/adr.md`, `output/architecture_diagram.mmd`, `output/assumptions_and_gaps.json`;
   the reported selected alternative equals `alternative_selection.json`.

### Partial re-run
1. After a run, the user says "redo only the diagram, show the external payment system".
2. Step 0 maps this to stage 4, `startStage: 4`, `feedback` set. Stages 1–3 are reused; Stage 4, the package and its
   review re-run. The ADR may stay unchanged; the diagram changes; `selected_alternative_id` is unchanged.

### Error flow
1. The Stage 2 review fails because `addressed_drivers` contains a name absent from `drivers.json`.
2. The solution designer receives the findings, fixes `alternatives.json` and the gap register; the re-review passes.
3. If it still failed, the run would stop after Stage 2 with `ok: false`, and the report would list the blocking
   findings and the existing Stage 1–2 artifacts.

### Missing input
1. The user gives only a project description.
2. Intake asks for the functional requirements and does not start the workflow until they are supplied.
