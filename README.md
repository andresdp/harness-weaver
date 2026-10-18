# HarnessWeaver

HarnessWeaver develops a runtime-neutral contract and tools for designing, validating, and evaluating agent harnesses. The implementation roadmap is in [docs/harnessweaver-implementation-roadmap.md](docs/harnessweaver-implementation-roadmap.md).

## Repository map

- `docs/` — project plans, methodology, and the HarnessSpec contract.
- `specs/` — versioned machine-readable HarnessSpec schemas.
- `examples/` — small, validated workflow specifications.
- `src/harnessweaver/` — Python package and `hw` validation command.
- `benchmarks/atam/` — HarnessWeaver-owned ATAM pilot protocol and run records.
- `harness-en/skills/` — current English harness, evolve, and DeepAgents port skills.
- `STRATEGY.md` and `CONCEPTS.md` — product direction and shared terminology.
- `case-studies/` — preserved research and application projects. Changes to their code/data remain owned by those projects; HarnessWeaver adds references and adapters around them.

See [docs/consolidation-plan.md](docs/consolidation-plan.md) for the current ownership inventory and known provenance limits. Start with [the Python quickstart](docs/quickstart.md).
