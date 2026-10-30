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

1. Locate the HarnessSpec or lightweight brief that defines the design. Record its version and provenance; validate a saved spec when a validator is available. Do not create a formal spec just to evolve a simple one-off.
2. Inspect the authored sources (`sources/` when present), `design-notes.md`, each generated target's actual files and its `materialization-report.md`, and the project change history. For Claude Code, include `.claude/agents/`, `.claude/skills/` and `CLAUDE.md`. For DeepAgents, include the stage directories, `wiring.yaml` and the output `README.md`. The target conventions are in the harness skill's `references/targets/`. Do not invent a `.claude/` tree for a non-Claude harness.
3. Establish a baseline before editing: identify the initial spec or brief, runtime artifact revision, methodology/profile revision, and run or evidence records being compared. Preserve that baseline by immutable copy, revision identifier, or repository history; never overwrite the only record of the prior design or results.
4. If it's a git repository, inspect the change history of those harness files and spec (`git log --oneline -- <paths>`) — establish what changed, when, and why relative to the initial configuration.
5. If `_workspace/` or another run-artifact location exists, skim recent intermediate artifacts and execution records:
   - Do artifacts actually exist at the paths the orchestrator defined? (If not, the workflow was bypassed or is dead code)
   - Does artifact quality follow the format/criteria the skill specifies?
6. Ask the user for feedback (skip if feedback has already been provided):
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
| Domain methodology or semantic progress | Domain profile/method reference, then HarnessSpec if its shared contract changes | A checkpoint, evidence rule, state meaning, or completion condition is wrong → trace the correction to its source, revise/version the method, and update semantic state without changing runtime bookkeeping |
| Missing or conflicting evidence | Source inventory, gap record, or affected claim | A conclusion lacks support or sources disagree → retain provenance, mark the claim unknown or unresolved, and do not encode an unsupported state transition |
| Authored intent or domain knowledge | `sources/intent.yaml` or `sources/domain/` | Scope was wrong, or a domain skill lacks a rule → change the source, then regenerate the spec and all targets with the harness skill |
| Target mapping | The harness skill's target reference, or that target's generated files | One runtime lost or approximated a spec element that another kept → fix the mapping, regenerate only that target, and update its `materialization-report.md` |
| Run mechanics or execution bookkeeping | Runtime host or run record | Retries, task flags, persistence, tools, or handoffs are wrong → fix execution mechanics without treating the change as domain-method progress |
| Missing triggers | Skill description | "It doesn't fire with that phrasing" → expand the description |
| Wrong execution mode | Orchestrator | "Same fan-out every time, and it's slow" → switch to workflow mode |
| Scale/cost | Orchestrator | "It burns too many tokens" → shrink default scale, add budget integration |

**Scope decision:** If adding/removing agents or redesigning the architecture is required, don't do it directly in this skill — guide the user to the harness skill (the Extend procedure in its Phase 0). evolve focuses on **adjusting the existing configuration**.

**Change at the source, then regenerate.** When a change belongs to the sources or the spec, edit it there and regenerate every affected target with the harness skill's Regenerate procedure, reusing the recorded gate answers. Hand-editing only one target's generated files makes the targets diverge silently. If a generated file must be edited directly, record it as a manual intervention in that target's `materialization-report.md`.

### Phase 3: Generalize and apply

1. **Generalize the feedback** — a narrow fix that only fits one instance is overfitting. Don't turn "this report's intro was long" into "keep intros under 10% of the total"; find out why it got long (e.g., the skill lacks length-allocation criteria) and fix it at the level of principle
2. **Record the why alongside** — annotate revised instructions with the reason. Knowing the reason lets agents judge correctly in edge cases
3. Apply one change at a time, and run Phase 4 immediately after each change
   - Route feedback to the narrowest layer that owns its meaning: general harness methodology, domain methodology/state, shared HarnessSpec, runtime adapter/bookkeeping, or project-local harness. If one observation affects multiple layers, state each causal link and make separate changes.
   - When shared intent or contracts change, update HarnessSpec and retain the prior version or Git history as the baseline. When domain methodology changes, preserve its source/revision provenance and record changed state or checkpoint meaning. When runtime mechanics change, update adapter artifacts and keep semantic progress unchanged unless evidence supports a domain-level change. A simple one-off without a spec may stay spec-free; create one only if the change makes it reusable, complex, or materially multi-runtime.
   - Compare a revision with its preserved baseline under the same case inputs and evaluation protocol before claiming improvement. Record regressions, evidence gaps, and unavailable measures; execution success alone is not evidence of domain quality.
4. **Prevent regressions:** if a change would revert an earlier fix in the change history, tell the user about the conflict and get confirmation (if it was shortened in the past for being "too long" and now it's "too short" — the right answer is criteria that satisfy both)
5. **Keep the language of the existing files** — write sentences applied to agents, skills, orchestrators, and `CLAUDE.md` in the language already used in the target file. Just because this skill document is in one language, do not mix sentences of that language into a harness written in another

### Phase 4: Update the change history and verify

1. Record in `design-notes.md` and in each target's change-history location (Claude Code: the **change history** table in `CLAUDE.md`; DeepAgents: the output `README.md`):

```markdown
**Change history:**
| Date | Change | Target | Reason |
|------|--------|--------|--------|
| 2026-07-19 | Added tone guide | skills/content-creator | "Too stiff" feedback |
```

2. Validate the structure of the modified files (frontmatter, reference consistency). If a HarnessSpec changed, run the available validator; report explicitly when validation could not run.
3. If a description was changed, run trigger validation (3+ should-trigger and 3+ near-miss cases each)
4. Final check that each target's change history, `materialization-report.md` and actual files agree

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
