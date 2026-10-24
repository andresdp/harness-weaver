# Question gates and the answers file

The `harness` skill asks the user before it writes files. This file lists the gates, what each must settle, and how answers are recorded or replayed.

## Gate discipline

- Ask the user directly in this conversation; never delegate a gate to a sub-agent.
- Batch related questions. Present concrete, reviewable material (a stage list, an artifact table, a skill skeleton) with 2–3 options and a recommendation.
- Resolve from evidence first. If the sources, the spec or existing files answer a question, say which file answered it and do not ask.
- Gates are mandatory for fresh builds. When extending an existing harness, gate only what the change touches.
- If the user is unavailable or says "just proceed", continue with the recommendation and record the answer as `unconfirmed`.
- Do not use a gate to offload a judgment the skill itself mandates, such as model tiering rules or verification patterns.

## Gates

| Gate | When | Must settle |
|---|---|---|
| **G0 Intake** | Before reading deeply | Which sources are authoritative (intent, methodology, domain). Whether to start from an existing spec, harness or application (harvest, see `intake-and-harvest.md`). Saved HarnessSpec or lightweight one-off. Where outputs go. |
| **G1 Clarification** | After domain analysis | Ambiguities in scope, terminology, input volume, and consumers of the outputs that the sources leave open. |
| **G2 Design options** | End of design | Stage boundaries; team shape and coordination pattern (see `team-patterns.md`); verification approach. If DeepAgents is a likely target, apply the design-time advice in `targets/deepagents.md`. |
| **G3 Artifact contracts** | Before writing any skill | Artifact names, top-level fields and ID linkage; reuse of supplied JSON Schemas. |
| **G4 Target** | After the HarnessSpec validates | **Claude Code, DeepAgents, or both.** Output directory per target (default `build/<target>/` next to the spec). |
| **G5 Target specifics** | Per selected target | *Claude Code:* allowed execution modes (sub-agents only, persistent agents, `Workflow`), model tiers. *DeepAgents:* model/provider, host (HarnessWeaver stage host or an existing application), human-in-the-loop points, whether subagents are allowed. |
| **G6 Write confirmation** | Before writing target files | Files to be written per target and the known approximated or unsupported mappings. |

## Recording answers

Write every gate question and its answer to `design-notes.md` next to the spec:

```markdown
## Gate answers
| Gate | Question | Answer | Source |
|---|---|---|---|
| G4 | Which runtime targets? | claude, deepagents | user (live) |
| G5 | DeepAgents host? | harnessweaver stage host | harness-answers.yaml |
| G2 | Coordination pattern? | sequential pipeline (recommended) | unconfirmed |
```

`Source` is one of `user (live)`, `harness-answers.yaml`, `evidence: <file>` or `unconfirmed`.

## The answers file

If the working directory contains `harness-answers.yaml`, read it first. Take any answer it provides, ask only the gates it leaves open, and record each answer's source as above. This lets a pilot be generated interactively once and replayed later, for example in a generation sandbox, with the same decisions.

```yaml
answers_version: "0.1"
G0:
  sources: sources/            # authoritative source directory
  start_from: none             # none | spec:<path> | harvest:<path>
  saved_spec: true
  output_root: generated/
G1: {}                         # free-form clarifications: {question: answer}
G2:
  coordination: sequential_pipeline
G3:
  contracts: use-supplied      # use-supplied | propose
G4:
  targets: [claude, deepagents]
G5:
  claude: {execution_modes: [subagents], models: default-tiering}
  deepagents: {host: harnessweaver, model: "openai:gpt-5.4-mini", hitl: none, subagents: false}
G6:
  confirm: true                # false = stop after showing the plan
```

An answer the file gives but the evidence contradicts is a conflict. Report it and ask; do not silently pick one.
