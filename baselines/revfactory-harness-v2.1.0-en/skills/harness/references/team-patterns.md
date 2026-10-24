# Team Composition Patterns — Six Basic Patterns, Quality Verification, Agent Definitions

This document supplements steps 2-2 and 3 of `SKILL.md`. For each pattern it explains the execution mode that v2 recommends. Details are in `execution-modes.md`.

---

## Contents

1. [Six basic patterns](#1-six-basic-patterns)
2. [Quality verification patterns (added in v2)](#2-quality-verification-patterns-added-in-v2)
3. [Composite patterns](#3-composite-patterns)
4. [Choosing an agent type](#4-choosing-an-agent-type)
5. [Agent definition structure](#5-agent-definition-structure)
6. [Agent separation criteria](#6-agent-separation-criteria)
7. [Agent reuse design](#7-agent-reuse-design)
8. [Distinguishing skills and agents](#8-distinguishing-skills-and-agents)

---

## 1. Six basic patterns

### 1-1. Pipeline

Continues the work in a fixed order. The previous agent's output becomes the next agent's input.

```
[analysis] → [design] → [implementation] → [verification]
```

**Suitable:** when each stage depends heavily on the outputs of the previous stage

**Example:** novel writing — world → characters → plot → writing → editing

**Caution:** if one stage is delayed, the whole work is delayed. Design each stage to be as independent as possible.

**Execution mode recommended in v2:** if the stages and items can be enumerated in advance, **workflow coordination** is recommended, using `pipeline()`. Each item moves to the next stage as soon as the previous stage finishes. There is no need to wait for all items of a stage to finish, so the overall execution time is also shorter. If a person must review the outputs between stages, call sub-agents one after another.

### 1-2. Distribute and integrate (fan-out/fan-in)

Processes mutually independent tasks at the same time, then merges the results into one.

```
         ┌→ [specialist A] ─┐
[split] → ├→ [specialist B] ─┼→ [integrate]
         └→ [specialist C] ─┘
```

**Suitable:** when the same input must be analyzed separately from several perspectives or areas

**Example:** comprehensive research — research official sources, press, community, and background at the same time, then organize them into one report

**Caution:** the way results are merged determines the overall quality.

**Execution mode recommended in v2:** consider **workflow coordination** first. Define the list of perspectives as an array and send it to `pipeline()`, receive the results according to `schema`, then merge them in code. Use `parallel()` only when duplicates must be removed after collecting all results. In that case, move to the next stage after all parallel calls finish. For research by 2–4 people in which researchers must share what they find in real time, persistent agent collaboration is also suitable.

### 1-3. Expert pool

Selects and calls only the specialists that fit the input and situation.

```
[classifier] → { specialist A | specialist B | specialist C }
```

**Suitable:** when the processing method must differ for each input type

**Example:** code review — call only the specialist for the relevant area among security, performance, and architecture specialists

**Caution:** if the classifier agent classifies the input wrongly, the suitable specialist can't be selected.

**Execution mode recommended in v2:** with **sub-agent delegation**, call only the needed specialists once. If a follow-up conversation with the same specialist must continue, give it a `name` and switch to persistent agent collaboration.

### 1-4. Generate and verify (Producer-Reviewer)

A generating agent and a verifying agent work as a pair.

```
[generate] → [verify] → (when a problem is found) → re-run [generate]
```

**Suitable:** when the quality of the outputs must be verified and objective judgment criteria can be defined

**Caution:** set the maximum number of retries to 2–3 so that verification and revision don't repeat endlessly.

**Execution mode recommended in v2:** if the verification criteria can be expressed in code, use **workflow coordination**. Perform parallel verification for each item found, with the adversarial verification pattern below. If subjective judgments must be coordinated, run the generator and verifier as **a pair of persistent agents** with names, and exchange feedback with SendMessage. Since the generator keeps the earlier conversation content, it can fix the pointed-out parts precisely.

### 1-5. Supervisor

A central agent manages the work status and divides work according to progress.

```
               ┌→ [worker A]
[supervisor] ──┼→ [worker B]    ← distribute according to progress
               └→ [worker C]
```

**Suitable:** when the amount of work keeps changing, or when how to divide the work must be decided during execution

**Difference from distributed execution:** distributed execution decides the distribution method before the work starts. A supervisor looks at progress and redistributes work.

**Caution:** if work is divided too finely, the supervisor must redistribute often and becomes a bottleneck.

**Execution mode recommended in v2:** use **persistent agent collaboration**. The main agent, as leader, registers tasks with `TaskCreate`, and after receiving workers' completion notifications, redistributes work with `SendMessage` and `TaskUpdate`. If the task list can be finalized in advance and the distribution procedure can also be written in code, switch to workflow coordination, because in that case there is nothing for the supervisor to judge separately.

### 1-6. Hierarchical delegation

An agent that has been delegated work delegates again to lower-level agents. This is used to divide a complex problem into several levels.

```
[lead] → [team lead A] → [practitioners A1, A2]
       → [team lead B] → [practitioner B1]
```

**Suitable:** when the problem can be naturally divided into higher-level and lower-level tasks

**Caution:** if it goes three or more levels deep, execution slows and earlier work content may not be passed on properly. **Within two levels is recommended.**

**Execution mode recommended in v2:** coordinate by nesting workflows. The higher-level workflow calls the lower-level workflow with `workflow(nameOrRef, args)`. Nested calls are supported to only one level, which prevents the hierarchy from getting too deep. Alternatively, remove the hierarchy and recompose it with the `phase()` of a single workflow.

## 2. Quality verification patterns (added in v2)

Workflow verification patterns to add to harnesses where output accuracy matters. Their purpose is to filter out results that look right at first glance but are actually wrong.

| Pattern | Structure | When to use |
|------|------|------|
| **Adversarial verification** | For each found item, run N independent adversarial verification agents. Pass only items that more than half of the N agents judge `confirmed` with sufficient evidence. | When the findings or claims must be trustworthy (review, audit, research) |
| **Perspective-distributed verification** | Instead of giving the N adversarial verification agents the same prompt, assign them different perspectives such as correctness, security, and reproducibility. | When errors can arise in several types. Dividing the verification criteria finds errors that repeating the same verification misses. |
| **Judge panel** | Judge in parallel N drafts made with different approaches. Write the final version based on the highest-rated draft, reflecting the strengths of other drafts where needed. | Design or planning with many possible solutions. Comparing several drafts is better than repeatedly fixing one draft. |
| **Repeat until there are no new items (Loop-until-dry)** | Repeat the search until newly found items are 0 for K consecutive rounds. Also record rejected items in `seen` to prevent the same items from being proposed repeatedly. | Searches where it is unknown how many problems there are (bugs, issues, boundary cases). Fixing the count in advance can miss problems that would be found later. |
| **Search by multiple criteria** | Run in parallel agents that search by different criteria, such as containers, contents, entities, and time. | When one search criterion alone can't find everything |
| **Omission review** | At the end, have one agent that checks only "which search criteria weren't used, which claims weren't verified, which material wasn't read?" | Just before merging the results. Newly found omitted items are put into the next search task. |
| **Disclose the number of excluded items** | When the checked range is limited by `top-N` or sampling, always record the number of excluded items with `log()`. | All distributed execution. If the excluded count isn't disclosed, the user wrongly assumes everything was checked. |

**Scaling principle:** set the scale according to the research scope the user requested. For "check whether there are bugs", compose a few searchers and one adversarial verification agent. For "audit it thoroughly", increase the searchers, have 3–5 adversarial verification agents verify each found item, and then go through a synthesis phase. If the requested scope is hard to judge, carry out research, review, and audit thoroughly, and do quick checks at a small scale.

> Implementation examples are in `workflow-recipes.md`.

## 3. Composite patterns

In real work, several patterns are combined.

| Composite pattern | Composition | Example |
|----------|------|------|
| **Distribute and integrate + generate and verify** | Make several drafts at the same time, then verify each | Multilingual translation — translate into four languages in parallel, then native-speaker reviewers per language check them |
| **Pipeline + distribute and integrate** | Process some of the sequential stages in parallel | Analysis (sequential) → implementation (parallel) → integration test (sequential) |
| **Supervisor + expert pool** | The supervisor calls the specialist suited to the situation | Customer inquiry handling — the supervisor classifies inquiries and assigns them to suitable specialists |
| **Search + adversarial verification + synthesis** | Search by multiple criteria → verify each found item → omission review → write the report | Comprehensive code audit, in-depth research |

In composite patterns, choose a suitable execution mode for each phase. Such a composition is called hybrid mode. The selection criterion is whether that phase's control flow can be fixed in code in advance.

## 4. Choosing an agent type

When calling an agent, specify the type with the Agent tool's `subagent_type` or Workflow's `agentType` parameter.

### Built-in types

| Type | Tools available | Suitable use |
|------|----------|-----------|
| `general-purpose` | All (including WebSearch, WebFetch) | Web research, general work, file modification |
| `Explore` | Read-only (Edit, Write excluded) | Finding code locations in a codebase. Not used for review or audit. |
| `Plan` | Read-only (Edit, Write excluded) | Architecture design, writing implementation plans |

### Custom types

Define the type in `.claude/agents/{name}.md`. When calling, specify `subagent_type: "{name}"` or `agentType: "{name}"`. Set the tools and model to use in the YAML frontmatter.

### Selection criteria

| Situation | Recommended | Reason |
|------|------|------|
| The role is complex and used repeatedly across sessions | **Custom type** | The specialist role and working principles are managed consistently in a file. |
| Simple one-off research or collection, where a detailed prompt alone is enough | `general-purpose` + detailed prompt | Use the built-in type directly without a separate definition file. |
| Only searching for code locations | `Explore` | No file-modification tools, so no risk of wrong edits. |
| Only writing a design or plan | `Plan` | Focuses only on analysis without code changes. |
| Simple one-off file modification | `general-purpose` + detailed prompt | Handle it right away with the built-in type. |
| Implementation used repeatedly or needing specialized rules | **Custom type** | Allow all needed tools and apply specialized guidance. |
| Modifying several files in parallel | Custom type + `isolation: 'worktree'` | Prevents file-modification conflicts between agents. Creating worktrees has a cost, so use it only when modifying in parallel. |

**Principle:** create specialist roles to be reused across sessions as custom types in `.claude/agents/{name}.md`. Don't create separate definition files for one-off work that uses built-in types as they are.

**Model policy:** choose the model tier by the work's complexity, expected duration, the scope of judgment it must make by itself, and the response speed needed. Use **fable** for the hardest work that must plan and run autonomously over a long period, and for agent coordination. Use **opus** for design and architecture, code generation, complex analysis, cross-verification, and creative writing. Use **sonnet** for routine work with little to judge, such as log analysis, format conversion, static file inspection, running deploy scripts, and simple collection. If it is hard to judge, choose sonnet. Don't assign the same model to all agents without a rationale, and leave the reason for the choice as a comment. Detailed criteria are in `model-selection-guide.md`.

## 5. Agent definition structure

```markdown
---
name: agent-name
description: "Describe the role in one or two sentences and list the expressions that serve as invocation conditions."
# tools: Read, Grep, Glob, Bash        ← optional: specify to restrict the tools used (read-only reviewers, etc.)
#                                         for agents that fix outputs, include Edit along with Write
# model: sonnet                         ← choose to fit the nature of the work (model-selection-guide.md), record the reason as a comment
---

# Agent Name — one-line summary of the role

You are a [role] specialist in [domain].

## Core role
1. Role 1
2. Role 2

## Working principles
- Principle 1 (write the reason too, so that the same criteria are used even in exceptional situations.)
- Principle 2

## Input and output rules
- Input: [what is received from where — file paths, args, previous-phase outputs]
- Output: [what is written where — a _workspace/ path or a structured return value]
- Format: [file format, structure, schema]

## Communication rules (persistent agent collaboration)
- First report: tell the leader the list of tools actually available (to check whether tools listed in `tools` are missing)
- Receiving messages: [what messages are received from whom]
- Sending messages: [what messages are sent to whom]
- Shared tasks: [what types of tasks are registered or requested]

## When called again
- If previous outputs exist, read them and reflect the improvements.
- When user feedback is received, modify only those parts.

## Error handling
- [what to do on failure]
- [what to do when input is missing or ambiguous]

## Collaboration
- Relationships with other agents
```

**Workflow-only agents:** instead of "Communication rules", include a "Structured output" item. Specify the JSON structure to return, and state that the final text is **return data**, not a message to the user.

**Points to watch when restricting `tools`:**

- Give agents that fix outputs Edit along with Write. With only Write, even fixing one line requires rewriting the whole file. When the output is large, the agent gives up on fixing and works around it by writing separately in another file, so the original output remains unfixed.
- There are cases where lazily loaded tools such as `TaskCreate` and `TaskUpdate` are not given at execution time even when listed in `tools` (observed in Claude Code 2.1.226; may differ by environment). `SendMessage`, another lazily loaded tool, was given, so the boundary of which tools go missing is not clear. Have persistent agents report the list of tools they can actually use in their first report. If tools are missing, the orchestrator handles that work in their place (e.g., the leader updates task status with `TaskUpdate`) or lifts the `tools` restriction in the definition file.

## 6. Agent separation criteria

| Criterion | Separate | Merge |
|------|------|------|
| Expertise | Separate if the areas of responsibility differ | Merge if the areas of responsibility overlap |
| Parallelism | Separate if they can run independently of each other | Consider merging if they must be processed in order |
| Information needed | Separate if one agent would handle a lot of information | Merge if little information is needed and the work is short |
| Reusability | Separate if it can be reused in other teams | Consider merging if it is used only in this team |

## 7. Agent reuse design

Before creating a new agent, compare its role with existing agents in `.claude/agents/`. If a harness is built or extended several times, agents with the same role can pile up under different names.

| Relationship to existing agents | Action |
|------|------|
| An existing agent covers all of the new role | Don't create a new one; call the existing agent. |
| It partly overlaps, and generalizing the existing agent lets it take on the new role too | Generalize and extend the existing agent. |
| It partly overlaps, but the domain was intentionally specialized | Create a new, separate agent. |
| The role's scope is entirely different | Create a new one. |

**Principle:** the more an agent focuses on one role, the easier it is to reuse and the less duplication there is. If extending results in two or more roles, first consider whether it can be split.

**When extending an existing agent:** the behavior of the orchestrators that call that agent can also change. Before extending, check which orchestrators call this agent, and reflect the widened role in the `description`. After extending, check with a dry run (step 6-5 of `SKILL.md`) that the existing flow still works.

## 8. Distinguishing skills and agents

| Aspect | Skill | Agent |
|------|-------------|-----------------|
| Definition | A work procedure and a set of tools | A specialist role and behavioral principles |
| Location | `.claude/skills/` | `.claude/agents/` |
| Execution condition | When the user's request matches the conditions written in the `description` | When called directly with the Agent or Workflow tool |
| Purpose | "How is it done" | "Who does it" |

### Ways of connecting skills and agents

| Approach | Implementation | Suitable when |
|------|------|-----------|
| **Skill tool call** | State "call /skill-name with the Skill tool" in the agent prompt | The skill is an independent workflow that the user may also call directly |
| **Included directly in the prompt** | Write the skill content directly in the agent definition | The skill is short, 50 lines or fewer, and used only by that agent |
| **Loading reference files** | Read the skill's `references/` files with `Read` only when needed | The skill content is large and needed only under specific conditions |

Call skills shared by several agents with the Skill tool. Put short skills used only by a specific agent directly in the prompt, and if the content is large, load only the needed reference files.
