# HarnessWeaver approach: inputs, generation, runtimes, sandboxes

**Status:** agreed approach for the CAIN 2027 prototype, 2026-10-24. Decisions in §9.
**Relation to other docs:** [STATUS.md](STATUS.md) lists what exists; this file defines what the prototype should be.

## 1. Summary

A coding agent equipped with the HarnessWeaver skills (`src/harnessweaver/skills/`: `harness` and `evolve`) performs generation. Deterministic tools prepare the agent's sandboxes, check what it produces, and run and record the generated harnesses.

```text
 ① AUTHOR (architect)                ② GENERATE (coding agent + unified harness skill, interactive, in a generation sandbox)
 pilots/<p>/sources/                  design phase ──────▶ harnessspec.yaml (design; human gate + hw validate)
   intent.yaml          ──────────▶   target gate: "Claude Code, DeepAgents, or both?"
   methodology.yaml                   materialize phase ─▶ build/claude/      (Claude Code project)
   domain/                                              └▶ build/deepagents/  (stage dirs + wiring)
                                      each target writes a materialization report (mapped / approximated / unsupported)
        ▲                                         │
        │                                         ▼  ③ CHECK BUNDLE (deterministic: hw check-bundle)
 ⑤ EVOLVE (coding agent + evolve skill)           │
   change sources or spec, regenerate             ▼
        ▲                             ④ RUN (execution sandbox per target × case; inputs only)
        └──── hw check + review ◀──── Claude Code CLI  |  HarnessWeaver stage host (or SARA's pipeline)
```

Principles:

1. **Authored sources stay small and runtime-free.** They state what the work is, what the domain knows and how the method proceeds. They contain no agent design, runtime constructs or case data.
2. **Generation is skill-driven and interactive.** One `harness` skill asks the user the necessary questions, designs the HarnessSpec, asks which target(s) to generate, and materializes each target from the same spec using target-specific references. The `evolve` skill revises a generated harness. The HarnessWeaver contribution is the method encoded in these skills plus the spec they share, not a code generator.
3. **Generation runs in its own sandbox and is recorded.** It has fixed inputs, pinned skill digests, the coding agent and model, the prompt and the transcript. Because LLM generation is not deterministic, the evidence is the recorded output, with its checks and any manual interventions, not a claim of reproducible bytes.
4. **Deterministic tools surround the agent; they do not replace it.** They prepare the sandboxes, validate the spec, check the bundle structure, run the generated harness and check the outputs.
5. **Cases are bound at run time.** An execution sandbox receives only a case's generation inputs. Evaluator-only data never enters any sandbox.
6. **Every manual edit after generation is an intervention.** It is logged with its reason and counted.

## 2. Step ① — What the architect provides

```text
pilots/<pilot>/
  sources/
    intent.yaml          # goal, scope, exclusions, intended user/decision, human review, target runtimes
    methodology.yaml     # activities, order/conditions, readiness, outputs, completion; semantic-state fields; review points; reference boundary
    domain/
      sources.yaml       # knowledge sources: id, ref, kind, authority, notes
      skills/            # existing domain skills (SKILL.md), portable
      contracts/         # JSON Schemas of output (and key intermediate) artifacts
      references/        # templates, glossaries, method excerpts
  cases/<case>.yaml      # case binding (§5); never read during generation
```

| File | Must say | Must not contain |
|---|---|---|
| `intent.yaml` | goal; scope; exclusions; user and decision supported; human review requirement; target runtimes | case facts; agent design |
| `methodology.yaml` | activities and order; readiness, outputs and completion per activity; semantic-state fields with evidence rules; review points; reference boundary | runtime constructs (subagents, tools, graphs) |
| `domain/` | sources with authority/provenance; portable skills; output contracts | runtime-specific paths, tools or types |

The ATAM pilot already has most of this: `methodology.yaml` matches, the report template and Pydantic models give the contract, and the domain skills exist (duplicated per runtime). The spec's intent section becomes `intent.yaml`.

A **source brief** (`sources/README.md`) may stand in for `intent.yaml` and `domain/` in a lightweight one-off, as the `harness` skill already allows. The pilots use the full form.

## 3. Step ② — Generation with a unified, interactive harness skill

### 3.1 Skill set (implemented 2026-10-24)

The generation skills live in `src/harnessweaver/skills/` (formerly `harness-en/skills/`) and are reduced to two. The former `deepagents-port` skill is now the DeepAgents target reference inside `harness`.

```text
src/harnessweaver/skills/
  README.md
  harness/                       # generate: intake → design → target gate → materialize → validate/report
    SKILL.md                     # runtime-neutral procedure and question gates
    references/
      question-gates.md          # gates G0–G6 and the harness-answers.yaml format
      intake-and-harvest.md      # design inputs; harvesting sources from an existing app/harness
      materialization-report.md  # fidelity report template (both targets)
      targets/
        claude-code.md           # former Steps 3–7 (agents, skills, orchestrator, CLAUDE.md, tests, operations)
        deepagents.md            # former deepagents-port skill, as Steps D0–D5, plus wiring.yaml
        deepagents-target-pattern.md, deepagents-mapping-table.md
      execution-modes.md, orchestrator-template.md, workflow-recipes.md, model-selection-guide.md, qa-agent-guide.md   # Claude Code details
      team-patterns.md, team-examples.md, skill-writing-guide.md, skill-testing-guide.md                              # shared design guidance
  evolve/
    SKILL.md                     # revise: change sources, spec, target mapping or host → regenerate via harness
```

`evolve` stays separate because it is triggered by run results and review feedback, not by a build request. It reuses the same target references.

### 3.2 Questions the skill asks

The skill keeps the existing gate discipline (ask before writing files; batch related questions; present concrete options with a recommendation). The gates, in order:

| Gate | When | Questions |
|---|---|---|
| G0 Intake | start | Which sources are authoritative? Is there an existing spec, harness or app to start from (harvest)? Saved spec or lightweight one-off? |
| G1 Clarification | after domain analysis | Ambiguities in scope, terminology, inputs, consumers that the sources do not resolve |
| G2 Design options | end of design | Team shape and orchestration (2–3 options with trade-offs); stage boundaries |
| G3 Artifact contracts | before writing skills | Artifact filenames, top-level fields, ID linkage; reuse of the supplied JSON Schemas |
| **G4 Target** | after the spec is validated | **Claude Code, DeepAgents, or both?** Output directory per target |
| G5 Target-specific | per selected target | *Claude Code:* allowed execution modes (sub-agents only vs persistent agents vs `Workflow`), model tiers. *DeepAgents:* model/provider, host (HarnessWeaver stage host vs an existing app such as SARA), human-in-the-loop points, subagents allowed |
| G6 Write confirmation | before writing files | Summary of files to be written and known losses per target |

**Interactive and sandboxed runs use the same skill.** If the working directory contains `harness-answers.yaml`, the skill takes answers from it, asks only about what is missing, and writes every question and answer, whether answered from the file or live, into `design-notes.md`. A pilot can therefore be generated interactively the first time and replayed with the recorded answers, without a separate non-interactive mode.

### 3.3 Generation sandbox

```text
sandboxes/gen-<pilot>-<yyyymmddThhmm>/
  sources/              # read-only copy of pilots/<p>/sources/ (and the spec, when only materializing)
  skills-plugin/        # the arm's skills wrapped as a Claude Code plugin, loaded with --plugin-dir:
                        #   HW arm: src/harnessweaver/skills/{harness,evolve}; baseline arm: baselines/revfactory-harness-v2.1.0-en
                        #   (digests recorded)
  .claude/skills/       # langchain-skills deep-agents-* (HW arm with a DeepAgents target only; digests recorded)
  harness-answers.yaml  # optional: pre-recorded gate answers
  generated/            # the only writable area: harnessspec.yaml, design-notes.md, claude/, deepagents/
  RUNBOOK.md            # what the user runs and what to send back (Claude sessions are run by the user, §9.8)
  run.sh                # launches Claude Code in this directory (interactive by default; `-p` when replaying answers)
  record/               # transcript, agent/model/version, input and skill digests, duration, cost if available
```

The coding agent is **Claude Code**. A second coding agent (e.g., Codex) is an optional robustness check. `hw sandbox collect` copies `generated/` into `pilots/<p>/` (`harnessspec.yaml`, `design-notes.md`, `build/<target>/`) together with `generation-record.json`. Generated files are committed.

### 3.4 What each target emits

| Target | Emits into `build/<target>/` | Checked by |
|---|---|---|
| Claude Code | `.claude/agents/*.md`, `.claude/skills/*/SKILL.md` (domain skills + orchestrator), `CLAUDE.md` pointer, `materialization-report.md` | `hw check-bundle --target claude` |
| DeepAgents | `stage{N}-{name}/AGENTS.md` + `skills/*/SKILL.md`, `wiring.yaml` (stages, hand-off prompts, expected artifacts), `port-manifest.md` (Python-side notes for an existing host app), `materialization-report.md` | `hw check-bundle --target deepagents` (automates the Step D5 checklist) |

The materialization report is the fidelity record: each spec element is mapped, approximated or unsupported, with the reason.

### 3.5 Skill changes (done 2026-10-24)

1. Merge `deepagents-port` into `harness` as `references/targets/deepagents.md` (plus the pattern and mapping files). Delete the `deepagents-port` skill directory.
2. Move the Claude-specific Steps 3–7 of `harness/SKILL.md` into `references/targets/claude-code.md` (as Steps C1–C5). `SKILL.md` keeps the runtime-neutral procedure and the gates.
3. Add the G4/G5 target gates and the `harness-answers.yaml` rule.
4. Add `wiring.yaml` and `materialization-report.md` as required outputs per target.
5. Update `evolve` to route changes to `sources/`, the spec or `build/<target>/`, and to read the target references.

Each revision is recorded by skill digest in the generation record.

### 3.6 Generation baseline (Claude runtime only)

To show what HarnessWeaver's skills add, the same pilot sources are also given to the **original revfactory/harness v2.1.0 skills**, run in a direct English translation ([`baselines/revfactory-harness-v2.1.0-en/`](../../baselines/revfactory-harness-v2.1.0-en/TRANSLATION.md)). The Korean original is vendored verbatim in [`baselines/revfactory-harness-v2.1.0/`](../../baselines/revfactory-harness-v2.1.0/BASELINE.md) as the authority for the translation. The baseline arm runs in its own generation sandbox, with the same opening prompt, coding agent, model and equivalent live answers, and produces a Claude Code project. Both projects then run on the same case in execution sandboxes and are checked the same way.

The baseline emits only the Claude Code form, so it serves Claude-runtime comparisons only. DeepAgents is compared against the hand-written reference runner instead (§4.1). The protocol, measures and threats are in `BASELINE.md`.

**Everything runs in English:** both arms' skills, the opening prompt, the gate answers and the generated artifacts. Comparing against the English baseline isolates HarnessWeaver's changes from the language of the skills.

## 4. Step ④ — Runtime hosts

| | Claude Code | DeepAgents |
|---|---|---|
| Generated form | Claude Code project: `.claude/agents`, `.claude/skills`, `CLAUDE.md`, `_workspace/` convention | Stage directories (`AGENTS.md` + `skills/`), JSON artifact contracts, `wiring.yaml` |
| Host (not generated) | Claude Code CLI | **HarnessWeaver stage host**: a small generic runner implementing the target pattern (one `create_deep_agent` per stage, `/agent/` mounted read-only, `/artifacts/` on a filesystem backend, completion checked against `wiring.yaml`). For SARA, SARA's own `PipelineService` is the host once adapted to read the generated stage directories. |
| Orchestration | Whatever the harness skill chose (orchestrator skill + subagents), recorded in the report | Sequential stages, deterministic in Python (the target pattern) |

### 4.1 What decision 3 implies

The DeepAgents target emits **stage directories, not Python**: one folder per stage with an `AGENTS.md` (ordered tasks, rules, completion protocol) and its `skills/`, plus `wiring.yaml`. This is the pattern the DeepAgents reference was distilled from (SARA).

1. **A host is needed, and it is not generated.** Something must loop over the stages, create one deep agent per stage with that stage's `AGENTS.md` and skills, pass the hand-off prompt, and check that the declared artifacts exist and parse. For SARA, its own `PipelineService` already does this (with Firestore). For ATAM and any new pilot, HarnessWeaver provides one generic **stage host** (an estimated 150–250 lines in `src/harnessweaver/hosts/deepagents.py`), written once and reused. Only data comes out of the skill, so generated output is reviewable and checkable.
2. **The generated DeepAgents harness is sequential.** Stage order is fixed in Python and task order inside a stage is fixed in `AGENTS.md`. The supervisor and fan-out profiles built in U7 (`src/harnessweaver/runtime/`, `adapters/deepagents/`, `pilots/atam/deepagents/atam_harness/`) are **not produced by the skill**. They stay in the repository as a hand-built **reference realization** and as evidence for runtime-level orchestration, but not as the generated path.
3. **Artifact contracts become JSON plus JSON Schema, not Pydantic.** Each stage writes `/artifacts/*.json`. The host validates them against `sources/domain/contracts/*.schema.json`, and the existing ATAM checker (`benchmarks/atam/pilot.py check`) runs on the final report as today. The ATAM Pydantic models remain only in the reference runner, and their exported schema becomes the contract.
4. **The two P1 targets will not have the same orchestration.** The Claude form uses whatever the skill chose at gate G2 (e.g., an orchestrator with sub-agents). The DeepAgents form is a stage pipeline. The paper compares *what the same spec becomes in each runtime*, with the losses from the materialization reports, not equivalent executions.
5. **What the paper gains:** three comparisons with no extra runs. Generated vs reference (DeepAgents and Claude) shows what hand-building adds. Claude vs DeepAgents generated from one spec shows runtime flexibility. Regenerated SARA vs original SARA shows skill fidelity.

Alternatives considered:

| Option | Generated DeepAgents output | Keeps U7 profiles on the generated path | Cost | Risk |
|---|---|---|---|---|
| **A. Stage pattern + stage host** (chosen) | Markdown + `wiring.yaml` | No (reference only) | host ≈ 0.5–1 d | low; matches the skill and SARA |
| B. Config for the U7 runner | `agents.yaml`, `orchestration.yaml`, schemas | Yes | generalize the ATAM-specific runner (Pydantic → schema) ≈ 1.5–2 d; rewrite the skill's target reference | medium; SARA does not use this runner |
| C. Full Python app | Python + Markdown | Possibly | low upfront | high: large, variable generated code that is hard to check and compare |

The hand-written `pilots/atam/claude-plugin/` is likewise the Claude reference realization.

## 5. Step ④ — Execution sandboxes

```text
sandboxes/run-<pilot>-<target>-<case>-<yyyymmddThhmm>/
  sandbox.yaml        # pilot, target, model, timeouts; digests of spec, bundle, case binding
  bundle/             # read-only copy of build/<target>/
  input/              # generation inputs only, extracted per the case binding
  workspace/          # the only writable area for the runtime
  output/             # report, artifacts, transcript, runtime sidecar
  run.sh              # single entry point
  manifest.json       # SHA-256 of bundle, input and outputs; tool versions
```

Case binding (`pilots/<p>/cases/<case>.yaml`):

```yaml
case: banking
generation_inputs:          # copied into input/
  - id: architecture-context
    from: ../../../case-studies/architecture-eval/ATAM/data/banking.json
    select: ATAM_Evaluation.evaluation_inputs
evaluator_only:             # never copied; read only by hw check
  - from: ../../../case-studies/architecture-eval/ATAM/data/banking.json
    select: ATAM_Evaluation.ground_truth_outputs
checks: [schema, semantic-state, atam-source-scenarios]
```

| Target | `run.sh` essentials | Isolation |
|---|---|---|
| Claude Code | copy `bundle/` into `workspace/` (it is a project); `cd workspace && claude -p --bare --no-session-persistence --append-system-prompt-file CLAUDE.md --settings ../claude-settings.json --add-dir ../input --output-format stream-json --model <m> "<invoke orchestrator on input>"` | `--bare` skips user hooks, plugins and CLAUDE.md discovery (the user's global RTK and graphify setup stays out). The generated settings allow reads in `input/`, writes in `workspace/`, and deny Bash and web tools. **To verify:** that project `.claude/agents` and `.claude/skills` load under `--bare`. `--bare` also requires `ANTHROPIC_API_KEY` (OAuth is not read). |
| DeepAgents | `python -m harnessweaver.hosts.deepagents --bundle ../bundle --input ../input --workspace . --out ../output --config ../sandbox.yaml` | Backend rooted at the sandbox; `/agent/` read-only from `bundle/`; env vars only from the sandbox `.env` |

This is directory and permission isolation. A container is later work. The leakage claim does not depend on it, because evaluator-only data is never copied in.

`hw check <sandbox>` runs outside the sandbox and writes `check.json`. `hw sandbox record` copies the manifest, outputs and check result to `docs/cain-2027/evidence/<run-id>/`.

## 6. `benchmarks/` (kept for now)

`benchmarks/` holds two HarnessWeaver-owned **evaluation protocols**:

- `benchmarks/atam/` (`pilot.json`, `pilot.py prepare|check|record`, `pilot-status.md`). `prepare` creates a run directory with evaluation inputs only, `check` is the deterministic ATAM checker, and `record` writes a write-once execution record. Run records are git-ignored.
- `benchmarks/saam/` (`pilot.py`, `runner.py`, protocol, blind-review preparation). This is a baseline-vs-spec-guided comparison for the parked SAAM pilot.

Decision (2026-10-24): **keep it during the sprint.** The new tooling reuses it rather than replacing it:

- `hw check` calls `benchmarks/atam/pilot.py check` for ATAM outputs.
- `hw sandbox create` borrows the input-only extraction logic of `pilot.py prepare`, but reads case bindings from `pilots/<p>/cases/`.
- `pilot-status.md` remains the ATAM evidence log until the curated evidence package exists.

Remove `benchmarks/` later, once `hw sandbox` and the per-pilot checks cover everything it does.

## 7. Pilots under this approach

| Pilot | ① Sources | ② Generation | ④ Hosts | Cases | Evidence for the paper |
|---|---|---|---|---|---|
| **P1 ArchEval-ATAM** | migrated from existing spec, methodology, skills, template | one `harness` session: design, then G4 = both targets | Claude Code; HarnessWeaver stage host | banking | generation records; materialization reports (mapping/loss); bundle checks; one run per target; diff against reference realizations |
| **P2 SARA** | harvested (G0) from SARA's 4 `AGENTS.md` + 11 `SKILL.md` | one `harness` session: harvest, design, G4 = DeepAgents, G5 host = SARA (the emitted `wiring.yaml` also lets the HarnessWeaver stage host run it standalone) | HarnessWeaver stage host (standalone); SARA's `PipelineService` (integration, stretch) | one project + requirements | harvest provenance; regenerated stage directories vs SARA's originals; standalone run; integration changes |
| **P2b SARA variation** (if time) | change `methodology.yaml` or a domain skill (method variant; runtime unchanged) | `evolve` or a `harness` replay with recorded answers | stage host | same case | diff sources → spec → bundle; files changed; run outcome |

P2 is also a fidelity check of the skill itself. The DeepAgents target pattern was distilled from SARA, so regenerating SARA's stage directories from harvested sources and comparing them with the originals measures how much of the pattern the skill reproduces.

## 8. Implementation delta (ordered)

| # | Work | Est. |
|---|---|---|
| 1 | ATAM `sources/` layout; JSON Schema export of the report contract; case binding file | 0.5 d |
| 2 | ~~Unified skill~~ done 2026-10-24 (structure and gates; prose refinement continues as runs expose gaps) | — |
| 3 | `hw sandbox create/collect/record` for generation and execution sandboxes; `run.sh` templates; `hw check-bundle` for both targets; `hw check` delegating to `benchmarks/atam/pilot.py check` | 1 d |
| 4 | HarnessWeaver DeepAgents stage host (generic target-pattern runner) | 0.5–1 d |
| 5 | P1: generate spec, Claude form and DeepAgents form; one execution run per target; checks | 0.5–1 d (LLM time dominates) |
| 5b | P1 baseline arm: English baseline skills in a generation sandbox → Claude project → execution run; coverage checklist for both arms | 0.5 d (user session + analysis) |
| 6 | P2: harvest, spec, DeepAgents form, standalone run | 1 d |
| 7 | P2 integration with SARA; P2b variation | stretch |

Items 1 and 3–6 take about 3.5–4.5 days. If time runs short, the cut order is: P2b, SARA integration, a second generation run for variance, and then the design step (keep the existing hand-written spec and say so, still materializing from it with the skills).

## 9. Decisions (agreed 2026-10-24)

1. Generation is done by a coding agent (Claude Code) with the HarnessWeaver skills, recorded in a generation sandbox. Deterministic tools only check, run and record.
2. The Claude target is a Claude Code **project** (what the `harness` skill emits), not a plugin. The existing plugin is a reference realization.
3. The DeepAgents target is the stage-pipeline pattern with a small HarnessWeaver stage host (option A, §4.1). The existing multi-profile runner is a reference realization.
4. Generated files are committed under `pilots/<p>/build/`, with generation records.
5. `benchmarks/` is kept during the sprint and reused by the new tooling; it is removed later.
6. Sandboxes use directory and permission isolation; containers are later work.
7. The skills are `harness` (interactive generation, target choice at gate G4) and `evolve`, in `src/harnessweaver/skills/`. `deepagents-port` is merged into `harness`.
8. **Claude sessions are run by the user.** Any step that runs Claude Code with skills is executed by the user, who reports back the sandbox's `record/` and `output/`. That covers generation in a generation sandbox and Claude-target runs in an execution sandbox. The development agent prepares the sandbox, its `run.sh`, a runbook and the answers file, then analyzes the returned records. DeepAgents execution runs are done by the development agent.
9. **Generation baseline:** revfactory/harness v2.1.0 skills in a direct English translation, loaded as a plugin, for Claude-runtime comparisons only (§3.6). The verbatim Korean original is kept as the translation's authority. All runs are in English.

## 10. Later (not for the submission)

- **Package the HarnessWeaver skills as a Claude Code plugin.** For now, `hw sandbox create` builds a temporary plugin wrapper around `src/harnessweaver/skills/{harness,evolve}`, which is the same layout a released plugin would use (`.claude-plugin/plugin.json` + `skills/`). Publishing it means fixing the plugin name and namespace (skills then become `<plugin>:harness` and `<plugin>:evolve`) and updating the skills' cross-references.
- Containers for sandboxes; a third target runtime; the Loop primitive; LLM-free regeneration checks.

## 11. Deviations from the co-author plan

The co-author plan ([HarnessWeaver_CAIN_2027_Coauthor_Plan.md](HarnessWeaver_CAIN_2027_Coauthor_Plan.md)) was written before this approach was agreed. Where they differ, this file governs the prototype; the paper text should follow it.

| Plan | Prototype | Why |
|---|---|---|
| Separate IntentSpec, DomainSpec and Methodology schemas | Authored `sources/` (`intent.yaml`, `methodology.yaml`, `domain/`) feeding one HarnessSpec v0.2 | Same separation of concerns without three new schemas in a six-day sprint |
| A deterministic generator and materializers | Generation by a coding agent with the `harness` skill, recorded in generation sandboxes; deterministic tools check, run and record | The method lives in the skills; recording plus checks gives the evidence |
| Orchestration primitives Sequence/Parallel/Delegate/Loop | Claude target: what the skill selects at gate G2. DeepAgents target: a sequential stage pipeline. The U7 supervisor/fan-out profiles remain a hand-written reference | Matches what each target can express; Loop is future work |
| One domain × two runtimes; second domain as a stretch | P1 ATAM × {Claude, DeepAgents}; P2 SARA × DeepAgents (harvested), P2b methodology variation as a stretch | SARA provides an independently written design method and the "bespoke application" example |
| No generation baseline | revfactory/harness v2.1.0 (English) as the Claude-runtime generation baseline | Shows what HarnessWeaver adds over its closest prior art |

