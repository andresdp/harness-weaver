# Team composition patterns — six basic patterns, quality verification, and agent definitions

This document supplements steps 2-2 and 3 of the harness `SKILL.md`. It describes the execution mode v2 recommends for each pattern. For details, see `execution-modes.md`.

---

## Table of contents

1. [Six basic patterns](#1-six-basic-patterns)
2. [Quality verification patterns (added in v2)](#2-quality-verification-patterns-added-in-v2)
3. [Compound patterns](#3-compound-patterns)
4. [Choosing an agent type](#4-choosing-an-agent-type)
5. [Agent definition structure](#5-agent-definition-structure)
6. [Criteria for splitting agents](#6-criteria-for-splitting-agents)
7. [Designing agents for reuse](#7-designing-agents-for-reuse)
8. [Skills vs. agents](#8-skills-vs-agents)

---

## 1. Six basic patterns

### 1-1. Pipeline

Stages run one after another in a fixed order. The previous agent's output becomes the next agent's input.

```
[Analyze] → [Design] → [Implement] → [Verify]
```

**Best for:** when each stage depends heavily on the previous stage's artifacts

**Example:** novel writing — worldview → characters → plot → drafting → editing

**Caution:** if one stage runs late, the whole job runs late. Design each stage to be as independent as possible.

**Execution mode recommended in v2:** if you can list the stages and items up front, use **workflow orchestration** with `pipeline()`. Each item moves on to the next stage as soon as the previous stage finishes for it. You never wait for every item in a stage to finish, so the total run time is shorter. If a human must review artifacts between stages, call sub-agents in sequence instead.

### 1-2. Fan-out/Fan-in

Independent tasks are processed at the same time, and the results are merged into one.

```
           ┌→ [Expert A] ─┐
[Dispatch] → ├→ [Expert B] ─┼→ [Merge]
           └→ [Expert C] ─┘
```

**Best for:** when the same input must be analyzed from several perspectives or domains

**Example:** comprehensive research — investigate official sources, media, communities, and background in parallel, then consolidate into a single report

**Caution:** how the results are merged determines the overall quality.

**Execution mode recommended in v2:** consider **workflow orchestration** first. Define the list of perspectives as an array, pass it to `pipeline()`, receive results conforming to the `schema`, and merge them in code. Use `parallel()` only when all results must be gathered before deduplication; in that case the next step proceeds only after every parallel call has finished. For research by a 2–4 agent team that must share findings in real time, persistent agent collaboration also fits.

### 1-3. Expert Pool

Only the experts that match the input and the situation are selected and invoked.

```
[Classifier] → { Expert A | Expert B | Expert C }
```

**Best for:** when each input type needs different handling

**Example:** code review — invoke only the expert for the relevant area among the security, performance, and architecture experts

**Caution:** if the classifier agent misclassifies the input, the right expert cannot be selected.

**Execution mode recommended in v2:** use **sub-agent delegation** and invoke only the experts you need, once each. If you must continue a follow-up conversation with the same expert, give it a `name` and switch to persistent agent collaboration.

### 1-4. Producer-Reviewer

A producer agent and a reviewer agent work as a pair.

```
[Produce] → [Review] → (issues found) → re-run [Produce]
```

**Best for:** when artifact quality must be verified and you can define objective pass criteria

**Caution:** cap retries at 2–3 so review-and-fix never loops forever.

**Execution mode recommended in v2:** if the verification criteria can be expressed in code, use **workflow orchestration** and run parallel verification for every item found with the adversarial verification pattern below. If subjective judgment has to be negotiated, run the producer and the reviewer as a **named pair of persistent agents** exchanging feedback over SendMessage. Because the producer keeps the earlier conversation, it can fix exactly the parts that were flagged.

### 1-5. Supervisor

A central agent manages task state and divides work according to progress.

```
             ┌→ [Worker A]
[Supervisor] ─┼→ [Worker B]    ← dispatch follows progress
             └→ [Worker C]
```

**Best for:** when the workload keeps changing, or how to split the work must be decided during execution

**Difference from fan-out:** fan-out fixes the distribution before work starts. A supervisor re-assigns work as progress unfolds.

**Caution:** split the work too finely and the supervisor must re-assign constantly, becoming a bottleneck.

**Execution mode recommended in v2:** use **persistent agent collaboration**. The main agent, acting as leader, registers tasks with `TaskCreate`, receives completion notices from workers, and re-assigns work with `SendMessage` and `TaskUpdate`. If the task list can be fixed up front and the assignment procedure can be written in code, switch to workflow orchestration — in that case there is nothing left for a supervisor to decide.

### 1-6. Hierarchical Delegation

A delegated agent delegates further to its own sub-agents. Use this to split a complex problem into multiple levels.

```
[Lead] → [Team lead A] → [Worker A1, A2]
       → [Team lead B] → [Worker B1]
```

**Best for:** when the problem splits naturally into parent tasks and child tasks

**Caution:** beyond three levels, execution slows down and earlier work may not carry over properly. **Keep it to two levels or fewer.**

**Execution mode recommended in v2:** orchestrate by nesting workflows. The parent workflow calls a child workflow with `workflow(nameOrRef, args)`. Nesting supports only one level, which prevents the hierarchy from getting too deep. Alternatively, remove the hierarchy and restructure the work as `phase()`s of a single workflow.

## 2. Quality verification patterns (added in v2)

These are workflow verification patterns added to harnesses where artifact accuracy matters. Their purpose is to filter out results that look right at a glance but are actually wrong.

| Pattern | Structure | When to use |
|------|------|------|
| **Adversarial verification** | Run N independent adversarial verification agents for each item found. Only items that more than half of the N agents judge as `confirmed` with sufficient evidence pass. | When findings or claims must be trustworthy (reviews, audits, investigations) |
| **Multi-perspective verification** | Instead of giving the N adversarial verification agents the same prompt, assign each a different perspective such as accuracy, security, or reproducibility. | When errors can occur in several types. Splitting the verification criteria catches errors that a repeated identical check misses. |
| **Judge panel** | Judge N drafts built with different approaches in parallel. Write the final draft based on the highest-scoring one, folding the strengths of the other drafts in where needed. | Design or planning work with many possible solutions. Comparing several drafts beats iterating on a single one. |
| **Loop-until-dry** | Repeat the search until K consecutive rounds yield zero new items. Record refuted items in `seen` too, so the same item is not proposed over and over. | Searches where you cannot know how many problems exist (bugs, issues, edge cases). A fixed count can miss problems still waiting to be found. |
| **Multi-criteria sweep** | Run in parallel agents that search by different criteria, such as container, content, entity, and time. | When a single search criterion cannot find everything |
| **Completeness critic** | Add one agent whose only job, at the end, is to check: "Which search criteria were not used? Which claims were never verified? Which sources were never read?" | Just before merging results. Newly found gaps go into the next search round. |
| **Disclose the excluded count** | Whenever `top-N` or sampling limits coverage, always record the number of excluded items with `log()`. | Every fan-out. Without the excluded count, users wrongly assume full coverage. |

**Scaling principle:** size the team to the scope the user requested. For "check whether there are bugs," use a handful of explorers and one adversarial verification agent. For "audit this thoroughly," add explorers, have 3–5 adversarial verification agents verify each finding, then run a synthesis stage. When the requested scope is hard to judge, be thorough for investigations, reviews, and audits, and keep quick checks small.

> Implementation examples are in `workflow-recipes.md`.

## 3. Compound patterns

Real work combines several patterns.

| Compound pattern | Composition | Example |
|----------|------|------|
| **Fan-out/Fan-in + Producer-Reviewer** | Produce several drafts at the same time, then verify each | Multilingual translation — translate into four languages in parallel, then have a native-speaker reviewer per language check the result |
| **Pipeline + Fan-out/Fan-in** | Run some of the sequential stages in parallel | Analysis (sequential) → implementation (parallel) → integration tests (sequential) |
| **Supervisor + Expert Pool** | The supervisor invokes the expert that fits the situation | Customer inquiries — the supervisor classifies the request, then routes it to the right expert |
| **Sweep + adversarial verification + synthesis** | Search by multiple criteria → verify each finding → completeness review → write the report | Comprehensive code audits, in-depth investigations |

In compound patterns, choose the execution mode that fits each stage. Such compositions are called mixed mode. The selection criterion is whether that stage's control flow can be defined in code up front.

## 4. Choosing an agent type

When invoking an agent, specify its type with the Agent tool's `subagent_type` parameter or the Workflow's `agentType` parameter.

### Built-in types

| Type | Available tools | Good for |
|------|----------|-----------|
| `general-purpose` | Everything (including WebSearch, WebFetch) | Web research, general tasks, file edits |
| `Explore` | Read-only (no Edit, Write) | Locating code in the codebase. Do not use it for reviews or audits. |
| `Plan` | Read-only (no Edit, Write) | Architecture design, writing implementation plans |

### Custom types

Define the type in `.claude/agents/{name}.md`. When invoking it, specify `subagent_type: "{name}"` or `agentType: "{name}"`. Define the tools and the model in the YAML frontmatter.

### Selection criteria

| Situation | Recommendation | Why |
|------|------|------|
| Complex role reused across many sessions | **Custom type** | The expert role and working principles are kept consistent in one file. |
| Simple one-off research or collection where a detailed prompt is enough | `general-purpose` + a detailed prompt | Use a built-in type directly, with no separate definition file. |
| Only locating code | `Explore` | It has no file-editing tools, so there is no risk of unintended fixes. |
| Producing designs or plans only | `Plan` | It focuses on analysis without changing code. |
| Simple one-off file edit | `general-purpose` + a detailed prompt | Handled directly with a built-in type. |
| Implementation that is reused or needs specialized rules | **Custom type** | Allow every tool needed and apply specialist instructions. |
| Editing many files in parallel | Custom type + `isolation: 'worktree'` | Prevents edit conflicts between agents. Creating worktrees has a cost, so use it only for parallel edits. |

**Principle:** turn expert roles you will reuse across sessions into custom types in `.claude/agents/{name}.md`. Do not create definition files for one-off tasks that a built-in type already covers.

**Model policy:** choose the model tier by task complexity, expected duration, how much independent judgment is required, and the response speed you need. Use **fable** for the hardest tasks that require planning and long autonomous runs, and for agent orchestration. Use **opus** for design and architecture, code generation, complex analysis, cross-verification, and creative writing. Use **sonnet** for routine work that involves little judgment — log analysis, format conversion, static file checks, running deployment scripts, simple collection. When in doubt, choose sonnet. Never assign the same model to every agent without a reason, and record the reason in a comment. Detailed criteria are in `model-selection-guide.md`.

## 5. Agent definition structure

```markdown
---
name: agent-name
description: "Describe the role in one or two sentences and list the phrases that should trigger invocation."
# tools: Read, Grep, Glob, Bash        ← optional: set this to restrict the available tools (e.g. a read-only reviewer)
#                                         for agents that edit artifacts, include Edit along with Write
# model: sonnet                         ← choose to fit the task (model-selection-guide.md); record the reason in a comment
---

# Agent Name — one-line role summary

You are a [role] expert in [domain].

## Core role
1. Role 1
2. Role 2

## Working principles
- Principle 1 (state the reason too, so the same standard applies in edge cases)
- Principle 2

## Input and output rules
- Input: [what you receive and from where — file paths, args, the previous stage's artifacts]
- Output: [what you write and where — a _workspace/ path or a structured return value]
- Format: [file format, structure, schema]

## Communication rules (persistent agent collaboration)
- First report: tell the leader which tools are actually available (to check whether anything listed in `tools` is missing)
- Inbound messages: [which messages you receive from whom]
- Outbound messages: [which messages you send to whom]
- Shared tasks: [which kinds of tasks you register or claim]

## On re-invocation
- If previous artifacts exist, read them and incorporate the improvements.
- When user feedback arrives, revise only the affected parts.

## Error handling
- [What to do on failure]
- [What to do when input is missing or ambiguous]

## Collaboration
- Relationship with other agents
```

**Workflow-only agents:** replace the "Communication rules" section with a "Structured output" section. Spell out the JSON structure to return, and describe the final text as **returned data**, not as a message to the user.

**Cautions when restricting `tools`:**

- Give agents that fix artifacts Edit along with Write. With Write alone, even a one-line fix rewrites the whole file. On a large artifact the agent gives up on editing and works around it by writing to a separate file, leaving the original artifact unfixed.
- Lazily loaded tools such as `TaskCreate` and `TaskUpdate` have been observed to be missing at run time even when listed in `tools` (observed in Claude Code 2.1.226; may vary by environment). `SendMessage`, which is also lazily loaded, was present, so exactly which tools go missing is unclear. Have persistent agents report the tools actually available in their first report. If a tool is missing, the orchestrator handles that work instead (e.g. the leader updates task status with `TaskUpdate`) or the `tools` restriction in the definition file is lifted.

## 6. Criteria for splitting agents

| Criterion | Split | Merge |
|------|------|------|
| Expertise | Split when the domains differ | Merge when the domains overlap |
| Parallelism | Split when they can run independently | Consider merging when they must run in order |
| Information needed | Split when one agent would handle too much information | Merge when little information is needed and the tasks are short |
| Reusability | Split when other teams can reuse it | Consider merging when only this team uses it |

## 7. Designing agents for reuse

Before creating a new agent, compare its role with the existing agents in `.claude/agents/`. If you build or extend harnesses repeatedly, agents with the same role can pile up under different names.

| Relationship to an existing agent | Action |
|------|------|
| The existing agent fully covers the new role | Do not create a new one; invoke the existing agent. |
| Partial overlap, and generalizing the existing agent would cover the new role | Generalize and extend the existing agent. |
| Partial overlap, but the domain is deliberately specialized | Create it as a separate agent. |
| The role scope is entirely different | Create a new one. |

**Principle:** the more each agent focuses on a single role, the easier it is to reuse and the less duplication accumulates. If an expansion leaves an agent with two or more roles, first check whether it can be split.

**When extending an existing agent:** the behavior of the orchestrators that call it can change too. Before extending, check which orchestrators invoke the agent, and reflect the widened role in its `description`. After extending, confirm with a dry run (step 6-5 of the harness `SKILL.md`) that existing flows still work unchanged.

## 8. Skills vs. agents

| Aspect | Skill | Agent |
|------|-------------|-----------------|
| Definition | A set of task procedures and tools | An expert role and behavior principles |
| Location | `.claude/skills/` | `.claude/agents/` |
| Runs when | A user request matches the applicability conditions written in `description` | Invoked directly via the Agent or Workflow tool |
| Answers | "How is it done?" | "Who does it?" |

### Ways to connect skills and agents

| Approach | Implementation | Good fit |
|------|------|-----------|
| **Skill tool invocation** | State in the agent prompt: `invoke /skill-name with the Skill tool` | When the skill is a standalone workflow that users may also invoke directly |
| **Inline in the prompt** | Write the skill's content directly into the agent definition | When the skill is short (50 lines or fewer) and used only by that agent |
| **Load reference files on demand** | `Read` files from the skill's `references/` only when needed | When the skill is large and needed only under specific conditions |

Invoke skills shared by several agents with the Skill tool. Inline short skills used by a single agent in the prompt; for larger ones, load only the reference files you need.
