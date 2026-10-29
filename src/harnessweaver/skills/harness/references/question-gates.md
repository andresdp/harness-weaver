# Question gates and the answers file

The `harness` skill asks the user before it writes target files. This file lists the decisions each gate must settle and how answers are recorded or replayed. The gate names and YAML keys are for the project; explain the choices to users in ordinary language.

## How to explain a gate

Keep the necessary questions. Make each one easy to answer without knowing HarnessWeaver terminology:

1. Ask only about decisions the sources and project instructions do not already settle.
2. State the decision in one sentence, then briefly say why it matters and what the choice changes.
3. Offer two or three concrete choices and a recommendation. Describe choices by their practical effect, not just by a field value or pattern name.
4. Explain technical words on first use. For example, call a JSON Schema a “machine-readable template that lets the runner check an output's structure.”
5. Show a proposed stage list, output table, or exact file list when that makes the choice easier to review. Do not ask users to invent these details from scratch.
6. If the user says “choose for me,” use the recommendation and record that it was the default. Do not turn an implementation detail into a question unless it changes workflow behavior, available runtimes, user effort, or review responsibility.

For example, instead of asking “Should Stage 4 include read-only artifact inputs?”, explain: “The decision-writing step refers to requirements and alternatives created earlier. Should it receive those earlier outputs as read-only context? **Recommended:** yes, so it can cite them without changing them. The trade-off is a larger context for that step.”

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

## Plain-language prompts for the gates

Use these as prompts to adapt to the user's case, not as a fixed questionnaire. Skip items answered by the source material or `harness-answers.yaml`.

| Gate | Explain it to the user this way |
|---|---|
| **G0 Intake** | “Which material should define the workflow, and are we starting from existing instructions or designing from a brief? For this multi-stage workflow, I recommend saving a reusable HarnessSpec—a file that records its stages, inputs, outputs, and checks. `saved_spec: true` means create that file; it does not mean that one already exists. Where should I put the generated files?” |
| **G1 Clarification** | Ask only about an unresolved point that changes the result. Show the source conflict or missing information, then explain the practical choices and recommend one. For example, say which earlier outputs a later stage would be allowed to read and why. |
| **G2 Design options** | Show two or three short workflow sketches. Explain the stage count, which work happens in order or at the same time, and the main trade-off. Recommend the option that best preserves the source method. |
| **G3 Artifact contracts** | “What should each step hand to the next one, and what must the final output contain?” Show an artifact table. Explain that a schema is a machine-readable template used to check output shape; reuse a supplied one when possible. |
| **G4 Target** | “Which kind of runnable assistant should I prepare?” Explain that Claude Code uses project instructions, skills, and agents, while DeepAgents uses configured stages with the HarnessWeaver host. Mention model-provider credentials only when they affect the choice or later run. |
| **G5 Target specifics** | Ask only choices that affect the user's run: which host executes the stages, whether the run should pause for approval, whether specialist subagents are needed, and how the model is configured. Explain each option's effect in the run; recommend defaults from the user's stated scope. |
| **G6 Write confirmation** | Show the exact target folders/files and summarize the important differences from the source workflow. Say plainly that confirming writes those files. Keep validation status and known limitations visible; do not ask the user to approve an unexplained file list. |

### Example: saved spec or one-off

This choice is easy to misunderstand. For a complex or evaluated workflow, explain that a saved HarnessSpec preserves the agreed design for checking and regenerating the assistant. A one-off skips that reusable design file and is appropriate only for a small, disposable task. Never describe `saved_spec: false` as “there is no existing spec” unless that is actually what the answer field means in context.

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
