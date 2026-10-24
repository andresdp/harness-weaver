# P2 · SARA design pilot

**Status:** not started. See [docs/cain-2027/STATUS.md](../../docs/cain-2027/STATUS.md) §3 and work items W7, W11 and W12. The approach is in [docs/cain-2027/APPROACH.md](../../docs/cain-2027/APPROACH.md).

SARA (`case-studies/software-architecture-agent/`, upstream `NicolasMP51/software-architecture-agent`, inspected revision `528ae7c`) is a bespoke application: a React frontend, a FastAPI service with Firebase/Firestore persistence, and a DeepAgents backend whose four stages are defined by `AGENTS.md` and `SKILL.md` files. The prior read-only mapping is in [docs/software-architecture-agent-mapping.md](../../docs/software-architecture-agent-mapping.md).

## Scope

- **Harvest:** in one `harness` session (gate G0 `start_from: harvest`), SARA's 4 stage `AGENTS.md` and 11 `SKILL.md` files become draft authored sources with provenance, reviewed before design.
- **Generate only the DeepAgents backend:** the same session designs a HarnessSpec and materializes the DeepAgents target (stage directories, skills, `wiring.yaml`, `port-manifest.md` for SARA as host). Gates G4 = DeepAgents and G5 host = SARA.
- **Run standalone first:** the HarnessWeaver stage host runs the generated stages from `wiring.yaml` on one input case.
- **Adapt the rest of SARA (stretch):** frontend, API, auth and Firestore persistence stay SARA's. The pilot records what must change for SARA's `PipelineService` to run the generated stage directories, as integration effort.
- **Variation (P2b, stretch):** a methodology change in `sources/` (not a runtime change), regenerated through `evolve` or a replay of the recorded gate answers.
- SARA's text is reused as domain and methodology source with provenance. Changes to SARA itself belong to its repository.

## Planned contents

```text
pilots/sara/
  sources/              # harvested, then reviewed: intent.yaml, methodology.yaml, domain/ (skills copied verbatim)
  harvest-report.md     # origin of each source item; defects found in the original (e.g., the Stage 1 call-contract mismatch)
  harnessspec.yaml      # generated design (v0.2), plus design-notes.md with gate answers
  build/deepagents/     # generated stage directories, wiring.yaml, port-manifest.md, materialization-report.md
  cases/<case>.yaml     # case binding for the input project description and requirements
  integration.md        # stretch: SARA-side changes needed to host the generated stages
```
