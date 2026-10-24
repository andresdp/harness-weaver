---
name: evolve
description: "Harness evolution skill. Collects and generalizes feedback on the execution results of a harness in use, reflects it into agents/skills/orchestrators, captures the delta relative to the initial configuration, and updates the change history. Always use this skill for improvement requests based on the execution experience of an existing harness, such as 'harness retrospective', 'harness evolution', 'apply harness feedback', 'improve the harness', 'the results were disappointing, fix the harness', 'apply this feedback to the harness', or 'summarize the harness lessons'. Building a new harness, redesigning its structure, and adding agents are handled by the harness skill."
---

# Harness Evolve — The Harness Evolution Mechanism

A harness is not a fixture but an evolving system. This skill captures the delta of "what worked and what didn't" and feeds it back into the harness, so that the next run gets measurably better.

```
initial harness ──▶ real project use ──▶ current harness
                                        │
                                        ▼ (delta captured with evolve)
                                  generalize feedback → reflect into agents · skills · orchestrator
                                        │
                                        ▼
                                  update change history → the next run starts from a better draft
```

## Workflow

### Phase 1: Collect the delta

1. Read `.claude/agents/`, `.claude/skills/`, and `CLAUDE.md` (the change history table)
2. If it is a git repository, look up the change history of the harness files (`git log --oneline -- .claude/ CLAUDE.md`) — identify what changed, when, and why relative to the initial configuration
3. If `_workspace/` exists, skim the intermediate outputs of recent runs to check actual execution traces:
   - Do outputs actually exist at the paths the orchestrator defined? (If not, the workflow was bypassed or is dead code)
   - Does output quality follow the format/criteria the skill specifies?
4. Ask the user for feedback (skip if feedback has already been provided):
   - "Is there anything in the results that could be improved?"
   - "Is there anything about the agent composition or workflow you'd like to change?"
   - Don't force it if there is no feedback. However, if the observation signals below are present, proactively propose improvements

**Observation-based evolution signals (propose even without feedback):**
- Traces of the same type of correction request repeated 2 or more times
- Patterns of agents repeatedly failing/retrying
- Traces of the user bypassing the orchestrator and working manually (suspected orchestrator trigger failure → candidate for expanding the description)
- v1 relics (TeamCreate/TeamDelete/experimental flags) remain in the orchestrator → point to the harness skill's migration procedure

### Phase 2: Classify feedback types and map them to fix targets

| Feedback type | Fix target | Example |
|-----------|----------|------|
| Output quality | The agent's skill | "The analysis is too superficial" → add depth criteria to the skill |
| Agent role | Agent definition `.md` | "Security review is also needed" → guide adding an agent with the harness skill |
| Workflow order | Orchestrator skill | "Verification should come first" → change the phase order |
| Team composition | Orchestrator + agents | "These two could be merged" → merge agents |
| Missing trigger | Skill description | "It doesn't work with this phrasing" → expand the description |
| Unsuitable execution mode | Orchestrator | "It's the same fan-out every time, and slow" → switch to workflow mode |
| Scale/cost | Orchestrator | "It uses too many tokens" → reduce the default scale, add budget integration |

**Scope decision:** If adding/removing agents or redesigning the architecture is needed, don't do it directly in this skill; guide the user to the harness skill (the extend-existing-configuration procedure in step 0). evolve focuses on **adjusting the existing configuration**.

### Phase 3: Generalize and reflect

1. **Generalize the feedback** — a narrow fix that fits only a specific case is overfitting. Not "the introduction was long in this report" → "keep the introduction within 10% of the whole", but find why it got long (no length-allocation criteria in the skill) and fix it at the level of principle
2. **Record the why alongside** — note the reason next to revised instructions. Knowing the reason, agents judge correctly even in edge cases
3. Apply changes one at a time, and run Phase 4 right after each change
4. **Prevent regression:** if a fix goes in the direction of undoing an earlier fix in the change history, tell the user about the conflict and get confirmation (if it was shortened in the past for being "too long" and is now "too short", the right answer is to find criteria that satisfy both)
5. **Keep the language of the existing files** — write sentences reflected into agents, skills, orchestrators, and `CLAUDE.md` in the language already used in the target file. Don't mix English sentences into a harness written in another language just because this skill document is in English

### Phase 4: Update the change history and verify

1. Record in the **change history** table of CLAUDE.md:

```markdown
**Change history:**
| Date | Change | Target | Reason |
|------|----------|------|------|
| 2026-07-19 | Added tone guide | skills/content-creator | "Too stiff" feedback |
```

2. Verify the structure of the modified files (frontmatter, reference consistency)
3. If the description was modified, run trigger verification (3 or more each of should-trigger + near-miss)
4. Final check of whether CLAUDE.md and the actual files match

### Phase 5: Report the evolution

Report to the user:
- A summary of the captured delta (initial configuration → current)
- The changes reflected this time and their generalization rationale
- Feedback decided not to be reflected, and why (if any)
- Improvements expected in the next run

## Principles

- **The delta is an asset** — the more the change history accumulates, the more the next harness build in the same domain starts from "a draft closer to release state". Don't delete the history
- **No reflecting without generalizing** — adding one rule per case 1:1 turns the skill into a pile of rules. Compress into principles
- **One at a time** — applying several changes together makes it impossible to know which change had the effect
