# Execution Modes in Detail — The Three Modes of Harness v2

This document explains the key capabilities, constraints, and selection criteria of the three execution modes that harness v2 provides. It supplements step 2-1 of the harness `SKILL.md`.

---

## Table of contents

1. [Mode A: Workflow orchestration](#1-mode-a-workflow-orchestration)
2. [Mode B: Persistent agent collaboration](#2-mode-b-persistent-agent-collaboration)
3. [Mode C: Sub-agent delegation](#3-mode-c-sub-agent-delegation)
4. [Decision tree for choosing an execution mode](#4-decision-tree-for-choosing-an-execution-mode)
5. [Migrating from v1 to v2](#5-migrating-from-v1-to-v2)

---

## 1. Mode A: Workflow orchestration

Runs an orchestration script with the `Workflow` tool. Control flow — fan-out, iteration, conditional branching — is decided by **code**, not judged by the model on the fly. The same input is therefore easy to reproduce with the same structure, and the mode also suits running many agents in parallel.

```
[Main agent] → Workflow(script)
           ├── phase('explore'): pipeline(items, item => agent(...))
           ├── phase('verify'): for each discovered item, look for counter-evidence and verify it (parallel)
           └── return { confirmed }   ← structured final result
```

**Key capabilities:**
- `agent(prompt, opts)` — Runs a sub-agent. Specifying a JSON Schema in `opts.schema` returns a structured object that has already passed schema validation. No separate parsing is needed, and calls that do not match the schema are retried automatically. Set `opts.agentType` to use a custom type defined in `.claude/agents/`. Tune reasoning effort with `opts.effort`, and isolate file changes with `opts.isolation: 'worktree'`.
- `pipeline(items, stage1, stage2, ...)` — Each item passes through several stages independently. There is no synchronization barrier between stages, so **use it by default for multi-stage work.**
- `parallel(thunks)` — A synchronization barrier that waits for every job to finish. Use it only when the next stage needs the **entire** result of the previous stage. Deduplication and early termination based on total counts fall into this category.
- `phase(title)` / `log(msg)` — Group progress into labeled phases and tell the user what is happening now.
- `budget` — Integrates with the token budget the user specified (for example, "+500k"). Use `budget.total` and `budget.remaining()` to adjust the scale of work dynamically.
- `workflow(nameOrRef, args)` — Runs another workflow nested up to one level deep. Use it to delegate work hierarchically.

**Characteristics:**
- Code defines the control flow, so the same input follows the same execution structure.
- Uses structured output (`schema`), so schema-conformant data can be passed between stages.
- An interrupted run can be resumed with `resumeFromRunId`. Unchanged `agent()` calls immediately return cached results, so re-running only part of the work costs little.
- Runs in the background and sends a notification when the work finishes.

**Constraints:**
- **The user must request it first.** Use this mode only when the user explicitly asks for a workflow or for multiple agents to be orchestrated, or when running a skill that explicitly calls `Workflow`. Orchestration skills created by the harness fall under the second case. Even so, keep the default agent count low, and use large-scale fan-out only when the user explicitly requests it.
- Scripts may use plain JavaScript only; TypeScript syntax is not allowed. `Date.now()`, `Math.random()`, and `new Date()` without arguments break resumption and are not permitted. Pass timestamps through `args`.
- Only literals are allowed in the `meta` block. Variables, function calls, and spread syntax are not accepted.
- There is a per-session cap on the number of agents that can run concurrently. Jobs above the cap are queued automatically. The total number of agents a workflow may invoke while running is also limited to prevent runaway execution.
- Failed or skipped `agent()` calls return `null`. `parallel()` does not throw when a call fails, so always apply `.filter(Boolean)` to the results.
- The `parallel()` barrier only aligns when jobs finish; it does not prevent edits afterwards. In mixed mode, a named agent woken by `SendMessage` after a workflow stage ends can modify that stage's artifact files, so freeze artifacts at boundaries where the mode changes (step 4 of Template B in `orchestrator-template.md`).

**Well-suited tasks:** fan-out runs whose list can be fixed in advance (N files or M perspectives), loop-until-dry iteration combined with adversarial verification, large-scale migrations and audits, generating structured reports

**Ill-suited tasks:** work whose targets must be found through ongoing conversation so the list cannot be fixed in advance, and work that requires frequent consultation with the user along the way

> For concrete script skeletons and pitfalls to avoid, see `workflow-recipes.md`.

## 2. Mode B: Persistent agent collaboration

Runs named agents and coordinates them with a shared task list and `SendMessage`. This replaces the v1 "agent team" mode.

**Biggest difference from v1:** `TeamCreate` and `TeamDelete` no longer exist. Unlike v1, no explicit team object is created; agents launched with names in the session belong to a single collaboration group that forms automatically.

```
[Main agent (leader)]
    ├── Agent(name: "researcher", subagent_type: "...", prompt: ...)   ← runs in parallel
    ├── Agent(name: "critic", ...)
    ├── TaskCreate(tasks + dependencies) → shared task list
    ├── SendMessage({to: "researcher"}, ...)  ← further instructions while keeping conversation context
    └── receive completion notifications → gather results → final write-up
```

**Key capabilities:**
- `Agent(name: ..., subagent_type: ..., model: ..., prompt: ...)` — Specifying `name` makes it a persistent agent that can be called again with `SendMessage`. It runs in the background by default and sends a notification on completion. Specify `run_in_background: false` when you must wait for it to finish.
- `SendMessage({to: name})` — Lets a previously launched agent continue working **while keeping its conversation context**. This is what you need when results are exchanged and revised iteratively.
- `TaskCreate` / `TaskUpdate` / `TaskList` / `TaskGet` — Share a task list. Use them to manage dependencies and progress between tasks, and to let a supervisor assign tasks as work progresses.
- `TaskStop` — Stops background jobs that run excessively or are no longer needed.

**Characteristics:**
- Agents remember earlier conversations and work history, so they can handle follow-up requests such as "only fix section 2 of the draft we made earlier in this session."
- Agents can share findings with one another, discuss disagreements, and correct course immediately.
- The same specialist agents remain available for as long as the session lasts.

**Constraints:**
- The main agent (leader) coordinates everything directly, so more agents means more work piling onto the leader. Three to five agents is a good size.
- Deeply nested delegation slows responses down and makes conversation context easy to lose. Delegating within two levels is recommended.
- It costs more tokens than calling a sub-agent once.
- Named agents keep receiving messages after they report completion, so while answering another agent's late question they may modify an artifact they have already handed off. If the next stage reads that artifact, freeze it at the stage boundary. The freeze procedure is step 4 of Template B in `orchestrator-template.md`.

**Well-suited tasks:** iterative revision in which a writer and a reviewer exchange results, reconciling conflicting data into one through discussion, a supervisor assigning tasks based on progress, work that needs specialist agents throughout the session

**Ill-suited tasks:** one-off jobs where receiving the result is enough, and large-scale fan-out whose task list can be fixed in advance

## 3. Mode C: Sub-agent delegation

Delegates work to sub-agents by invoking the `Agent` tool once. Only the results come back to the main agent, and agents do not communicate with each other.

```
[Main agent] → Agent(sub A) ─┐
              → Agent(sub B) ─┼→ (parallel, runs in the background by default) → receive completion notifications → gather results
              → Agent(sub C) ─┘
```

**Characteristics:**
- Low execution overhead and fast. The main agent receives summarized results.
- Independent calls sent **together in a single message** run concurrently.
- Runs in the background by default. Specify `run_in_background: false` when you need the result immediately.
- The main agent does not repeat a search it has already delegated; it waits for the result.

**Constraints:**
- Agents cannot communicate with each other, and conversation context does not carry over once a call ends. To start as a new task, call without `name`.
- All coordination rests with the main agent.

**Well-suited tasks:** one-shot research or collection, choosing the specialists you need and taking only the results, a single round of independent verification

**Ill-suited tasks:** work that requires iterative back-and-forth revision, and large-scale distributed work whose execution flow can be fixed in advance

## 4. Decision tree for choosing an execution mode

```
Can the task list, verification criteria, and loop conditions be expressed in code up front?
├── Yes → Workflow orchestration (Mode A)
│        Control flow is defined in code, not decided by the model.
│        Keep the condition that the user must request it first, and do not grow the agent count beyond what is needed.
│
└── No → Does quality improve only when results are exchanged repeatedly and conversation context is carried over?
              ├── Yes → Persistent agent collaboration (Mode B)
              │
              └── No → Are there two or more agents?
                            ├── Yes → Parallel sub-agent delegation (Mode C)
                            └── No → Single sub-agent call (Mode C)
```

**Choosing mixed mode:** when the answer to the questions above differs by stage, mix execution modes. The following combinations are used most often.

| Combination | Layout | Example |
|------|------|------|
| Workflow collection → persistent integration | A → B | Split a large body of material and collect it at scale, then have the team discuss the conflicting data and reach agreement |
| Persistent drafting → workflow verification | B → A | The team produces a draft, then adversarial verification is fanned out across every discovered item |
| Sub-agent reconnaissance → workflow main work | C → A | The main agent or a sub-agent first maps the task list, then passes that list to the workflow as `args` |

**Check the list before orchestrating:** before starting a workflow, skim the file list, review targets, or research items and finalize the task list. Understanding the shape of the work before execution keeps the script simple and cuts unnecessary work.

## 5. Migrating from v1 to v2

When you find orchestration skills or agent definitions produced by an existing v1 harness, propose converting them to the v2 format according to the table below.

| v1 element | Status | v2 replacement |
|---------|------|---------|
| `TeamCreate(team_name, members)` | **Removed** | Run `Agent(name: ...)` calls in parallel within a single message. Named agents belong to a collaboration group that forms automatically in the session, so there is no need to create a separate team object. |
| `TeamDelete` / "team cleanup" step | **Removed** | Delete that step. Agents end naturally when their work is done; stop them with `TaskStop` if needed. |
| "Only one active team per session" constraint | **Changed form** | Because explicit team objects no longer exist, the v1 constraint does not apply. Named agents work together in the collaboration group that forms automatically in the session. |
| `SendMessage({to: "all"})` broadcast | Changed | Send `SendMessage` individually, only to the parties that need it. |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | **Unnecessary** | Remove it from both documentation and scripts. |
| Forcing `model: "opus"` on every agent | Policy retired | Choose a model per agent according to the work. When the call is close, use `sonnet`, and keep model inheritance only where it was chosen deliberately. |
| Structuring large-scale fan-out as a team | Improved | Move it to a `Workflow` script. Define control flow in code, use structured output, and make the run resumable. |
| The orchestration skill's "Step 0: check conversation context" | Kept | Keep the existing procedure, but add the `resumeFromRunId` option for workflow orchestration mode. |
| `_workspace/` file-writing rules | Kept | Keep as is. |
| `CLAUDE.md` location guidance and change history | Kept | Keep as is. |

**Migration procedure:**
1. Remove `TeamCreate`, `TeamDelete`, broadcast sends, and experimental flag references from the existing orchestration skill.
2. Locate the fan-out and verification loop sections. If the execution flow can be defined in code up front, convert those sections to workflow orchestration mode.
3. Rewrite the remaining collaboration sections with persistent agent collaboration syntax (`Agent(name:)` + `SendMessage` + `TaskCreate` / `TaskUpdate`).
4. Remove blanket `model: "opus"` assignments from agent definitions and keep only the justified ones.
5. Re-run the 6-step validation (structure validation and dry run) and record it in the `CLAUDE.md` change history.
