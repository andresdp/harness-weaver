---
name: harness
description: "Designs and generates task-specific agent harnesses from intent, domain knowledge, and methodology, then materializes them for a selected runtime: a Claude Code project and/or a DeepAgents stage pipeline. Asks the user the necessary questions, including which target runtime to generate. Use when the user asks to build, set up, design, generate, extend, audit, or maintain a harness or agent team; to generate or port a harness to DeepAgents or Claude Code; to harvest a harness design from an existing agent application; or to regenerate a target from an updated HarnessSpec. For retrospectives and applying execution feedback to an existing harness, use the evolve skill."
---

# Harness — design once, materialize per runtime

This skill takes the user from sources to a runnable harness in four moves: **intake → design (HarnessSpec) → target selection → materialization**. The design is runtime-neutral. Each runtime target has its own reference under `references/targets/`, which is read only when that target is selected.

Agents describe *who* does the work; skills describe *how* it is done. Methodology state describes *what meaningful progress has been made*, and runtime bookkeeping never substitutes for it.

## Core principles

1. **Ask before writing files.** Deriving a harness is a design task, not transcription. Run the question gates in `references/question-gates.md`; resolve what the evidence answers and ask the rest.
2. **Separate the layers.** Intent, methodology and domain knowledge go into the design. Runtime constraints arrive only at gates G4/G5. Never put a runtime's paths, tools or syntax into the shared spec, and never put case data or reference outputs into anything generated.
3. **Keep the design proportionate.** Use a saved HarnessSpec for reusable, multi-stage, multi-runtime or evaluated work. A simple one-off may proceed from a recorded brief; state that choice and its trade-off.
4. **Materialize only what the target supports.** Every target writes a materialization report listing each spec element as mapped, approximated or unsupported. Do not claim two targets behave equivalently unless both implement the same declared behavior.
5. **Make progress meaningful.** The design states the domain method, required evidence, semantic progress and completion criteria. Agent messages, retries and task flags do not prove domain progress.
6. **Write in the user's language.** Generated agents, skills and notes follow the language of the conversation, an explicitly requested language, or that of the existing harness files.
7. **Feed results back.** Execution results and feedback are handled by the `evolve` skill; this skill handles building, extending and regenerating.

## Harness IR content

The HarnessSpec (or a recorded brief) must contain these semantic parts:

- **Intent and methodology:** goal, scope, exclusions; the domain method with versioned sources and labeled adaptations.
- **Activities and readiness:** stages, responsible roles, inputs (as named input ports or artifact ids, never case file paths), outputs, and evidence-based readiness.
- **Artifacts and validation:** artifact contracts (JSON Schema where structured) and checks for structure, content, provenance and evidence links, with a stated checker for each (producer, verifier, deterministic code, or human).
- **Semantic progress and completion:** domain states or checkpoints, evidence per assessment, open gaps, next-state requirements, completion criteria.
- **Evidence and uncertainty:** references for claims; observed facts, assumptions, unknowns, conflicts and accepted gaps kept distinct.
- **Human gates:** where a qualified person must review before consequential use.

Validation checks the design and contracts. Verification checks whether a produced artifact meets a stated requirement. Evaluation judges quality against declared criteria. Keep their questions and results distinguishable.

## Procedure

### Phase 0: State check and intake (gate G0)

1. If `harness-answers.yaml` exists in the working directory, read it (format in `references/question-gates.md`).
2. Inspect what already exists: a HarnessSpec and `design-notes.md`; a `sources/` directory; a Claude Code project (`.claude/agents/`, `.claude/skills/`, `CLAUDE.md`); DeepAgents stage directories with `wiring.yaml` or a `port-manifest.md`.
3. Choose the procedure:
   - **Fresh build:** no spec or harness exists → all phases.
   - **Harvest:** the user wants to start from an existing harness or application → follow `references/intake-and-harvest.md`, stop for review of the draft sources, then continue at Phase 1.
   - **Regenerate:** a validated spec exists and only targets are needed → Phases 3–5.
   - **Extend:** add or change roles, stages or skills → the phases the change touches. Re-run the affected targets.
   - **Operate/maintain:** inspect, fix or sync an existing harness → Phase 6.
4. If existing Claude orchestrators contain `TeamCreate`, `TeamDelete` or `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, they are v1 artifacts. Propose migrating them (`references/execution-modes.md`, "Migrating from v1 to v2").
5. Run gate G0 (authoritative sources, starting point, saved spec or brief, output location). Report the findings and the plan, then get confirmation.

### Phase 1: Analyze the domain and the work (gate G1)

1. Resolve the four design inputs (intent, methodology, domain knowledge, runtime constraints) as described in `references/intake-and-harvest.md`.
   - If the user is authoring or revising a methodology source, use `references/methodology-authoring-guide.md` to clarify the expected content and distinguish universal needs from conditional sections.
2. Break the work into its kinds (generation, verification, editing, analysis) and examine the workflow:
   - Can the items be enumerated in advance?
   - Is an iterate-verify-fix loop needed?
   - Must specialists exchange opinions or keep conversational context?
3. Identify the tech stack, data models and existing agents or skills that overlap.
4. Match explanations to the user's vocabulary.
5. Run gate G1 for the ambiguities that remain.

### Phase 2: Design the HarnessSpec (gates G2, G3)

#### 2-1. Stages, roles and coordination

1. Divide the work by specialty and by stable artifact sets; each set is a candidate stage.
2. Choose the coordination pattern that fits (criteria in `references/team-patterns.md`):
   - **Pipeline**: each stage consumes the previous stage's output.
   - **Fan-out/Fan-in**: independent tasks in parallel, then merged.
   - **Expert Pool**: only the specialists matching the input are invoked.
   - **Producer-Reviewer**: one produces, another reviews.
   - **Supervisor**: a central role tracks progress and reassigns work.
   - **Hierarchical Delegation**: at most two levels.
3. If accuracy is critical, add verification schemes: adversarial verification (majority `confirmed` with evidence), judge panel, loop-until-dry, multi-criteria sweep, completeness critic.
4. Split roles by required expertise, parallelism, retained context and reuse (`references/team-patterns.md`, "Agent separation criteria").
5. If DeepAgents is a likely target, apply the design-time advice in `references/targets/deepagents.md`.
6. Run gate G2 with 2–3 viable designs and a recommendation.

#### 2-2. Artifacts, semantic state and checks

1. Define each artifact: id, direction, description, and `schema_ref` for structured artifacts (reuse supplied JSON Schemas).
2. Define the semantic state profile, completion criteria, verification entries and human gates from the methodology.
3. Run gate G3 on the artifact table before any skill is written.

#### 2-3. Write and validate

1. Write the HarnessSpec using the repository's canonical schema (`specs/harnessspec/`). Reference long guidance instead of copying it, and preserve source authority and revisions.
2. Validate it with `hw validate <spec>` (in the HarnessWeaver repository: `conda run -n harness hw validate <spec>`). If no validator is available, say that validation was not run.
3. Write `design-notes.md` next to the spec: the gate answers table, the designs considered and why one was chosen, assumptions and open questions.
4. A valid spec does not prove the harness works. Keep validation results separate from task-quality results.

### Phase 3: Select targets (gates G4, G5)

1. Run gate G4: **Claude Code, DeepAgents, or both?** Also settle the output directory per target (default `build/<target>/` next to the spec).
2. Run gate G5 for each selected target (Claude Code: execution modes and models; DeepAgents: model, host, human-in-the-loop, subagents).
3. Check the spec's `runtime_requirements` against each target (`hw validate <spec> --capability <c>`) and report gaps before materializing.

### Phase 4: Materialize each target (gate G6)

For each selected target, read its reference and follow it:

| Target | Reference | Emits |
|---|---|---|
| Claude Code | `references/targets/claude-code.md` | `.claude/agents/`, `.claude/skills/` (domain skills + orchestrator), `CLAUDE.md` pointer |
| DeepAgents | `references/targets/deepagents.md` | `stage{N}-{name}/AGENTS.md` + `skills/`, `wiring.yaml`, `port-manifest.md` for an existing host app |

Before writing, run gate G6 with the file list and the known approximated or unsupported mappings. After writing, produce `materialization-report.md` in each output directory (`references/materialization-report.md`).

When both targets are selected, materialize them from the **same** spec revision, and copy domain skills from the same source paths. Differences between the targets must come from the mapping, never from a divergent design.

### Phase 5: Validate and report

1. Run each target's checklist. Where available, run `hw check-bundle <output-dir> --target <claude|deepagents> --spec <spec>` (in the HarnessWeaver environment: `conda run -n harness hw check-bundle ...`); it also confirms the materialization report accounts for every spec element. Fix what it reports before handing off. For Claude Code, also run `claude plugin validate` if the output is packaged as a plugin.
2. Run skill and trigger tests as the target reference describes, when the user asks for them or the environment allows.
3. Report to the user: spec path and version, targets generated, output directories, the counts of mapped, approximated and unsupported elements, manual setup required, what was not verified, and a suggested smoke test per target.

### Phase 6: Operate and maintain

1. **State check:** compare the spec, the design notes and each target's files; list mismatches.
2. **Incremental changes:** change one item at a time; regenerate the affected targets and re-run Phase 5.
3. **Record changes:** add the date, change, target and reason to the change history (`CLAUDE.md` for Claude Code; the output `README.md` for DeepAgents) and to `design-notes.md`.
4. Propose `evolve` when the same feedback recurs, agents fail for the same root cause, or the user bypasses the harness.

## Artifact checklist

- [ ] Gates G0–G6 ran (or were answered from `harness-answers.yaml`); every answer and its source is in `design-notes.md`.
- [ ] A HarnessSpec exists for reusable or complex work and passes `hw validate`, or the handoff says validation was unavailable; a deliberate one-off has a stated reason.
- [ ] The spec contains no runtime syntax, case facts or reference outputs; stage inputs are ports or artifact ids.
- [ ] Every selected target was materialized from the same spec revision and has a `materialization-report.md` covering every spec element.
- [ ] Domain skills were copied from their source paths; adaptations are listed in the report.
- [ ] Each target's own checklist passes (`references/targets/<target>.md`).
- [ ] Semantic progress is produced only from evidence, never from runtime completion.

## Reference documents

- **Question gates and answers file:** `references/question-gates.md`
- **Intake and harvest:** `references/intake-and-harvest.md`
- **Materialization report template:** `references/materialization-report.md`
- **Claude Code target:** `references/targets/claude-code.md` (with `execution-modes.md`, `orchestrator-template.md`, `workflow-recipes.md`, `model-selection-guide.md`, `qa-agent-guide.md`)
- **DeepAgents target:** `references/targets/deepagents.md` (with `targets/deepagents-target-pattern.md`, `targets/deepagents-mapping-table.md`)
- **Shared design guidance:** `references/team-patterns.md`, `references/team-examples.md`, `references/skill-writing-guide.md`, `references/skill-testing-guide.md`
