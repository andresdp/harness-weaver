# Harness → DeepAgents Mapping Table

Concept-by-concept mapping used during Phase B of the port. "Default" is what the port emits when no contrary decision is recorded; the "Alternative" column feeds the B-2 decision table in the parent `SKILL.md`.

## People and roles

| Harness concept | Target equivalent | Notes |
|---|---|---|
| Agent definition (`.claude/agents/{name}.md`) — *who* | Not a runtime object. Roles collapse into the stage's `AGENTS.md` responsibility sentence and the skills' Procedure sections | The target has one deep agent per *stage*, not per specialist. "Who" survives as prose; "what/in which order" becomes skills |
| Orchestrator skill (who-when-in-what-order) | `stage{N}/AGENTS.md` ordered task list + Python `STAGES` registry | Sequencing moves out of the LLM entirely |
| Trigger conditions in skill `description` | SKILL.md frontmatter `description` kept; triggering is *not* runtime-relevant (skills are invoked by AGENTS.md order) | Keep descriptions anyway — they document intent and aid maintainers |
| Model tier per agent (`fable`/`opus`/`sonnet` + rationale comment) | Single env-driven model per application; tier rationale kept as comments | Alternative: per-stage model choice if the factory is extended |
| `CLAUDE.md` pointer + change history | Python `stages.py`/`STAGE_ARTIFACTS` replaces the pointer; carry the change-history table into a domain README | evolve-skill compatibility |

## Data and artifacts

| Harness concept | Target equivalent | Notes |
|---|---|---|
| `_workspace/` intermediate artifacts | `/artifacts/*.json` on the composite backend (Firestore/filesystem) | Naming `{phase}_{agent}_{artifact}.{ext}` → `{NN}_{step}.json` |
| File-based data passing between phases | JSON artifacts; the *only* inter-stage channel | Matches harness's "files when data is large or must be reviewable" |
| `schema`-validated structured returns | JSON structure block in each SKILL.md + read-back verification + Mandatory Completion Protocol | Assertion is procedural (read-back), not schema-validated at the API layer — the main fidelity loss; see below |
| Structured cross-references (schema fields) | ID fields inside JSON (e.g. `source_requirement_ids`) | Never prose linkage |

## Execution and control flow

| Harness concept | Target equivalent | Notes |
|---|---|---|
| Workflow orchestration (`Workflow`, `pipeline()`, `parallel()`, `phase()`) | Python pipeline loop + AGENTS.md ordered tasks | `parallel()` semantics (barrier) are lost; serialize instead |
| Persistent agents (`Agent(name:)` + context retention) | No equivalent; a stage's context = its AGENTS.md + artifacts it reads | Iterative negotiation doesn't fit the pattern; see decisions |
| `SendMessage` agent-to-agent | Replace with artifact write/read steps | Alternative: DeepAgents subagents for genuinely iterative exchange |
| Sub-agent delegation (one-shot `Agent`) | Intra-stage: just another skill step; or DeepAgents `subagents=[…]` if isolation is needed | Default: skill step |
| Shared task list (`TaskCreate`/`TaskUpdate`) | AGENTS.md post-task protocol ("update workflow status; determine next incomplete task") | Status is self-tracked by the agent in-run; Python checks completion afterwards |

## Verification and quality

| Harness concept | Target equivalent | Notes |
|---|---|---|
| Adversarial verification (N verifiers, majority `confirmed`) | Intra-agent verification skill step (read-back + rules); or a dedicated verification stage | The majority-voting guarantee does not survive single-agent verification — record this in the port report |
| Judge panel (N drafts, parallel judging) | Not portable. Serialize: generate candidates → one selection skill | Diversity of drafts can be preserved procedurally (distinct lenses in the Procedure) |
| Loop-until-dry | A skill's Procedure can include a stopping rule (e.g. "stop when no new items for K rounds"), but no code-level loop | Weaker than `Workflow` iteration |
| Completeness critic | Final skill step of the stage, or the Mandatory Completion Protocol itself | — |
| Trigger-condition validation (should-trigger / near-miss) | Not applicable at runtime; keep as a maintenance practice in the domain README | — |
| Dry run / test scenarios (orchestrator's `## Test scenarios`) | Smoke test in `port-report.md`: minimal input → stage 1 → all artifacts valid JSON | Python-side integration test hooks can assert `STAGE_ARTIFACTS` existence |

## What has no mapping (dropped, with report entries)

- `Workflow` script features: `budget`, `resumeFromRunId`, `.filter(Boolean)`, caching semantics.
- `agentType`/`subagent_type` custom-type invocation.
- Token-budget-driven scaling (`+500k` directives).
- Experimental-flag/v1 checks (nothing to do — the source should already be v2).

## Fidelity ladder (what survives, weakest → strongest)

1. **Strongest — artifact contracts.** JSON structure blocks, filenames, ID linkage: near-lossless, and they are the application's API.
2. **Strong — procedures, rules, examples, scope boundaries.** The design intelligence; ports as content nearly verbatim.
3. **Medium — sequencing intent.** Order survives; the *mechanism* changes from skill prose + Workflow code to Python + AGENTS.md.
4. **Weak — collaboration.** Messaging, negotiation, parallel fan-outs flatten into serialized steps or subagent decisions.
5. **Weakest — probabilistic guarantees.** N-verifier majority voting, judge-panel diversity, loop-until-dry become procedural approximations.
