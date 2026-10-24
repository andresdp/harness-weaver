# HarnessWeaver

HarnessWeaver develops a runtime-neutral contract and tools for designing, validating, and evaluating agent harnesses. The implementation roadmap is in [docs/harnessweaver-implementation-roadmap.md](docs/harnessweaver-implementation-roadmap.md).

## Repository map

- `docs/` — project plans, methodology, and the HarnessSpec contract; see [docs/README.md](docs/README.md). CAIN 2027 submission status: [docs/cain-2027/STATUS.md](docs/cain-2027/STATUS.md).
- `specs/` — versioned machine-readable HarnessSpec schemas.
- `pilots/` — pilot harnesses (HarnessSpec, methodology, runtime realizations); see [pilots/README.md](pilots/README.md) for which are active.
- `src/harnessweaver/` — Python package and `hw` validation command.
- `benchmarks/atam/` — HarnessWeaver-owned ATAM pilot protocol and run records.
- `src/harnessweaver/skills/` — the two generation skills (`harness`, `evolve`) used by a coding agent; see [its README](src/harnessweaver/skills/README.md).
- `STRATEGY.md` and `CONCEPTS.md` — product direction and shared terminology.
- `case-studies/` — preserved research and application projects. Changes to their code/data remain owned by those projects; HarnessWeaver adds references and adapters around them.

See [docs/consolidation-plan.md](docs/consolidation-plan.md) for the current ownership inventory and known provenance limits. Start with [the Python quickstart](docs/quickstart.md).
