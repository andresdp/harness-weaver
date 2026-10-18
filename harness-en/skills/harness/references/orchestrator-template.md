# Orchestrator Skill Templates (v2)

The orchestrator coordinates the whole team. Three templates are provided according to the execution mode, along with guidance on combining execution modes stage by stage.

- **Template A: Workflow orchestration** — large-scale fan-out or iterative verification with a control flow fixed in advance
- **Template B: Persistent agent collaboration** — iterative feedback, negotiation, and long-horizon collaboration where agents must retain prior conversation
- **Template C: Sub-agent delegation** — handing independent jobs to agents once each, in parallel, and collecting only the results
- **Mixed mode** — combining the execution mode that fits each stage

Every template checks for existing work in step 0. It must also include the `_workspace/` file layout rules, error handling, and test scenarios.

---

## Template A: Workflow orchestration

```markdown
---
name: {domain}-orchestrator
description: "Orchestrates the {domain} workflow. Use when the user requests one of {initial trigger keywords}; also use it for follow-up work such as revising {domain} results, partial re-runs, updates, additions, re-execution, or improving previous results."
---

# {Domain} Orchestrator

## Execution mode: Workflow orchestration

This skill uses the Workflow tool to coordinate work whose control flow is fixed in advance. When the user invokes this skill,
that counts as consent to use Workflow. Cap the default number of agents at {N}. Increase the agent count only when the user
asks for "thorough", "exhaustive", or "everything".

## Agent configuration

| Role | `agentType` | Skill | Artifact (`schema` summary) |
|------|-----------|------|--------------------|
| {collector} | {custom or default} | {skill} | {findings: [...]} |
| {verifier}  | {custom or default} | {skill} | {status, reason} |

In `{custom or default}`, write the name of a custom type or a built-in type.

## Procedure

### Step 0: Check for existing work (handle follow-up requests)

1. Check whether `_workspace/` exists.
   - Absent → run from scratch
   - Present, and the request is to fix only part → re-run only that part
   - Present, and new input was received → move the existing `_workspace/` to `_workspace_{ts}/` and start fresh
2. When re-running only part of the work, if the `runId` of the most recent run is in `_workspace/run_meta.json`, proceed as follows.
   - Edit only the affected stage in the script and resume with `resumeFromRunId`. `agent()` calls whose content is unchanged
     return cached results immediately, so the cost of re-running is small.
3. When starting fresh, receive a new `runId` and record it in `_workspace/run_meta.json`.

### Step 1: Finalize the task list (performed directly by the main agent)

Before starting the workflow, skim {file list / research axes / review targets} and organize them into an array.
Pass the organized list to the script as `args`.

### Step 2: Run the workflow

Pass the following script to the Workflow tool. See the harness skill's `workflow-recipes.md` for detailed examples.

- `meta`: `name` is '{domain}-run', `phases` is [{collect}, {verify}, {synthesize}]
- Collect: pipeline(args.items, item => agent(..., {schema: COLLECT}))
- Verify: adversarial verification for each discovered item → .filter(Boolean) → pass only verified items to the next stage
- Synthesize: return the structured results

After invoking it, wait for the completion notification. Do not presume results before the notification arrives.

### Step 3: Organize results and report

1. Take the value returned by the workflow.
2. If any items were excluded or dropped, always disclose them in the report.
3. Create the final artifact at `{output-path}/{filename}`.
4. Leave intermediate artifacts and `run_meta.json` in `_workspace/`.

## Error handling

| Situation | How to respond |
|------|------|
| An individual `agent()` fails (returns `null`) | Exclude it with `.filter(Boolean)` and log the number of excluded items with `log()`. Disclose the dropped items in the report as well. |
| The whole workflow fails | Inspect the actual return values in the `journal`, fix only the failed stage, and resume with `resumeFromRunId`. |
| Failures where retrying is futile (usage limit exhausted, expired authentication, permission denied) | Do not retry or resume until the cause clears, because doing so only burns the remaining quota. Open the `journal` and the partial artifacts directly to confirm exactly how far the work got, record the missing content as files under `_workspace/`, and report to the user. For a usage limit, also tell the user when it resets. Once the cause clears, you can continue the run with `resumeFromRunId`. The main agent incorporates only the facts it confirmed itself and never guesses at an agent's judgment (for example, which material was excluded and why). |
| The result is empty | Do not mistake it for success. Check each agent's actual return values in the `journal`. |
| Data that conflicts with itself | Do not delete it; write it down together with its sources. |

## Test scenarios

### Happy path
1. The user provides {input}, and pre-checking confirms {M} items.
2. The workflow collects {M} items, of which {K} pass verification, and the results are organized.
3. Expected outcome: `{output-path}/{filename}` is created and run information is recorded in `run_meta.json`.

### Error path
1. Two items return `null` in the collection stage.
2. Exclude those items with `.filter(Boolean)` and announce "2 items excluded" with `log()`.
3. Write "failed to collect 2 {item-name} items" in the final report.
```

---

## Template B: Persistent agent collaboration

```markdown
---
name: {domain}-orchestrator
description: "Coordinates the collaboration of {domain} agents. Use when the user requests one of {initial trigger keywords}; also use it for follow-up work such as revision, partial re-runs, updates, additions, re-execution, or improving previous results."
---

# {Domain} Orchestrator

## Execution mode: Persistent agent collaboration

Unlike v1, no explicit team object is created. Agents launched with names in the session belong to a single
collaboration group that forms automatically. TeamCreate and TeamDelete are tools used only in v1.

## Agent configuration

| Name | `subagent_type` | Role | Skill | Artifact |
|------|--------------|------|------|------|
| {teammate-1} | {custom or built-in} | {role} | {skill} | {output-file} |
| {teammate-2} | {custom or built-in} | {role} | {skill} | {output-file} |

In `{custom or built-in}`, write the name of a custom type or a built-in type.

## Procedure

### Step 0: Check for existing work
As in Template A, check whether `_workspace/` exists and decide whether to run for the first time, re-run only
part of the work, or start fresh. When re-running only part, put the previous artifact paths into the agent prompts
so the agents read and build on the existing results.

### Step 1: Preparation
1. Analyze the user's input and confirm {what to establish}.
2. Create `_workspace/` and store the input in `_workspace/00_input/`.

### Step 2: Launch agents and register tasks

1. Launch the agents in parallel within a single message. `name` is required and is used to address them in SendMessage.
   - Agent(name: "{teammate-1}", subagent_type: "{type}", prompt: "{role + task instructions + output path}")
   - Agent(name: "{teammate-2}", subagent_type: "{type}", prompt: "...")
2. Register the shared task list.
   - TaskCreate({title: "{task-1}", assignee: "{teammate-1}"})
   - TaskCreate({title: "{task-3}", depends_on: [task-1]})
   > Three to six tasks per teammate is about right. Make task dependencies explicit with `depends_on`.

### Step 3: Coordinating the collaboration

- Proceed while receiving completion and waiting notifications from teammates. Track overall progress with TaskList.
- Request review with SendMessage({to: "{teammate-2}"}, "Review the _workspace/01_... draft from {teammate-1}
  and tell them what to fix"), then relay the reply to {teammate-1} so they revise.
  Because agents retain prior conversation, you can narrow the scope with instructions like "only section 2 of that earlier draft."
- When teammates need to discuss findings with each other, the leader relays the messages. Always leave artifacts as files.

**Artifact storage locations:**

| Teammate | Output path |
|------|----------|
| {teammate-1} | `_workspace/{phase}_{teammate-1}_{artifact}.md` |
| {teammate-2} | `_workspace/{phase}_{teammate-2}_{artifact}.md` |

### Step 4: Freezing artifacts

Named agents keep receiving messages after they report completion. If a teammate modifies an artifact it already handed off while answering another teammate's late question, the next stage would read the pre-edit content. Cross-checking messages between teammates can catch errors, so do not block them. Instead, freeze the artifacts at every stage boundary so the files the next stage reads do not change midway.

1. Use TaskList and completion notifications to confirm that every teammate assigned to the previous stage has reported completion.
2. Notify those teammates of the freeze via SendMessage. Example: "The {stage} artifacts are now frozen. If something needs fixing later, do not edit the existing file; write a new version file such as `{phase}_{teammate}_{artifact}_v2.md` and tell the leader."
3. Record artifact hashes. Example: `shasum _workspace/{phase}_* > _workspace/freeze_{phase}.sha` (`md5sum` also works)
4. Pass both the artifact paths and the hash file path in the prompt of the agent handling the next stage.

If there are several collaboration stages, repeat this procedure at every stage boundary.

### Step 5: Integration
1. Confirm with TaskList that every task is finished.
2. Read each artifact with Read and apply {integration/verification logic}.
3. Just before producing the final artifact, recompute the hashes (for example, `shasum -c _workspace/freeze_{phase}.sha`) to confirm the frozen artifacts have not changed. If a hash differs or a new version file has appeared, find out what changed and decide whether to re-run the stages that read the pre-edit content.
4. Create the final artifact at `{output-path}/{filename}`.

### Step 6: Wrap-up
1. Keep `_workspace/` so the work can be verified and its process inspected later.
2. Summarize the results and report to the user.
   There is no team-disbanding procedure. Agents end automatically when their work is done; stop them with TaskStop if needed.

## Error handling

| Situation | How to respond |
|------|------|
| A teammate does not respond or has stopped | Check its status with SendMessage and re-instruct it. If that still fails, launch the same custom type under a new name and pass the necessary task context in the prompt. |
| The stop was caused by an exhausted usage limit, expired authentication, or permission denial | Retrying yields the same outcome, so do not re-instruct or launch a replacement agent. Open the partial artifacts directly to confirm exactly how far the work got, record the missing content as files under `_workspace/`, and report to the user. For a usage limit, also tell the user when it resets. The leader incorporates only the facts it confirmed itself and never guesses at an agent's judgment (for example, which material was excluded and why). |
| More than half of the teammates fail | Notify the user and confirm whether to continue. |
| The time limit is exceeded | Proceed with the results received so far and disclose the unfinished areas in the report. |
| Data conflicts with itself | Do not delete it; write the versions side by side with their sources. |
| Task status lags behind reality | Check with TaskList and update directly with TaskUpdate. |

## Test scenarios

### Happy path
1. The user provides {input}; step 2 launches {N} agents and registers {M} tasks.
2. Step 3 exchanges {K} rounds of feedback, step 4 freezes the artifacts, and step 5 integrates the results.
3. Expected outcome: `{output-path}/{filename}` is created.

### Error path
1. In step 3, {teammate-2} does not respond.
2. Check its status with SendMessage and re-instruct it. If that still fails, launch a replacement agent named "{teammate-2}b" and pass it the existing artifact paths.
3. Write "partial rework of the {teammate-2} area" in the final report.
```

---

## Template C: Sub-agent delegation

```markdown
---
name: {domain}-orchestrator
description: "Delegates independent {domain} tasks to sub-agents. Use when the user requests one of {initial trigger keywords}; also use it for follow-up work such as revising results, partial re-runs, updates, additions, re-execution, or improving previous results."
---

## Execution mode: Sub-agent delegation

## Procedure

### Step 0: Check for existing work
Check whether `_workspace/` exists and decide whether to run for the first time, re-run only part of the work, or start fresh.

### Step 1: Preparation
Analyze the input and create `_workspace/`.

### Step 2: Parallel execution
Invoke the Agent tool N times simultaneously in a single message. It runs in the background by default.

| Agent | `subagent_type` | Input | Artifact |
|---------|--------------|------|------|
| {agent-1} | {type} | {source} | `_workspace/{phase}_{agent}_{artifact}.md` |
| {agent-2} | {type} | {source} | `_workspace/{phase}_{agent}_{artifact}.md` |

In `{type}`, write the name of a custom type or a built-in type.

Wait for the completion notifications. The main agent does not repeat a search it has already delegated.

### Step 3: Integration
1. Gather the return values and file artifacts, integrate them, and produce the final artifact.

### Step 4: Wrap-up
Keep `_workspace/` and summarize the results for the user.

## Error handling
- If one agent fails, retry it once. If it fails again, disclose the gap and continue.
- For failures where retrying yields the same outcome — exhausted usage limits, expired authentication, permission denial — do not retry. Open the partial artifacts directly to confirm exactly how far the work got, record the missing content as files under `_workspace/`, and report to the user. For a usage limit, also tell the user when it resets. The main agent incorporates only the facts it confirmed itself and never guesses at an agent's judgment.
- If more than half of the agents fail, notify the user and confirm whether to continue.
```

---

## Combining execution modes per stage (mixed mode)

Use the execution mode that fits each stage. Write `**Execution mode:**` at the top of each stage.

```markdown
## Execution mode: Mixed

| Stage | Execution mode | Why |
|------|----------|-----------|
| Stage 1 (pre-check) | Done directly by the main agent, or delegated to a sub-agent | The task list must be finalized. |
| Stage 2 (bulk collection and verification) | Workflow orchestration | A pre-fixed list must be processed in a distributed fashion with adversarial verification. |
| Stage 3 (consensus and integration) | Persistent agent collaboration | Conflicting data must be discussed and reconciled. |
| Stage 4 (independent verification) | Sub-agent delegation | One quality-verification agent verifying independently is enough. |
```

**Rules for switching execution modes:**
- Workflow orchestration → persistent agent collaboration: save the structured data returned by the workflow to `_workspace/`, and put the file paths in the persistent agents' prompts.
- Persistent agent collaboration → workflow orchestration: freeze the team's artifacts (step 4 of Template B), then pass the list of file paths to the script as `args`.
- At every point where the execution mode changes, write down how data is handed over, so no stage is left unable to find the previous stage's results.

---

## Writing principles that apply to every template

1. **State the execution mode at the top of the document.** In mixed mode, summarize the per-stage execution modes in a table.
2. **In workflow orchestration mode, spell out the script structure in detail.** Enumerate `phases`, the `schema` summaries, and everything that goes into `args` without omission.
3. **In persistent agent collaboration mode, spell out how `name`, SendMessage, and TaskCreate are used.** Include the list of agents to launch, the communication rules, task dependencies, and the artifact-freeze procedure at stage boundaries.
4. **In sub-agent delegation mode, list every Agent parameter.** State whether it is a one-shot invocation without `name`, and specify `subagent_type`, `prompt`, and the output path.
5. **Write file paths explicitly.** Base paths on `_workspace/` and follow the `{phase}_{agent}_{artifact}.{ext}` naming rule.
6. **Make dependencies between stages explicit.** At points where the execution mode changes, describe in particular detail how data flows across.
7. **Plan for errors that can actually happen.** Do not assume every job succeeds; define how to handle each situation.
8. **Always include test scenarios.** Write at least one happy-path scenario and one error-path scenario.
9. **Do not include v1-only elements.** If TeamCreate, TeamDelete, `team_name`, broadcast sends, or the experimental flag are referenced, the template was written incorrectly.

## Follow-up request phrasing to include in `description`

Include the following phrases so the skill is selected not only on first run but also when results are revised or re-run.

- re-run, run again, update, revise, supplement
- "only the {part} of {domain}, again"
- "based on the previous results", "improve the results"
- request phrasing commonly used in the domain (for example, for a launch-strategy harness: "launch", "promotion", "trending")

Without follow-up request phrasing, this harness may not be selected again after the first run.
