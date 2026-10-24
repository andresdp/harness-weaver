# Target: DeepAgents stage pipeline

Read this file when gate G4 selects **DeepAgents**. It turns a validated HarnessSpec (or a recorded lightweight brief) into **stage directories plus wiring data**, not application code: one deep agent per stage, an `AGENTS.md` per stage, `skills/*/SKILL.md` per task, JSON artifacts on a virtual filesystem, and a `wiring.yaml` that a host executes deterministically. The conventions are defined in `deepagents-target-pattern.md`; keep `deepagents-mapping-table.md` open while mapping.

**This is generation, not line-by-line translation.** Claude Code constructs (`SendMessage`, `Workflow` scripts, `subagent_type`, model tiers) have no DeepAgents equivalents. Extract the design (stages, ordered tasks, artifact contracts, verification intent, scope boundaries) and re-emit it in the target conventions. Never fake a mapping the target cannot express; record it in the materialization report.

**Host.** The output is executed by a host that is not generated:

- the **HarnessWeaver stage host** (`python -m harnessweaver.hosts.deepagents`), which reads `wiring.yaml`; or
- an **existing application** that already runs stage directories (for example SARA's `PipelineService`). In that case also write `port-manifest.md` with the Python-side changes the application needs. Do not edit the application's code unless the user asks.

Gate G5 asks which host to target.

**langchain-skills.** The official [langchain-skills](https://github.com/langchain-ai/langchain-skills) (`deep-agents-core`, `deep-agents-orchestration`, `deep-agents-memory`, `langgraph-human-in-the-loop`) are the authority on code-side questions such as middleware, checkpointers, interrupts and backends. Consult them for any `port-manifest.md` content. If they are not installed, say so and record in the report that code-side notes were not cross-checked.

## Contents

- Design-time advice (when DeepAgents is a target)
- Step D0: Inventory the inputs
- Step D1: Decide the stage boundaries
- Step D2: Resolve decision points
- Step D3: Emit stage directories
- Step D4: Emit `wiring.yaml` (and `port-manifest.md` for an existing host)
- Step D5: Validate and report
- Principles

## Design-time advice (when DeepAgents is a target)

If DeepAgents is selected at G4, or is likely to be, apply these constraints at the design gate (G2) so the mapping stays mechanical. They also keep a Claude Code form comparable.

| Design choice | Effect on the DeepAgents form |
|---|---|
| A fixed sequential pipeline of stages | Maps 1:1 to host-driven stage sequencing |
| All data between steps as JSON artifacts with `{NN}_{step}.json` names | Maps directly to `/artifacts/*.json` |
| One orchestrator plus one-shot specialists | Avoids messaging-based collaboration with no target equivalent |
| Every task documents its input artifacts, output JSON structure, and read-back rule | Produces exactly the sections a target `SKILL.md` needs |
| Verification as explicit task steps, not messaging loops | Verification intent survives as intra-agent steps |

A worked example (the four-stage architecture decision pipeline) is in the repository's `docs/harness-100-prompts_EN.md`, appendix "portability-aware example".

## Step D0: Inventory the inputs

1. Read the HarnessSpec and record its path, version and digest. Validate it with `hw validate` (in the HarnessWeaver repository: `conda run -n harness hw validate <spec>`). If validation is unavailable, say so; do not claim the spec passed.
2. Read the domain skills, contracts (JSON Schemas), and methodology the spec references. These carry the design intelligence that must survive.
3. If other runtime artifacts are supplied (a Claude Code project, an existing DeepAgents app), compare them with the spec and list conflicts. The spec is the design authority; carry runtime-only behavior as a D2 decision.
4. If a source still uses v1 artifacts (`TeamCreate`, experimental flags), stop and migrate them first (see `../execution-modes.md`, "Migrating from v1 to v2").

## Step D1: Decide the stage boundaries

The target pattern is **one deep agent per stage; each stage runs N ordered task skills**.

- Map each spec stage (or each group of stages that produces one stable artifact set) to `stage{N}-{snake_case_name}/`.
- A spec *role* is not necessarily a target *stage*. Roles that perform one task inside a stage become that stage's task skill; "who" survives as the `AGENTS.md` responsibility sentence.
- Parallel work inside a stage: serialize it (the pattern's "one task at a time" rule) or flag it as a subagent decision in D2.
- Record the stage plan: number, name, responsibility sentence, ordered tasks, artifact filenames, upstream artifacts consumed, and the spec ids each element comes from.

Show the stage plan and the artifact table to the user (gate G3) before writing files, unless `harness-answers.yaml` already fixes them.

## Step D2: Resolve decision points

Decide each item once and apply it everywhere. Record the decisions in the materialization report.

| Decision | Default | Alternative |
|---|---|---|
| Agent-to-agent messaging (`SendMessage`) | Convert exchanges into artifact read/write steps | Enable DeepAgents subagents if the exchange is genuinely iterative |
| User confirmation points in the harness | Drop (the Claude-side gates don't apply at port time); if the *application* needs approval flows, add `HumanInTheLoopMiddleware` + checkpointer per langchain-skills `langgraph-human-in-the-loop` guidance | `interrupt_on` tool-level approval for artifact writes |
| Adversarial verification / judge panels | Intra-agent verification skill step (matches target pattern) | Dedicated verification stage between producer stages |
| `Workflow` scripts | Discard; sequencing moves to the Python pipeline + AGENTS.md ordered tasks | — |
| Model tiers (fable/opus/sonnet) | Single env-driven model; keep tier rationale as comments in AGENTS.md/skills | Map tiers to provider models (e.g. pro/flash) if the target supports per-agent models |
| Structured schemas (`schema`/`agentType`) | JSON structure block in each skill + Mandatory Completion Protocol in AGENTS.md | — |
| `CLAUDE.md` registry | Discard; the Python `stages.py` registry replaces it | Keep a domain README with the change-history table for evolve compatibility |
| Semantic methodology state | Final stage writes a semantic-state artifact (or report section) with evidence references; runtime completion never sets it | — |
| Spec input ports | Host writes each case input to `/artifacts/00_<port>.json` before stage 1 | — |

## Step D3: Emit stage directories

For each stage, follow `deepagents-target-pattern.md` exactly:

1. `stage{N}-{name}/AGENTS.md`: role header, responsibility, strictly ordered task list, Input Artifacts, execution Rules, scope boundaries, Mandatory Completion Protocol, post-task protocol.
2. `stage{N}-{name}/skills/{task}/SKILL.md`: frontmatter (`name`, `description`), Objective, Input Artifacts, Procedure, Rules with a Correct/Incorrect pair, Expected Output (path, JSON structure block, read-back verification), and the boundary line.
3. JSON contracts: one artifact file per task, `{NN}_{step}.json` in stage order, with cross-stage references by ID fields. When the spec supplies a JSON Schema for an artifact, the JSON structure block must agree with it; name the schema in `wiring.yaml`.

Carry over the domain skills' content (procedures, rules, examples, evidence standards). Rewrite only the runtime sections: paths, collaboration and output location.

## Step D4: Emit `wiring.yaml` (and `port-manifest.md` for an existing host)

`wiring.yaml` is the machine-readable contract between the generated stages and any host:

```yaml
wiring_version: "0.1"
spec: {path: <relative path>, id: <spec id>, version: <spec_version>}
inputs:                      # spec input ports → files the host writes before stage 1
  - port: <port id>
    path: /artifacts/00_<port>.json
stages:
  - number: 1
    dir: stage1-<name>
    handoff_prompt: <one sentence: responsibility and consumed artifacts>
    artifacts: [01_<step>.json, 02_<step>.json]
    schemas: {01_<step>.json: <relative path to JSON Schema>}   # optional, per artifact
output:
  artifact: <final artifact filename>
  schema: <relative path to JSON Schema>                        # optional
human_gates:                 # from the spec; the host records them, it does not auto-approve
  - id: <gate id>
    after_stage: <N>
```

For an existing application host, also write `port-manifest.md`. It holds the `STAGES` registry entries, the `STAGE_ARTIFACTS` rows, factory notes (memory and skills mount paths, backend routing), and any D2 decisions that need application support, following langchain-skills practice.

## Step D5: Validate and report

Checklist (`hw check-bundle --target deepagents` automates the structural items):

- [ ] Every stage directory has `AGENTS.md`; every task has `skills/{task}/SKILL.md` with frontmatter.
- [ ] Every skill's Input Artifacts exist as outputs of an earlier skill or as declared inputs in `wiring.yaml`.
- [ ] Every artifact in every Mandatory Completion Protocol appears under that stage in `wiring.yaml`.
- [ ] JSON structure blocks use snake_case, reference prior artifacts by ID fields, and agree with any named schema.
- [ ] No Claude Code constructs remain (`SendMessage`, `Workflow`, `subagent_type`, `agentType`, `.claude/` paths, `model: opus` pins).
- [ ] No `AGENTS.md` or `SKILL.md` body exceeds ~500 lines.
- [ ] Each stage has a scope-boundary section.

Then write `materialization-report.md` (template: `../materialization-report.md`) with a suggested smoke test: run stage 1 on a minimal input and check that all stage-1 artifacts parse. The report is the fidelity record. Do not modify the HarnessSpec to hide target limitations.

## Principles

- **Preserve design intelligence, replace runtime bindings.** Procedures, verification intent, evidence standards and scope boundaries carry over; tools, paths and collaboration protocols are re-emitted in target conventions.
- **The artifact contract is the contract.** All communication between tasks and stages is files with documented JSON structure, never prose or messaging.
- **Determinism lives outside the LLM.** Stage sequencing and completion checks belong to the host; the agent controls only within-stage task order, which `AGENTS.md` pins.
- **One decision per concept.** Decide messaging, verification and model policy once (D2), then apply it everywhere.
- **Keep the change history alive.** Carry the design's change history into a `README.md` in the output directory so `evolve` can continue.
