# Orchestrator Skill Templates (v2)

The orchestrator coordinates the whole team. Three templates are provided according to execution mode, along with how to combine execution modes per phase.

- **Template A: Workflow coordination** — large-scale distributed execution or repeated verification whose control flow is fixed in advance
- **Template B: Persistent agent collaboration** — repeated feedback, negotiation, and long-term collaboration where agents must keep earlier conversation content
- **Template C: Sub-agent delegation** — delegate independent tasks once each in parallel and collect only the results
- **Hybrid mode** — combine suitable execution modes per phase

Every template checks existing work in step 0. The `_workspace/` file organization rules, error-handling methods, and test scenarios must also always be included.

---

## Template A: Workflow coordination

```markdown
---
name: {domain}-orchestrator
description: "Coordinates the {domain} workflow. Use when the user requests with one of {initial run keywords}, and also for follow-up work such as fixing {domain} results, partial re-runs, updates, supplements, running again, and improving previous results."
---

# {Domain} Orchestrator

## Execution mode: Workflow coordination

This skill uses the Workflow tool to coordinate work whose control flow is fixed in advance. When the user
loads this skill, consider consent to use Workflow given. Limit the default number of agents to {N}. Increase
the number of agents only if the user asked for "thoroughly", "exhaustively", or "all".

## Agent composition

| Role | `agentType` | Skill | Output (`schema` summary) |
|------|-----------|------|--------------------|
| {collector} | {custom or built-in} | {skill} | {findings: [...]} |
| {verifier}  | {custom or built-in} | {skill} | {status, reason} |

In `{custom or built-in}`, write the name of a custom type or a built-in type.

## Work procedure

### Step 0: Check existing work (handling follow-up requests)

1. Check whether `_workspace/` exists.
   - If not → run from the beginning
   - If it exists and the request is to fix only part → re-run only that part
   - If it exists and new input was received → move the existing `_workspace/` to `_workspace_{ts}/` and run fresh
2. If re-running only part and the previous run's `runId` is in `_workspace/run_meta.json`, handle it as follows.
   - Modify only that phase in the script, then resume with `resumeFromRunId`. `agent()` calls whose content didn't change
     return cached results immediately, so the execution cost is low.
3. When running fresh, get a new `runId` and record it in `_workspace/run_meta.json`.

### Step 1: Finalize the task list (performed directly by the main agent)

Before starting the workflow, briefly look over {the file list / investigation axes / review targets}, then organize them into an array.
Pass the organized list to the script via `args`.

### Step 2: Run the workflow

Pass the following script to the Workflow tool. See `workflow-recipes.md` of the harness skill for detailed examples.

- `meta`: `name` is '{domain}-run', `phases` is [{collect}, {verify}, {synthesize}]
- Collect: pipeline(args.items, item => agent(..., {schema: COLLECT}))
- Verify: adversarial verification for each found item → .filter(Boolean) → pass only items that passed verification to the next phase
- Synthesize: return the structured results

After calling, wait for the completion notification. Don't presume the result before receiving the notification.

### Step 3: Organize and report results

1. Receive the value returned by the workflow.
2. If items were excluded or missing, always state it in the report.
3. Create the final output at `{output-path}/{filename}`.
4. Keep the intermediate outputs and `run_meta.json` in `_workspace/`.

## Error handling

| Situation | Response |
|------|------|
| Individual `agent()` failure (returns `null`) | Exclude it with `.filter(Boolean)` and record the number of excluded items with `log()`. Also state the missing items in the report. |
| Whole workflow failure | Check the actual return values in `journal`, then fix only the failed phase and resume with `resumeFromRunId`. |
| Failures that retrying won't help (exhausted usage limit, expired authentication, denied permission) | Don't retry or resume before the cause is resolved, because it only uses up the remaining limit. Open `journal` and the partial outputs directly to check how far the work actually got, record the missing content as a file in `_workspace/`, and report to the user. For usage limits, also tell when it resets. After the cause is resolved, execution can continue with `resumeFromRunId`. The main agent reflects only facts it checked directly, and doesn't guess and fill in the agents' judgments (e.g., which material was excluded and why). |
| Empty results | Don't mistake it for success. Check each agent's actual return value in `journal`. |
| Conflicting data | Don't delete it; write it down with its source. |

## Test scenarios

### Normal flow
1. When the user provides {input}, the pre-check finalizes {M} items.
2. The workflow collects {M} items, and when {K} of them pass verification, the results are organized.
3. Expected result: `{output-path}/{filename}` is created and execution information is recorded in `run_meta.json`.

### Error flow
1. Two items return `null` in the collection phase.
2. They are excluded with `.filter(Boolean)` and "2 excluded" is reported with `log()`.
3. The final report says "{item name}: 2 failed to collect".
```

---

## Template B: Persistent agent collaboration

```markdown
---
name: {domain}-orchestrator
description: "Coordinates the collaboration of {domain} agents. Use when the user requests with one of {initial run keywords}, and also for follow-up work such as fixes, partial re-runs, updates, supplements, running again, and improving previous results."
---

# {Domain} Orchestrator

## Execution mode: Persistent agent collaboration

Don't create an explicit team object as in v1. Agents run with names in a session automatically belong to
the single collaboration group that forms. TeamCreate and TeamDelete were tools used only in v1.

## Agent composition

| Name | `subagent_type` | Role | Skill | Output |
|------|--------------|------|------|------|
| {teammate-1} | {custom or built-in} | {role} | {skill} | {output-file} |
| {teammate-2} | {custom or built-in} | {role} | {skill} | {output-file} |

In `{custom or built-in}`, write the name of a custom type or a built-in type.

## Work procedure

### Step 0: Check existing work
As in template A, check whether `_workspace/` exists to decide whether to run for the first time, re-run only part,
or run fresh. If re-running only part, put the previous output paths in the agent prompts so they
read and reflect the existing results.

### Step 1: Preparation
1. Analyze the user input to determine {what to identify}.
2. Create `_workspace/` and save the input in `_workspace/00_input/`.

### Step 2: Run agents and register tasks

1. Run the agents in parallel in one message. `name` is required and is used to specify the target in SendMessage.
   - Agent(name: "{teammate-1}", subagent_type: "{type}", prompt: "{role + work instructions + output path}")
   - Agent(name: "{teammate-2}", subagent_type: "{type}", prompt: "...")
2. Register the shared task list.
   - TaskCreate({title: "{task1}", assignee: "{teammate-1}"})
   - TaskCreate({title: "{task3}", depends_on: [task1]})
   > 3–6 tasks per teammate is appropriate. Specify dependencies between tasks with `depends_on`.

### Step 3: Coordinate the collaboration

- Proceed while receiving teammates' task-completion and idle notifications. Check overall progress with TaskList.
- Request a review with SendMessage({to: "{teammate-2}"}, "Review {teammate-1}'s draft in _workspace/01_...
  and tell me what to fix"). Forward the answer to {teammate-1} to revise.
  Since agents keep earlier conversation content, instructions can be narrowed in scope, such as "only section 2 of that draft from before".
- If teammates need to discuss what they found, the leader relays the messages. Always leave outputs as files.

**Output locations:**

| Teammate | Output path |
|------|----------|
| {teammate-1} | `_workspace/{phase}_{teammate-1}_{artifact}.md` |
| {teammate-2} | `_workspace/{phase}_{teammate-2}_{artifact}.md` |

### Step 4: Freeze outputs

Named agents receive messages even after reporting completion. If, while answering another teammate's late question, one modifies an output already handed over, the next phase ends up reading and working on the content from before the change. Messages in which teammates cross-check each other can catch errors, so don't block them. Instead, freeze the outputs every time a phase is handed over, so that the files the next phase reads don't change midway.

1. Use TaskList and completion notifications to check that every teammate responsible for the previous phase has reported completion.
2. Notify those teammates of the freeze with SendMessage. Example: "Freezing the {phase} outputs. If something needs fixing afterward, don't modify the existing file; write a new version file such as `{phase}_{teammate}_{artifact}_v2.md` and notify the leader."
3. Record the output hashes. Example: `shasum _workspace/{phase}_* > _workspace/freeze_{phase}.sha` (`md5sum` may also be used)
4. Pass the output paths together with the hash file path in the prompts of the agents responsible for the next phase.

If there are several collaboration phases, follow the same procedure at every phase boundary.

### Step 5: Integration
1. Check with TaskList that all tasks have finished.
2. Read each output with Read and apply {integration/verification logic}.
3. Right before creating the final output, recompute the hashes, such as `shasum -c _workspace/freeze_{phase}.sha`, to check that the frozen outputs haven't changed. If a hash differs or a new version file appeared, check what changed and decide whether to re-run the phases that read the content from before the change.
4. Create the final output at `{output-path}/{filename}`.

### Step 6: Wrap-up
1. Keep `_workspace/` so the work can be verified and the work process checked later.
2. Report a summary of the results to the user.
   There is no procedure to disband the team. Agents end automatically when their work is done; if needed, stop them with TaskStop.

## Error handling

| Situation | Response |
|------|------|
| A teammate doesn't respond or has stopped | Check its status with SendMessage and instruct again. If it still fails, run the same custom type under a new name and pass the needed work context in the prompt. |
| The cause of stopping is an exhausted usage limit, expired authentication, or denied permission | Retrying gives the same result, so don't instruct again or run a substitute agent. Open the partial outputs directly to check how far the work actually got, record the missing content as a file in `_workspace/`, and report to the user. For usage limits, also tell when it resets. The leader reflects only facts it checked directly, and doesn't guess and fill in the agents' judgments (e.g., which material was excluded and why). |
| More than half of the teammates failed | Inform the user and confirm whether to continue. |
| The time limit was exceeded | Proceed with the results received so far, and state the unfinished areas in the report. |
| Data conflicts | Don't delete it; write it side by side with its sources. |
| Task status was reflected late | Check with TaskList, then update it directly with TaskUpdate. |

## Test scenarios

### Normal flow
1. When the user provides {input}, step 2 runs {N} agents and registers {M} tasks.
2. Step 3 exchanges feedback {K} times, step 4 freezes the outputs, and step 5 integrates the results.
3. Expected result: `{output-path}/{filename}` is created.

### Error flow
1. In step 3, {teammate-2} doesn't respond.
2. Check its status with SendMessage and instruct again. If it still fails, run a substitute agent named "{teammate-2}b" and pass the existing output paths.
3. The final report says "part of the {teammate-2} area reworked".
```

---

## Template C: Sub-agent delegation

```markdown
---
name: {domain}-orchestrator
description: "Delegates independent {domain} tasks to sub-agents. Use when the user requests with one of {initial run keywords}, and also for follow-up work such as fixing results, partial re-runs, updates, supplements, running again, and improving previous results."
---

## Execution mode: Sub-agent delegation

## Work procedure

### Step 0: Check existing work
Check whether `_workspace/` exists to decide whether to run for the first time, re-run only part, or run fresh.

### Step 1: Preparation
Analyze the input and create `_workspace/`.

### Step 2: Parallel execution
Call the Agent tool N times concurrently in one message. They run in the background by default.

| Agent | `subagent_type` | Input | Output |
|---------|--------------|------|------|
| {agent-1} | {type} | {source} | `_workspace/{phase}_{agent}_{artifact}.md` |
| {agent-2} | {type} | {source} | `_workspace/{phase}_{agent}_{artifact}.md` |

In `{type}`, write the name of a custom type or a built-in type.

Wait for the completion notifications. The main agent doesn't redo searches it has already delegated.

### Step 3: Integration
1. Collect and integrate the return values and file outputs, then create the final output.

### Step 4: Wrap-up
Keep `_workspace/` and report a summary of the results to the user.

## Error handling
- If one agent fails, retry once. If it fails again, state the omission and continue.
- Don't retry failures that give the same result when retried, such as an exhausted usage limit, expired authentication, or denied permission. Open the partial outputs directly to check how far the work actually got, record the missing content as a file in `_workspace/`, and report to the user. For usage limits, also tell when it resets. The main agent reflects only facts it checked directly, and doesn't guess and fill in the agents' judgments.
- If more than half of the agents fail, inform the user and confirm whether to continue.
```

---

## Combining execution modes per phase (hybrid mode)

Use a suitable execution mode for each phase. Write `**Execution mode:**` at the very top of each phase.

```markdown
## Execution mode: Hybrid

| Phase | Execution mode | Reason for choice |
|------|----------|-----------|
| Phase 1 (pre-check) | Performed directly by the main agent or delegated to a sub-agent | The task list must be finalized. |
| Phase 2 (bulk collection and verification) | Workflow coordination | A predefined list must be processed in a distributed way and adversarial verification performed. |
| Phase 3 (agreement and integration) | Persistent agent collaboration | Conflicting data must be discussed and agreed on. |
| Phase 4 (independent verification) | Sub-agent delegation | It's enough for one quality-verification agent to verify independently. |
```

**Execution mode switching rules:**
- Workflow coordination → persistent agent collaboration: save the structured data returned by the workflow in `_workspace/`, and write the file paths in the persistent agents' prompts.
- Persistent agent collaboration → workflow coordination: freeze the team outputs (step 4 of template B), then put the list of file paths into the script via `args`.
- Write the data-passing path at every point where the execution mode changes, so that the results of the previous phase are never lost.

---

## Writing principles that apply to all templates

1. **State the execution mode at the very top of the document.** For hybrid mode, organize the per-phase execution modes into a table.
2. **In workflow coordination mode, describe the script structure in detail.** Specify `phases`, the `schema` summary, and the items to put in `args` without omission.
3. **In persistent agent collaboration mode, describe the use of `name`, SendMessage, and TaskCreate in detail.** Include the list of agents to run, communication rules, dependencies between tasks, and the output-freezing procedure at phase boundaries.
4. **In sub-agent delegation mode, write the Agent parameters without omission.** State whether it is a one-off run without `name`, and specify `subagent_type`, `prompt`, and the output path.
5. **Write file paths clearly.** Write paths relative to `_workspace/`, and follow the `{phase}_{agent}_{artifact}.{ext}` rule for file names.
6. **State the dependencies between phases.** At points where the execution mode changes, describe especially carefully how data is passed over.
7. **Prepare for errors that can actually happen.** Don't assume all work succeeds; define how to handle each situation.
8. **Always include test scenarios.** Write one normal scenario and at least one error scenario.
9. **Don't include items used only in v1.** If TeamCreate, TeamDelete, `team_name`, broadcast, or the experimental flag are referenced, it was written incorrectly.

## Follow-up request expressions to put in `description`

Put the following expressions in so that this skill is selected not only on the first run but also when fixing or re-running results.

- re-run, run again, update, fix, supplement
- "redo only the {part} of {domain}"
- "based on the previous results", "improve the results"
- Request expressions used routinely in the domain (e.g., for a launch-strategy harness, "launch", "promotion", "trending")

Without follow-up request expressions, this harness may not be selected again after the first run.
