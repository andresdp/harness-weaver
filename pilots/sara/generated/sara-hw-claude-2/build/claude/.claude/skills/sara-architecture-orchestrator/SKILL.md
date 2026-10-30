---
name: sara-architecture-orchestrator
description: "Runs the SARA four-stage architecture design workflow: from a project description and functional requirements to one evidence-backed architecture recommendation documented as an ADR and a high-level Mermaid component diagram (requirements & drivers -> solution design -> alternative evaluation -> architecture decision). MUST be used when the user asks to design or recommend a software architecture for a described system, derive architectural drivers or alternatives from requirements, or produce an ADR plus component diagram from requirements. Also use for follow-ups: re-run, run again, redo only stage N / only the ADR or diagram, update or revise the previous results, fix a failed stage, continue an interrupted run. Do not use for a quick conceptual question about a single pattern, for reviewing an existing ADR without requirements, or for writing code."
---

# SARA Architecture Design Orchestrator

Coordinates the four SARA stages as a strict serial pipeline. Each stage is one specialist agent that runs its three (Stage 4: two) tasks in a pinned order. Artifacts in `_workspace/artifacts/` are the only communication channel between tasks and stages.

The result is a **draft recommendation** until a software architect reviews it after the run.

## Execution mode: Sub-agent delegation (serial)

One `Agent` call per stage, one at a time, in the foreground (`run_in_background: false`), because every stage depends on the previous stage's artifacts. There is no parallelism and no agent-to-agent messaging. Between stages, the orchestrator itself runs a deterministic schema gate (`scripts/validate_stage.py`); a stage starts only when the gate for all its inputs passes.

| Stage | Stage id | `subagent_type` | Writes (in `_workspace/artifacts/`) |
|---|---|---|---|
| 1 | `requirements_drivers` | `requirements-drivers-analyst` | `requirements_analysis.json`, `quality_attributes.json`, `drivers.json` |
| 2 | `solution_design` | `solution-designer` | `pattern_candidates.json`, `pattern_compatibility.json`, `alternatives.json` |
| 3 | `alternative_evaluation` | `alternative-evaluator` | `alternative_evaluation.json`, `trade_off_analysis.json`, `alternative_selection.json` |
| 4 | `architecture_decision` | `decision-recorder` | `adr.json`, `architecture_decision.json` (final package) |

Agents do not pin a model; they inherit the session model.

Do not do a stage's domain work yourself, and do not edit stage artifacts. If a stage fails, the fix comes from re-invoking that stage's agent.

## Files

- `_workspace/artifacts/00_project_description.json`, `_workspace/artifacts/00_functional_requirements.json`: input ports, written by you in Step 1.
- `_workspace/artifacts/<artifact>.json`: stage artifacts (SARA's artifact names, one location for all).
- `_workspace/run_log.md`: your gate results per stage, retries and stop reason.
- `output/architecture_decision.json`: copy of the final package once Stage 4 passes.
- Contracts: `references/contracts/*.schema.json`. Shared method: `references/methodology.yaml` (verbatim copy of the package methodology; where it differs, the Stage 4 inputs and outputs listed in this skill and in the agents, adaptations A6 and A7, apply).

## Procedure

### Step 0: Check for existing work

1. No `_workspace/` → fresh run, go to Step 1.
2. `_workspace/` exists and the user supplied **new** project input → move it to `_workspace_<YYYYMMDD-HHMMSS>/` (take the time from `date +%Y%m%d-%H%M%S`) and start fresh.
3. `_workspace/` exists and the user asks to redo or fix part of the run (e.g. "redo only Stage 3", "fix the diagram", "continue"):
   - Run `python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --stage <id>` for each stage to see which stages pass.
   - Restart at the earliest stage the request or a failing gate names. Every later stage depends on it, so re-run all later stages too, in order. Move the artifacts of the restarted and later stages to `_workspace/superseded_<timestamp>/` before re-running so stale files cannot pass a gate.
   - Pass the user's feedback to the restarted stage's agent (see the re-invocation prompt below).

### Step 1: Write the input ports

1. Obtain the project description and the functional requirements from the user's message or the files they name. If either is missing, ask for it; do not invent requirements.
2. Write them unchanged in meaning to `_workspace/artifacts/00_project_description.json` (a JSON string or object) and `_workspace/artifacts/00_functional_requirements.json` (a JSON string, list or object; keep any identifiers such as `RF1` exactly).
3. Run `python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --ports`. Proceed only on exit code 0.

### Step 2: Run the stages in order

For each stage 1 → 4:

1. **Readiness gate.** Re-run the gate for every upstream stage (`--stage <upstream id>`; for Stage 1, `--ports`). All must exit 0. Stage 4 also needs Stage 1 and Stage 2 to pass, because it reads their artifacts (A6).
2. **Invoke the stage agent** (one call, foreground). Stage 1 shown; for Stages 2–4 use `subagent_type` `solution-designer`, `alternative-evaluator`, `decision-recorder` and the matching stage number and id:

   ```
   Agent(
     subagent_type: "requirements-drivers-analyst",
     description: "SARA Stage 1 requirements_drivers",
     run_in_background: false,
     prompt: "Run SARA Stage 1 (requirements_drivers) in this project. Artifacts are in _workspace/artifacts/.
              Execute your tasks in the pinned order, reading each task's SKILL.md first, and finish with
              your completion protocol. Report each artifact with its schema-check result."
   )
   ```

3. **Stage gate.** Run `python3 .claude/skills/sara-architecture-orchestrator/scripts/validate_stage.py --stage <stage id>` yourself. Do not rely on the agent's report. Record the output in `_workspace/run_log.md`.
4. **On exit 1 (missing or invalid artifact):** re-invoke the same agent **once** with the re-invocation prompt:

   ```
   "Previous Stage <N> artifacts exist in _workspace/artifacts/. The stage gate failed with:
    <exact validator output>. Read the existing artifacts and fix only what fails, keeping the
    task order and skill rules. Then re-run your completion protocol."
   ```

   Then run the stage gate again. If it still fails, **stop the pipeline**: later stages cannot run on invalid inputs. Record the failure and go to Step 3.
5. **On exit 2 (`VALIDATION UNAVAILABLE`):** stop. Do not continue unverified. Tell the user to install `jsonschema` for `python3`.

### Step 3: Wrap up

1. If Stage 4 passed, copy `_workspace/artifacts/architecture_decision.json` to `output/architecture_decision.json`.
2. Report to the user:
   - each stage's gate result, retries and, if it stopped, where and why;
   - the selected alternative id (read from `alternative_selection.json`);
   - that the result is a **draft recommendation pending architect review**;
   - the post-run checks that are still open (below). Do not mark any of them as done, and do not claim any methodology checkpoint is achieved: they are assessed after the run from the artifacts, never from stages finishing.

### Post-run checks (manual; not performed by this harness)

| Check | What the reviewer compares |
|---|---|
| v-requirement-coverage | Every requirement id in `requirements_analysis.json` is evaluated for every alternative in `alternative_evaluation.json`. |
| v-reference-integrity | `source_requirement_ids` exist in `requirements_analysis.json`; alternative ids in evaluation, trade-offs and selection exist in `alternatives.json`; `selected_alternative_id` in the package equals the Stage 3 selection. |
| v-package-fidelity | `adr_markdown` in the package equals `adr.json`; `selected_alternative_id` and `selection_rationale` equal `alternative_selection.json`. |
| v-scope-boundaries | Stage 1 proposes no solutions; Stage 2 does not select; Stage 3 does not introduce alternatives; Stage 4 does not change the selection. |
| architect-review | A software architect confirms the rationale, the visible weaknesses, and that the ADR and diagram match the selected alternative before use. |

## Error handling

| Situation | Response |
|---|---|
| Stage gate fails | One repair re-invocation of the same agent with the exact validator output, then the gate again. A second failure stops the pipeline. |
| Agent returns without writing all artifacts | Same as a failed gate. Do not write the missing artifact yourself. |
| Usage limit, expired authentication, or denied permission | Do not retry. Run the gates to see how far the run got, record it in `_workspace/run_log.md`, and report. For a usage limit, give the reset time if shown. |
| Validator unavailable (exit 2) | Stop; ask the user to install `jsonschema`. |
| Conflicting or ambiguous input | Pass it through unchanged; Stage 1 records ambiguities. Do not resolve it by assumption. |

When you report a partial run, state only facts you verified from the files and gate output. Never fill in a stage's judgment (e.g. why an alternative was rejected) yourself.

## Test scenarios

### Happy path

1. The user provides a project description and a list of functional requirements `RF1…RFn`.
2. Step 1 writes both ports; `--ports` passes.
3. Stages 1–4 each run once; every stage gate passes on the first try.
4. Expected: 11 artifacts in `_workspace/artifacts/`, `output/architecture_decision.json` with the same `selected_alternative_id` as `alternative_selection.json`, and a report that lists the open post-run checks and the pending architect review.

### Error path

1. Stage 2 writes `alternatives.json` without the `limitations` key in one alternative.
2. The Stage 2 gate fails with `alternatives.json: alternatives/1: 'limitations' is a required property`.
3. The orchestrator re-invokes `solution-designer` once with that output; the agent edits the file; the gate passes; Stage 3 starts.
4. If the second gate also fails: the pipeline stops after Stage 2, `run_log.md` records both failures, and the report says Stages 3–4 did not run.
