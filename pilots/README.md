# Pilots

Each pilot pairs a domain methodology with a HarnessSpec and one or more runtime realizations. Status and remaining work for the CAIN 2027 submission are tracked in [docs/cain-2027/STATUS.md](../docs/cain-2027/STATUS.md).

| Pilot | Directory | Domain / method | Realizations | Status |
|---|---|---|---|---|
| **P1 · ArchEval-ATAM** | [`atam/`](atam/) | Architecture evaluation / ATAM (banking case from `case-studies/architecture-eval/`) | To generate: Claude Code project and DeepAgents stage pipeline (`build/`). Reference realizations (hand-written): `claude-plugin/`, `deepagents/` | **Active** |
| **P2 · SARA** | [`sara/`](sara/) | Architecture design: requirements → drivers → alternatives → evaluation → ADR (`case-studies/software-architecture-agent/`) | To generate: DeepAgents stage pipeline harvested from SARA, hosted standalone and then by SARA's application | **Active**, not started |
| SAAM (WRCS) | [`saam/`](saam/) | Architecture evaluation / SAAM | DeepAgents (Pydantic report) | Parked |
| ADD design exploration | [`design-exploration/`](design-exploration/) | Architecture design / ADD | None (profile and review protocol only) | Parked |

Parked pilots keep their tests and remain valid examples; they are not part of the submission's evidence.

Each active pilot gets the layout in [APPROACH.md](../docs/cain-2027/APPROACH.md) §2: authored `sources/`, a generated `harnessspec.yaml` with `design-notes.md`, generated targets under `build/<target>/`, and case bindings under `cases/`.
