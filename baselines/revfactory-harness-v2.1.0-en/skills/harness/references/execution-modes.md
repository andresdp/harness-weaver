# Execution Modes in Detail — The Three Modes of Harness v2

This document explains the main capabilities, constraints, and selection criteria of the three execution modes that Harness v2 provides. It supplements step 2-1 of `SKILL.md`.

---

## Contents

1. [Mode A: Workflow coordination](#1-mode-a-workflow-coordination)
2. [Mode B: Persistent agent collaboration](#2-mode-b-persistent-agent-collaboration)
3. [Mode C: Sub-agent delegation](#3-mode-c-sub-agent-delegation)
4. [Decision tree for choosing an execution mode](#4-decision-tree-for-choosing-an-execution-mode)
5. [Moving from v1 to v2](#5-moving-from-v1-to-v2)

---

## 1. Mode A: Workflow coordination

Run a coordination script with the `Workflow` tool. Control flow such as distributed execution (fan-out), repetition, and conditional branching is decided by **code**, not by the model's moment-to-moment judgment. Therefore, given the same input, it is easy to reproduce with the same structure, and it is also suited to running many agents in parallel.

```
[main agent] → Workflow(script)
           ├── phase('explore'): pipeline(items, item => agent(...))
           ├── phase('verify'): for each found item, verify by looking for grounds to refute it (parallel)
           └── return { confirmed }   ← structured final result
```

**Main capabilities:**
- `agent(prompt, opts)` — runs a sub-agent. If a JSON Schema is specified in `opts.schema`, it returns a structured object that has passed schema validation. No separate parsing is needed, and it retries automatically if the result doesn't match the schema. Specifying `opts.agentType` lets you use a custom type defined in `.claude/agents/`. Adjust reasoning intensity with `opts.effort`, and isolate file changes with `opts.isolation: 'worktree'`.
- `pipeline(items, stage1, stage2, ...)` — each item goes through several stages independently. There is no synchronization barrier between stages, so **use it by default for multi-stage work.**
- `parallel(thunks)` — a synchronization barrier that waits until all tasks finish. Use it only when the next stage needs **all** of the previous stage's results. Deduplication or early termination based on the total count fall into this case.
- `phase(title)` / `log(msg)` — group and display progress, and inform the user of the current work.
- `budget` — integrates with the token budget the user specified (e.g., "+500k"). Use `budget.total` and `budget.remaining()` to adjust the scale of work dynamically.
- `workflow(nameOrRef, args)` — runs another workflow nested up to one level. Use it to delegate work hierarchically.

**Characteristics:**
- Since code decides the control flow, the same input follows the same execution structure.
- Since structured output (`schema`) is used, schema-conforming data can be passed between stages.
- An interrupted run can be continued with `resumeFromRunId`. Unchanged `agent()` calls return cached results immediately, so re-running only part costs little.
- Runs in the background, and sends a notification when the work finishes.

**Constraints:**
- **The user must request it first.** It can be used only if the user directly requested a workflow or coordination of several agents, or ran a skill that specifies `Workflow` calls. Coordination skills made by the harness fall into the second case. However, keep the default number of agents small, and use large-scale distributed execution only when the user explicitly requests it.
- Scripts can use only pure JavaScript; TypeScript syntax cannot be used. `Date.now()`, `Math.random()`, and argument-less `new Date()` interfere with resuming execution, so they cannot be used. Pass timestamps via `args`.
- Only literals can be used in the `meta` block. Variables, function calls, and spread syntax are not allowed.
- There is an upper limit on the number of agents that can run concurrently per session. Work beyond the limit is automatically queued. The total number of agents that can be called while one workflow runs is also limited, to prevent excessive execution.
- An `agent()` that failed or was skipped returns `null`. `parallel()` doesn't throw an exception even if a call fails, so always apply `.filter(Boolean)` to the results.
- The `parallel()` barrier only aligns the time when tasks finish; it doesn't prevent modifications after they finish. In hybrid mode, a named agent woken with `SendMessage` after a workflow phase ends can modify that phase's output files, so freeze the outputs at the boundary where the mode changes (step 4 of template B in `orchestrator-template.md`).

**Work it fits well:** distributed execution whose list can be fixed in advance, such as N files or M perspectives; repeating until there are no new items (Loop-until-dry) and adversarial verification; large-scale migration and audits; structured report generation

**Work it doesn't fit:** work where the list can't be fixed in advance because the work targets must be found while continuing a conversation; work that must frequently consult the user midway

> For concrete script skeletons and points to watch, see `workflow-recipes.md`.

## 2. Mode B: Persistent agent collaboration

Run named agents and coordinate them with a shared task list and `SendMessage`. This replaces the "agent team" mode of v1.

**The biggest difference from v1:** `TeamCreate` and `TeamDelete` no longer exist. No explicit team object is created as in v1; agents run with names in a session automatically belong to the single collaboration group that forms.

```
[main agent (leader)]
    ├── Agent(name: "researcher", subagent_type: "...", prompt: ...)   ← run in parallel
    ├── Agent(name: "critic", ...)
    ├── TaskCreate(tasks + dependencies) → shared task list
    ├── SendMessage({to: "researcher"}, ...)  ← further instructions while keeping conversational context
    └── receive completion notifications → collect results → final summary
```

**Main capabilities:**
- `Agent(name: ..., subagent_type: ..., model: ..., prompt: ...)` — specifying `name` makes it a persistent agent that can be called again with `SendMessage`. It runs in the background by default and sends a notification on completion. If you must wait until the work finishes, specify `run_in_background: false`.
- `SendMessage({to: name})` — lets a previously run agent continue its work **while keeping its conversational context**. Needed when exchanging results and revising repeatedly.
- `TaskCreate` / `TaskUpdate` / `TaskList` / `TaskGet` — share a task list. Use them to manage dependencies between tasks and progress status, and when a supervisor assigns work according to progress.
- `TaskStop` — stops background tasks that are running excessively or are no longer needed.

**Characteristics:**
- Since agents remember earlier conversations and work history, follow-up requests such as "in the same session, fix only section 2 of the draft made earlier" can be handled.
- Agents can share what they found with each other, discuss differing opinions, and correct the direction of work right away.
- The same specialist agent can keep being used while the session lasts.

**Constraints:**
- Since the main agent (leader) coordinates directly, the more agents there are, the more work concentrates on the leader. 3–5 agents is appropriate.
- Nesting delegation levels deeply slows responses and makes losing conversational context likely. Delegating within two levels is recommended.
- It uses more tokens than calling a sub-agent only once.
- Named agents receive messages even after reporting completion, so while answering another agent's late question they can modify outputs already handed over. If the next phase reads those outputs, freeze the outputs at the phase boundary. The freezing procedure is in step 4 of template B in `orchestrator-template.md`.

**Work it fits well:** work where an author and a verifier exchange results and revise repeatedly; work that discusses mismatched data and merges it into one; work where a supervisor assigns tasks according to progress; work that needs specialist agents throughout the session

**Work it doesn't fit:** one-off work where only the result is needed; large-scale distributed execution whose task list can be fixed in advance

## 3. Mode C: Sub-agent delegation

Delegate to a sub-agent by calling the `Agent` tool only once. Only the result returns to the main agent, and agents don't communicate with each other.

```
[main agent] → Agent(sub A) ─┐
             → Agent(sub B) ─┼→ (parallel, background execution by default) → receive completion notifications → collect results
             → Agent(sub C) ─┘
```

**Characteristics:**
- Low execution overhead and fast. The main agent receives summarized results.
- Independent calls sent **bundled in one message** run concurrently.
- Runs in the background by default. If the result must be received right away, specify `run_in_background: false`.
- The main agent doesn't redo searches it has already delegated; it waits for the results.

**Constraints:**
- Agents can't communicate with each other, and the conversational context doesn't continue after a call ends. To start as a new task, call without `name`.
- All coordination is handled by the main agent.

**Work it fits well:** investigation and collection completed in one pass; work that selects the needed specialists and receives only results; one round of independent verification

**Work it doesn't fit:** work that must exchange results and revise repeatedly; large-scale distributed work whose execution flow can be fixed in advance

## 4. Decision tree for choosing an execution mode

```
Can the task list, verification criteria, and repetition conditions be expressed in code in advance?
├── Yes → Workflow coordination (mode A)
│        Control flow is decided by code, not by the model's judgment.
│        However, keep the condition that the user must request it first, and don't increase the number of agents more than needed.
│
└── No → Does quality improve when results are exchanged repeatedly and conversational context continues?
              ├── Yes → Persistent agent collaboration (mode B)
              │
              └── No → Are there two or more agents?
                            ├── Yes → Parallel sub-agent delegation (mode C)
                            └── No → Single sub-agent call (mode C)
```

**Choosing a hybrid mode:** if the answers to the questions above differ per phase, mix execution modes. The following combinations are mainly used.

| Combination | Composition | Example |
|------|------|------|
| Workflow collection → persistent integration | A → B | Collect material in large divided batches, then the team discusses mismatched data and reaches agreement |
| Persistent generation → workflow verification | B → A | The team makes a draft, then adversarial verification runs distributed for each found item |
| Sub-agent pre-investigation → workflow main work | C → A | The main agent or a sub-agent first identifies the task list, then passes that list to the workflow via `args` |

**Principle of checking the list before coordinating:** before starting a workflow, briefly look over the file list, review targets, and investigation items, and finalize the task list. Understanding the shape of the work before running makes the script simpler and reduces unnecessary work.

## 5. Moving from v1 to v2

If you find coordination skills or agent definitions made by an existing v1 harness, propose converting them to the v2 format according to the table below.

| v1 element | Status | v2 replacement |
|---------|------|---------|
| `TeamCreate(team_name, members)` | **Removed** | Run `Agent(name: ...)` in parallel in one message. Named agents belong to the collaboration group that forms automatically in the session, so there is no need to create a team object separately. |
| `TeamDelete` / "team cleanup" step | **Removed** | Delete that step. Agents end naturally when they finish their work; if needed, stop them with `TaskStop`. |
| "Only one team active per session" constraint | **Changed form** | Since explicit team objects are gone, the v1 constraint doesn't apply. Named agents work together in the collaboration group that forms automatically in the session. |
| `SendMessage({to: "all"})` broadcast | Changed | Send `SendMessage` separately only to the counterparts that need it. |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | **Unnecessary** | Remove it from all documents and scripts. |
| Forcing `model: "opus"` on all agents | Policy abolished | Choose models individually according to the nature of the work. If judgment is ambiguous, use `sonnet`, and keep model inheritance only when intentionally chosen. |
| Composing large-scale distributed execution as a team | Improved | Move it to a `Workflow` script. Define control flow in code, use structured output, and make execution resumable. |
| "Step 0: check conversational context" of coordination skills | Kept | Keep the existing procedure, but add the `resumeFromRunId` option for workflow coordination mode. |
| `_workspace/` file-writing rules | Kept | Use as is. |
| `CLAUDE.md` location guidance and change history | Kept | Use as is. |

**Migration procedure:**
1. Remove references to `TeamCreate`, `TeamDelete`, broadcast, and the experimental flag from existing coordination skills.
2. Find the distributed execution and verification-repetition sections. If the execution flow can be fixed in code in advance, switch them to workflow coordination mode.
3. Rewrite the remaining collaboration sections in persistent agent collaboration syntax (`Agent(name:)` + `SendMessage` + `TaskCreate` / `TaskUpdate`).
4. Remove the bulk `model: "opus"` assignment from agent definitions, and keep only assignments with a rationale.
5. Run step 6 verification (structure verification and trial run) again, and record it in the `CLAUDE.md` change history.
