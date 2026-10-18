---
name: evolve
description: "Harness evolution skill. Collects and generalizes feedback on the execution results of an existing harness, applies it to agents/skills/orchestrators, captures the delta against the initial configuration, and updates the change history. MUST be used whenever the user asks to improve an existing harness based on its execution experience: 'run a harness retrospective', 'evolve the harness', 'apply this feedback to the harness', 'improve the harness', 'the results were disappointing, fix the harness', 'incorporate this feedback into the harness', 'distill the harness lessons'. Building a new harness, redesigning its structure, or adding agents is handled by the harness skill."
---

# Harness Evolve — The Harness Evolution Mechanism

A harness is not a fixture; it is an evolving system. This skill captures the delta of "what worked and what didn't" and feeds it back into the harness so that the next run is measurably better.

```
initial harness ──▶ real project use ──▶ current harness
                                        │
                                        ▼ (delta captured by evolve)
                              generalize feedback → apply to agents · skills · orchestrator
                                        │
                                        ▼
                              update change history → the next run starts from a better draft
```

## Workflow

### Phase 1: Collect the delta

1. Read a HarnessSpec if the harness references one or the project contains `harnessspec.yaml` / `harnessspec.json`. Record its spec version and validate it when the validator is available. Treat the spec as shared design intent; do not assume every simple one-off has a saved spec.
2. Inspect the selected runtime's actual artifacts and project change history. For Claude Code, include `.claude/agents/`, `.claude/skills/`, and `CLAUDE.md`; for other runtimes, use the paths named by the spec or adapter. Do not invent a `.claude/` tree for a non-Claude harness.
3. If it's a git repository, inspect the change history of those harness files and spec (`git log --oneline -- <paths>`) — establish what changed, when, and why relative to the initial configuration.
4. If `_workspace/` exists, skim the intermediate artifacts of recent runs to see the actual execution traces:
   - Do artifacts actually exist at the paths the orchestrator defined? (If not, the workflow was bypassed or is dead code)
   - Does artifact quality follow the format/criteria the skill specifies?
5. Ask the user for feedback (skip if feedback has already been provided):
   - "Is there anything in the results that could be improved?"
   - "Is there anything about the agent composition or workflow you'd like to change?"
   - Never push for feedback if none is offered. However, if any of the observation signals below are present, proactively propose improvements

**Observation-based evolution signals (propose even without feedback):**
- Evidence that the same type of correction was requested 2+ times
- Patterns of agents repeatedly failing/retrying
- Evidence that the user bypassed the orchestrator and worked manually (suspect the orchestrator isn't triggering → candidate for expanding its description)
- v1 artifacts (TeamCreate/TeamDelete/experimental flags) remain in the orchestrator → point to the migration procedure in the harness skill

### Phase 2: Classify feedback and map it to fix targets

| Feedback type | Fix target | Example |
|-----------|----------|------|
| Output quality | The agent's skill | "The analysis is too shallow" → add depth criteria to the skill |
| Agent roles | Agent definition `.md` | "We also need security review" → guide the user to add an agent via the harness skill |
| Workflow order | Orchestrator skill | "Verification should come first" → reorder phases |
| Team composition | Orchestrator + agents | "These two could be merged" → merge agents |
| Shared workflow intent | HarnessSpec | "Every runtime needs the same stage, artifact, or verification change" → update the spec and preserve runtime-specific mapping notes |
| Missing triggers | Skill description | "It doesn't fire with that phrasing" → expand the description |
| Wrong execution mode | Orchestrator | "Same fan-out every time, and it's slow" → switch to workflow mode |
| Scale/cost | Orchestrator | "It burns too many tokens" → shrink default scale, add budget integration |

**Scope decision:** If adding/removing agents or redesigning the architecture is required, don't do it directly in this skill — guide the user to the harness skill (the extend-existing-configuration procedure in step 0). evolve focuses on **adjusting the existing configuration**.

### Phase 3: Generalize and apply

1. **Generalize the feedback** — a narrow fix that only fits one instance is overfitting. Don't turn "this report's intro was long" into "keep intros under 10% of the total"; find out why it got long (e.g., the skill lacks length-allocation criteria) and fix it at the level of principle
2. **Record the why alongside** — annotate revised instructions with the reason. Knowing the reason lets agents judge correctly in edge cases
3. Apply one change at a time, and run Phase 4 immediately after each change
   - When feedback changes shared workflow intent, update HarnessSpec and retain the prior version or Git history as the baseline. When feedback changes runtime mechanics, update adapter artifacts and keep the shared spec unchanged. A simple one-off without a spec may stay spec-free; create one only if the change makes it reusable, complex, or materially multi-runtime.
4. **Prevent regressions:** if a change would revert an earlier fix in the change history, tell the user about the conflict and get confirmation (if it was shortened in the past for being "too long" and now it's "too short" — the right answer is criteria that satisfy both)
5. **Keep the language of the existing files** — write sentences applied to agents, skills, orchestrators, and `CLAUDE.md` in the language already used in the target file. Just because this skill document is in one language, do not mix sentences of that language into a harness written in another

### Phase 4: Update the change history and verify

1. Record in the existing project change-history location (for Claude Code this is the **change history** table in `CLAUDE.md`):

```markdown
**Change history:**
| Date | Change | Target | Reason |
|------|--------|--------|--------|
| 2026-07-19 | Added tone guide | skills/content-creator | "Too stiff" feedback |
```

2. Validate the structure of the modified files (frontmatter, reference consistency). If a HarnessSpec changed, run the available validator; report explicitly when validation could not run.
3. If a description was changed, run trigger validation (3+ should-trigger and 3+ near-miss cases each)
4. Final check that CLAUDE.md and the actual files agree

### Phase 5: Report the evolution

Report to the user:
- A summary of the captured delta (initial configuration → current)
- The changes applied this round and the generalization rationale for each
- Feedback deliberately not applied and why (if any)
- Expected improvements in the next run

## Principles

- **The delta is an asset** — as the change history accumulates, the next harness build in the same domain starts from "a draft closer to launch quality." Never delete the history
- **No applying feedback without generalizing** — adding one rule per case at 1:1 turns the skill into a pile of rules. Compress to principles
- **One change at a time** — batching multiple changes makes it impossible to tell which change produced the effect
