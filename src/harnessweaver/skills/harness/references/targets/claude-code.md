# Target: Claude Code project

Read this file when gate G4 selects **Claude Code**. It turns a validated HarnessSpec (or a recorded lightweight brief) into a Claude Code project: `.claude/agents/`, `.claude/skills/` (domain skills plus one orchestrator skill), and a `CLAUDE.md` pointer. "Project" below means the **target output directory** chosen at G4 (default `build/claude/` next to the spec; the user's own repository when they build a harness in place).

Inputs: the spec, `design-notes.md` (gate answers), the domain skills and contracts it references. Outputs: the project files plus `materialization-report.md` (see `../materialization-report.md`). Copy domain skills from their source paths rather than rewriting them; adapt only paths, frontmatter, and collaboration sections, and record each adaptation in the report.

## Contents

- Execution modes in Claude Code
- Step C1: Write agent definitions
- Step C2: Write skills
- Step C3: Integrate and define the execution order (orchestrator, data passing, errors, scale, `CLAUDE.md`)
- Step C4: Validate and test
- Step C5: Operate and maintain
- Claude Code checklist

## Execution modes in Claude Code

Gate G5 asks which of these modes the user allows. Recommend from the spec's stages and the design options chosen at G2.


Harness v2 uses three Claude Code multi-agent capabilities. Pick one of the following modes to match the workflow.

| Execution mode | Capabilities used | Suited work |
| --- | --- | --- |
| **Workflow orchestration** | `Workflow` script's `agent()`, `pipeline()`, `parallel()`, `phase()` | Work where the item list, verification procedure, and iteration count can be defined in code. Work that needs schema-conforming results or dozens or more `Agent` calls |
| **Persistent agent collaboration** | `Agent(name:)`, `SendMessage`, `TaskCreate`, `TaskUpdate` | Work where named specialists must iterate on feedback, negotiation, and co-editing while keeping conversational context |
| **Sub-agent delegation** | A single `Agent` call; runs in the background by default, parallel calls possible | Work where agents don't need to talk to each other and you only need the result once |

Decide in this order:

1. If the item list, verification criteria, and loop conditions can be expressed in code up front, use a workflow. Don't leave a fixed flow to the model's in-the-moment judgment if you want reruns to behave the same way.
2. If it's hard to define in code and agents must converse or remember earlier context, use persistent agents.
3. If neither applies and you only need the result, delegate to sub-agents.
4. If the nature of the work differs per phase, compose a hybrid mode. Note each phase's execution mode in the orchestrator.

Using the `Workflow` tool requires explicit user consent. Consent is assumed if the user directly requested a workflow run or invoked an orchestrator skill that instructs `Workflow` calls. Keep the default execution to a few agents; scale up only when the user asks for a broad investigation with words like "thorough" or "exhaustive".

> For a comparison of execution modes, concurrency limits, schemas, token budgets, and resume conditions, see `references/execution-modes.md`.

## Step C1: Write agent definitions

Specialized agents to be reused across sessions are defined as `project/.claude/agents/{name}.md` files. Don't put repeatedly used roles directly in the `Agent` tool's `prompt` only.

- Only by defining them as files can they be reused in later sessions. Invoke them with `subagent_type: "{name}"` from the `Agent` tool, or `agentType: "{name}"` from `Workflow`.
- Predefine what agents will exchange so collaboration results are stable.
- Agents describe *who* does the work; skills describe *how* it's done — don't mix the two.

Create reusable specialist roles as custom types in files, and specify that file's name in `subagent_type` or `agentType` when invoking. Don't create separate definition files for one-off tasks that use built-in types like `general-purpose`, `Explore`, or `Plan` as-is.

### Check for overlap with existing agents

Before creating a new agent file, check whether its role overlaps with existing agents in `project/.claude/agents/`. Don't skip this check even when adding just an agent while skipping step 1 — building or extending a harness multiple times can accumulate agents with the same role under different names. If it overlaps, don't create a new name; reuse or extend the existing agent. See the decision criteria and exceptions (intentional domain specialization) in the "Agent reuse design" section of `../team-patterns.md`.

### Model selection criteria

Choose a model per agent based on the work's complexity, duration, autonomy, and response-speed needs. Specify it in the YAML frontmatter `model:` or in the invocation arguments `model` / `opts.model`, and record the rationale as a comment in the agent definition or the orchestrator.

| Model | Selection criteria | Representative work |
| --- | --- | --- |
| **fable** | The hardest work that must plan on its own, chain multiple steps, and run autonomously over a long period | Agent coordination, planning and long-horizon execution, synthesizing vast material, concretizing vague ideas |
| **opus** | Specialized work with a clear scope but requiring deep reasoning and analysis | Design/architecture, code generation, complex analysis, cross-verification, research-method critique, creative writing |
| **sonnet** | Routine work with clear procedures where fast turnaround matters | Log analysis, format conversion, static file inspection, running deploy scripts, simple collection, general writing and summarization |

- If the work must run autonomously over a long period while adapting the next plan to earlier results, use fable. To deeply analyze one well-scoped problem, use opus. For example, critiquing a single paper in depth suits opus; reviewing dozens of papers to produce a strategy and report suits fable.
- Default to sonnet for ambiguous general work.
- Don't assign everything fable or opus just because the agent is "important". Choose the model by the actual work profile, not the agent's status.
- Even if the top-level planning/coordination agent uses fable, pick each worker's model separately to match its own work.

> Detailed per-model criteria are in `../model-selection-guide.md`.

### What goes into a definition file

The YAML frontmatter must include `name` and `description`. Optionally add `tools` to restrict available tools and `model` to change the model. For read-only review/analysis agents, remove Edit and Write from `tools` so they cannot modify files.

Conversely, give Edit along with Write to agents that fix artifacts. Without Edit, even a one-line fix requires rewriting the whole file, so on large artifacts the agent gives up on edits and works around them. Also, since there are cases where tools listed in `tools` aren't actually granted at runtime, have persistent agents report the list of tools actually available in their first message.

The body must state the core role, working principles, input/output rules, error handling, and collaboration methods. For persistent agents, add a `## Communication rules` section defining `SendMessage` counterparts and shared task-list usage.

> Definition templates, full examples, and cautions on restricting `tools` are in the "Agent definition structure" section of `../team-patterns.md`.

### When including a QA agent

- Give the QA agent a type that can use all verification tools. `Explore` is read-only and cannot run verification scripts.
- Don't just check file existence. Compare API responses against the frontend hook response structures.
- Don't verify only once at the very end. Verify as soon as each module is completed.
- Follow the details in `../qa-agent-guide.md`.

## Step C2: Write skills

Create each agent's skill at `project/.claude/skills/{name}/SKILL.md`. Follow `../skill-writing-guide.md` for the detailed method.

### C2.0 Check for overlap with existing skills

Before creating a new skill, check whether its function overlaps with existing skills in `project/.claude/skills/`. If it overlaps, don't create a new name; wire or extend the existing skill to the agent. See the decision criteria and exceptions (intentional domain specialization), and how far to generalize, in the "Skill reuse design" section of `../skill-writing-guide.md`.

### C2.1 Directory structure

```
skill-name/
├── SKILL.md              # required
│   ├── YAML frontmatter  # name and description required
│   └── Markdown body
├── scripts/              # optional: executable code for repeated work or work that must
│                         # always produce identical results
├── references/           # optional: reference documents read on demand
└── assets/               # optional: files used in artifacts, like templates and images
```

### C2.2 Write trigger conditions into the description

Claude decides which skill to load by looking at the skill's `name` and `description`. The `description` should state specifically what the skill does and when it must be used, and also distinguish lookalike cases where it must not be used.

**Bad example:** `"A skill that processes PDF documents"`

**Good example:** `"Performs PDF work: reading PDF files, extracting text and tables, merging, splitting, rotating, watermarking, encryption, OCR. MUST be used whenever the user mentions a .pdf file or requests a PDF artifact."`

### C2.3 Body writing principles

| Principle | How to apply |
| --- | --- |
| **Explain the why** | Don't just list `ALWAYS`/`NEVER`; explain why the rule exists. Knowing the reason leads to correct judgment in exceptional situations. |
| **Stay concise** | Keep `SKILL.md` under 500 lines. Delete content that doesn't aid judgment, or move it to ``. |
| **Generalize into principles** | Don't create rules that fit only a specific example. Write judgment criteria that apply across many inputs. |
| **Pre-place repeated code** | If multiple agents would rewrite the same script during testing, put it in `scripts/`. |
| **Write as directives** | Pick one imperative style and use it consistently throughout the document. The required actions must be unmistakable. |

### C2.4 Load information progressively, only what's needed

A skill loads its information and executable code at the following points in time.

| Information | When it's loaded | Recommended size |
| --- | --- | --- |
| **Metadata** (`name`, `description`) | Always | ~100 words |
| **`SKILL.md` body** | When the skill is invoked | Under 500 lines |
| **``** | When the material is needed | Unlimited |
| **`scripts/`** | When running repeated work or work that must always produce identical results | Unlimited; can be executed directly without reading |

- As `SKILL.md` approaches 500 lines, move details into `` and note in the body when to read which file.
- If a reference document exceeds 300 lines, add a table of contents near the top.
- If guidance differs per domain or framework, split reference documents so only the needed file is read.

### C2.5 Wiring agents and skills

- One agent can use one or more skills.
- Multiple agents can share the same skill.
- Skills describe how the work is done; agents carry the role responsible for that work.

## Step C3: Integrate and define the execution order

The orchestrator is also a skill. It binds individual agents and skills into one workflow and defines who collaborates, when, and in what order. Full per-mode templates are in `../orchestrator-template.md`, and workflow script examples are in `../workflow-recipes.md`.

When extending an existing harness, don't create a new orchestrator; edit the existing file. When adding agents, reflect that in the composition, task assignment, and data-passing order, and add the new trigger conditions to the `description`.

### C3.0 Orchestrators per execution mode

**A. Workflow orchestration**

Define a `Workflow` script in the orchestrator skill. The script consists of `meta`, `phase()`, `pipeline()`, `parallel()`, and `agent()`. Specify custom types with `agentType`, and receive schema-conforming results via `schema`.

```
[orchestrator skill] → Workflow(script)
    ├── phase('collect'): pipeline(items, ...)   ← fan out a pre-defined list
    ├── phase('verify'): adversarial verification or judge panel
    └── return structured results → main writes the synthesis report
```

**B. Persistent agent collaboration**

Spawn named agents, then coordinate via a shared task list and `SendMessage`. `TeamCreate` and `TeamDelete` no longer exist. No explicit team object is created; agents spawned with names in a session automatically belong to the single collaboration group that forms. You can message those agents again while they retain prior conversational context.

```
[main agent (leader)]
    ├── Agent(name: "researcher", ...) / Agent(name: "critic", ...)  ← run in parallel
    ├── TaskCreate(tasks + dependencies)
    ├── SendMessage({to: "critic"}, "review researcher's draft")
    └── collect and synthesize results
```

**C. Sub-agent delegation**

Call the `Agent` tool N times in parallel within one message and collect results from the completion notifications. Invoked agents run in the background by default.

If the nature of the work differs per phase, you can compose a hybrid mode. For example, collect material with a workflow and have persistent agents negotiate the synthesis, or adversarially verify persistent agents' output with a workflow. Label each phase with `**Execution mode:**`.

### C3.1 Data-passing methods

| Method | Implementation | Suited execution mode | When to use |
| --- | --- | --- | --- |
| **Structured return value** | `Workflow`'s `agent(prompt, {schema})` returns validated JSON | Workflow orchestration | When the next stage must process the result in code |
| **Plain return value** | The `Agent` tool's return message | Sub-agents | When the main agent collects summary results directly |
| **Messages** | Direct agent-to-agent transfer via `SendMessage` | Persistent agents | When real-time coordination and feedback are needed |
| **Shared task list** | State sharing via `TaskCreate`, `TaskUpdate` | Persistent agents | When managing progress, dependencies, dynamic assignment |
| **Files** | Write to and read from predetermined paths | All modes | When data is large or the work process must be reviewable later |

Follow these rules when passing data through files.

- Store intermediate artifacts under `_workspace/` in the working directory.
- Use filenames of the form `{phase}_{agent}_{artifact}.{ext}`. E.g., `01_analyst_requirements.md`
- Store only the final artifacts at the user-specified path. Keep `_workspace/` for post-hoc verification.

### C3.2 Error handling

Put an error-handling policy in the orchestrator.

- Retry once; if it fails again, proceed without that result but record the gap in the final report. Don't delete conflicting data — keep it with provenance.
- However, don't retry failures that will end the same way, such as exhausted usage limits, expired authentication, or denied permissions — retrying just burns the remaining quota. Open the partial artifacts yourself to see how far it actually got, record the missing content in a file, and report to the user. For usage limits, also tell the user when the limit resets.
- When the orchestrator fills a gap left by a stalled agent, substitute only facts you verified yourself. Never guess the agent's judgment calls (e.g., which material it excluded and why). Filling gaps with guesses amounts to forging the records needed for post-hoc verification.
- In workflows, a failed or skipped `agent()` returns `null`, and `parallel()` doesn't throw on failure. Apply `.filter(Boolean)` to result arrays and report the missing-item count via `log()`.
- If a persistent agent doesn't respond, check its status with `SendMessage` and re-instruct it. If it still fails, spawn the same custom type under a new name and pass the necessary task context in the prompt.

> For error-type-specific responses, see the "Error handling" section of the relevant execution-mode template in `../orchestrator-template.md`.

### C3.3 Job scale

| Job scale | Persistent agents | Workflow `Agent` call scale |
| --- | --- | --- |
| Small: under 10 tasks | 2–3 agents | 2–5 calls |
| Medium: 10–20 tasks | 3–5 agents | ~10 calls; waits automatically past the concurrency limit |
| Large: over 20 tasks | Supervisor + 3–5 workers | Dozens to hundreds of calls; overall cap 1,000 |

- More agents means more coordination overhead. Keep the default scale small.
- If the user specifies a token budget like `+500k`, the workflow script checks `budget.remaining()` to scale execution accordingly.

### C3.4 Record harness wiring in `CLAUDE.md`

When configuration is done, record in the project's `CLAUDE.md` that a harness exists, along with its trigger conditions. `CLAUDE.md` is read every new session, so don't repeat detailed execution rules there.

````markdown
## Harness: {domain name}

**Goal:** {one line describing the harness's core objective}

**Trigger conditions:** When asked to do work related to {domain}, use the `{orchestrator-skill-name}` skill. Simple questions may be answered directly.

**Change history:**
| Date | Change | Target | Reason |
| --- | --- | --- | --- |
| {YYYY-MM-DD} | First configured with Harness v2 | All | - |
````

Don't include agent/skill lists, directory structures, or detailed execution rules. That information is managed by the orchestrator skill and `.claude/agents/`, `.claude/skills/`. Keep only trigger conditions and the change history in `CLAUDE.md`.

### C3.5 Handling follow-up requests

The orchestrator must work not only on first run but also when results need rework.

1. Include phrases like `run again`, `re-run`, `update`, `fix`, `revise`, `redo only the {sub-task} of {domain}`, `based on the previous results`, and `improve the results` in the `description`.
2. In the orchestrator's step 0, check the existing task context.
   - If `_workspace/` exists and only part needs fixing, re-run only the relevant phase or agent.
   - If `_workspace/` exists and new input arrived, move the existing directory to a timestamped one and run fresh.
   - If `_workspace/` doesn't exist, run from scratch.
   - If the workflow's previous `runId` is available, you can resume with `resumeFromRunId`. Unchanged `agent()` calls reuse cached results.
3. Write re-invocation instructions in agent definitions. If previous result files exist, read them; if the user gave feedback, fix only the relevant parts.

## Step C4: Validate and test

Validate the generated harness. Follow `../skill-testing-guide.md` for details.

For a saved HarnessSpec, validate the spec before relying on it to generate runtime files. Keep validation results separate from task-quality results: a valid spec does not prove that the generated harness works.

### C4.1 File and reference validation

- Confirm every agent file is in the right location.
- Confirm each skill's YAML frontmatter has `name` and `description`.
- Confirm the names agents use to reference each other are consistent.
- Confirm no command files were created in `.claude/commands/`.
- Confirm no v1-style `TeamCreate`, `TeamDelete`, `team_name`, or experimental flags remain in the artifacts.

### C4.2 Per-mode validation

- **Workflow orchestration**: confirm `meta` is a literal containing only values, no `Date.now()`/`Math.random()` usage, `parallel()` used only when waiting for all results, `.filter(Boolean)` not missing, and `phase()` titles match `meta.phases`.
- **Persistent agent collaboration**: check `SendMessage` send/receive paths, task dependencies, and agent counts.
- **Sub-agent delegation**: check that each agent's input and output connect, that parallel calls are batched into one message, and that all results are collected without gaps.
- **Hybrid mode**: check that each phase states its execution mode and that data doesn't break across phase boundaries.

### C4.3 Skill execution testing

1. For each skill, write 2–3 concrete test requests a real user might type.
2. Run with-skill and baseline executions in parallel and compare how much the skill improves results. If you need repetitions, you can even build the A/B comparison itself as a workflow.
3. Combine qualitative evaluation by direct user review with quantitative evaluation using assertions. If objective criteria can't be constructed, defer to user judgment.
4. When problems appear, don't add rules that block just one example; fix with principles that apply across situations. Re-test, and repeat until further fixes yield almost no gain.
5. If multiple agents keep recreating the same code, move it into `scripts/`.

### C4.4 Trigger-condition validation

1. Write 10 requests that should invoke the skill, in varied phrasings and levels of explicitness.
2. Write another 10 boundary cases that sound similar but should use a different skill or tool.

Obviously unrelated requests can't validate boundaries. For example, when testing an image-generation skill, `extract the charts in this Excel file as PNGs` is a better boundary case than `write a Fibonacci function` — the result is an image, but a spreadsheet tool is actually more appropriate. Also check whether trigger conditions overlap with existing skills.

### C4.5 Dry run

- Confirm the orchestrator's phase order is logical.
- Confirm data-passing paths don't break midway.
- Confirm every agent's input matches the previous phase's output.
- Confirm fallback procedures for errors can actually execute.

### C4.6 Record test scenarios

Add a `## Test scenarios` section to the orchestrator skill with at least one happy path and one error path.

## Step C5: Operate and maintain

A harness isn't a build-once artifact.

Retrospectives on execution results and applying feedback are handled by the `evolve` skill. When the user asks to `run a harness retrospective`, `evolve the harness`, or `apply feedback`, use `evolve`. That skill analyzes the difference between the initial configuration and the current state, generalizes the feedback so it applies across situations, and applies it to agents, skills, and orchestrators. It also updates the `CLAUDE.md` change history.

This `harness` skill directly handles the following procedures for operating and maintaining an existing harness.

1. **State check**: compare `.claude/agents/`, `.claude/skills/`, and the orchestrator configuration; produce a mismatch list and inform the user.
2. **Incremental changes**: change only one item at a time and immediately run the next validation.
3. **Record changes**: write the date, change, target, and reason into `CLAUDE.md`.
4. **Verify changes**: check file structure. If trigger conditions are affected, run trigger tests too. For large changes, also run execution tests and dry runs, then do a final check that `CLAUDE.md` matches the actual files.

Propose improving via `evolve` in the following situations.

- The same kind of feedback has come up twice or more.
- Agents repeatedly fail for the same root cause.
- The user keeps handling the same task manually, bypassing the orchestrator.

## Claude Code checklist

- [ ] Created files in `project/.claude/agents/` for every custom type to be reused, excluding one-off tasks that use built-in types as-is.
- [ ] Ran the clarification gate after domain analysis and the option gates before execution-mode selection and skill generation; user decisions (or "proceed unconfirmed") are recorded in the change history.
- [ ] Created the needed `SKILL.md` files and reference documents in `project/.claude/skills/`.
- [ ] A HarnessSpec is present for reusable or complex harnesses; any deliberate one-off without a saved spec has a stated reason.
- [ ] Saved specs pass the available validator, or the handoff clearly says validation was unavailable.
- [ ] Runtime outputs match the selected supported adapter, and unsupported or lossy mappings are disclosed.
- [ ] Included data-passing methods, error handling, and test scenarios in a single orchestrator skill.
- [ ] Stated which execution mode — workflow orchestration, persistent agents, or sub-agent delegation — is used; for hybrid modes, labeled each phase.
- [ ] Chose each agent's `model:` by complexity, duration, autonomy, and response speed, and recorded the rationale as comments. Did not blanket-pin every agent to the same high-end model.
- [ ] No v1-style `TeamCreate`, `TeamDelete`, or experimental flags remain in the artifacts.
- [ ] Included `.filter(Boolean)` in workflow scripts and used only literals in `meta`. Waits for all results via `parallel()` only when strictly necessary.
- [ ] Created no files in `.claude/commands/`.
- [ ] Checked new agents/skills for role overlap with existing ones before creating them. Unless intentionally domain-specialized, reused or extended overlapping ones, with no name or role conflicts.
- [ ] Wrote agent definitions, skills, the orchestrator, and `CLAUDE.md` entries in the language the user uses in conversation. Followed an explicitly specified language or the language of existing harness files when present.
- [ ] Wrote what the skill does and its trigger conditions specifically in the skill `description`, including follow-up request phrasings.
- [ ] Kept the `SKILL.md` body under 500 lines; moved details into `` beyond that.
- [ ] Ran it with 2–3 test sentences resembling real requests.
- [ ] Validated trigger conditions with requests that should invoke the skill and boundary cases that shouldn't.
- [ ] Recorded only trigger conditions and the change history in `CLAUDE.md`.
- [ ] The orchestrator's step 0 distinguishes first runs, follow-up runs, and partial re-runs. For workflows, it also handles the resume option.

- [ ] `materialization-report.md` lists every spec stage, role, artifact, verification, and human gate as mapped, approximated, or unsupported.
