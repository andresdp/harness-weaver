# P2 · SARA design pilot

**Status:** not started. See [docs/cain-2027/STATUS.md](../../docs/cain-2027/STATUS.md) §3 and gap G9.

SARA (`case-studies/software-architecture-agent/`, upstream `NicolasMP51/software-architecture-agent`, inspected revision `528ae7c`) is a bespoke application: a React frontend, a FastAPI service with Firebase/Firestore persistence, and a DeepAgents backend whose four stages are defined by `AGENTS.md` and `SKILL.md` files. The prior read-only mapping is in [docs/software-architecture-agent-mapping.md](../../docs/software-architecture-agent-mapping.md).

## Scope

- **HarnessWeaver generates (or approximates) only the DeepAgents backend**: stage agents, skills, artifact contracts, and orchestration, from a HarnessSpec v0.2 that uses `sequential_pipeline + typed_artifact_handoffs`.
- **The rest of SARA** (frontend, API, auth, Firestore persistence) stays SARA's; the pilot determines what adaptation is needed to connect it to the generated backend and records that adaptation as integration effort.
- SARA's stage and skill text is reused as domain/methodology source with provenance. Changes to SARA itself belong to its repository.

## Planned contents

- `harnessspec.yaml`: intent, methodology (four stages, eleven tasks), artifacts, checks.
- `methodology.yaml`: stage/task order, readiness and completion criteria derived from the stage `AGENTS.md` files.
- `deepagents/`: generated backend and materialization manifest.
- `integration.md`: interface between SARA's `PipelineService`/Firestore backend and the generated backend; required changes and their owners.
