# v1 → v2 Migration Guide

A guide for converting harness artifacts generated with harness v1 (≤1.2.x) to the v2 runtime. When the factory (the harness skill) detects v1 artifacts in Phase 0, it automatically offers and performs this procedure. To proceed manually, follow the steps below.

## Why migration is necessary

v1 assumed the `TeamCreate`/`SendMessage`/`TaskCreate` APIs behind the experimental flag (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`). In the current Claude Code:

- `TeamCreate` / `TeamDelete` / `team_name` have been **removed** — a session has a single implicit team, and agents spawned with `Agent(name: ...)` are the team members
- `SendMessage` and shared tasks (`TaskCreate`, etc.) work **without any flag**
- A **`Workflow` tool** has been added for deterministic orchestration — a strict superset of the large-scale fan-outs and verification loops v1 emulated with teams

Running a v1 orchestrator as-is will attempt calls to non-existent tools and quietly degrade into single-agent execution. That is the first reason v2 exists.

## Conversion mapping

| v1 | v2 |
|----|----|
| `TeamCreate(team_name, members: [...])` | Spawn agents in parallel with `Agent(name: "...", ...)` in a single message |
| `TeamDelete` / "Phase N: team cleanup" | Delete (natural termination; use `TaskStop` if needed) |
| "One active team per session" constraint and team re-formation procedures | Delete (the constraint no longer exists) |
| `SendMessage({to: "all"})` broadcasts | Individual `SendMessage` calls to only the agents that need them |
| `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | Delete |
| Every agent `model: "opus"` | Remove the blanket pin → re-select fable/opus/sonnet per task profile (complexity, duration, autonomy, speed) (`references/model-selection-guide.md`) |
| Team-based large-scale fan-outs / generate-verify loops | `Workflow` scripts (`pipeline()` + `schema` + adversarial verification) |
| Phase 0 context check (`_workspace/` branching) | Keep + workflow mode adds `resumeFromRunId` |
| `_workspace/` file conventions, CLAUDE.md pointers/change history | Keep as-is |

## Manual migration procedure

1. **Audit:** grep the orchestrator/agent definitions for `TeamCreate`, `TeamDelete`, `team_name`, `to: "all"`, `EXPERIMENTAL_AGENT_TEAMS`, `model: "opus"`
2. **Re-adjudicate the mode:** for each phase, ask "can the task list, verification criteria, and loop conditions be expressed in code up front?"
   - Yes → convert to workflow mode (use the recipes in the harness skill's `references/workflow-recipes.md`)
   - No, iterative negotiation is needed → rewrite with persistent-mode syntax (`Agent(name:)` + SendMessage + Tasks)
   - No, only the result matters → simplify to one-shot sub-agent calls
3. **Clean up agent definitions:** re-select blanket `model: "opus"` into task-profile-based tiers (fable/opus/sonnet), update the `## Team communication protocol` section to match the mode (for workflow-only agents, replace it with a "structured output" section), and add `## Re-invocation guidelines`
4. **Clean up docs:** remove experimental-flag instructions from README/CLAUDE.md
5. **Verify:** run the structural validation and dry run per the harness skill's Phase 6 criteria. Do a final check that grepping for v1 artifacts returns 0 hits
6. **Record:** add a "v2 migration" row to the CLAUDE.md change history

## Automatic migration

Just ask in the project:

```
check my harness   (if v1 artifacts are detected, it will propose the migration)
```
