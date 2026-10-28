# HarnessWeaver

HarnessWeaver is a research prototype for describing domain-specific agentic workflows and materializing them as LLM-based assistants for different agent runtimes. It makes the workflow model explicit—its intent, domain knowledge, methodology, artifacts, state, checks, human review, and runtime requirements—so the method can be inspected separately from a particular runtime implementation.

The project is exploratory. Its Python command currently validates HarnessSpec documents; the generated Claude Code and DeepAgents workflows are pilot implementations. HarnessWeaver does not yet discover an optimal workflow automatically or guarantee equivalent behavior across runtimes.

## Quick start

Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
hw --help
```

To validate the ATAM pilot specification:

```bash
hw validate pilots/atam/harnessspec-v0.2.yaml
```

This checks the specification and its declared local references. It does not run an assistant. See the [quickstart](docs/quickstart.md) for validation details and the [pilot guide](pilots/README.md) for the current examples. Runtime pilots have additional dependencies and provider-authentication requirements; their runbooks describe those separately.

## How the project fits together

Authors describe the problem and its domain and methodology in source specifications. The HarnessWeaver generation skill uses those sources to produce a HarnessSpec intermediate representation. Runtime-specific materializers then create assistant workflows—for example, Claude Code skills and agents or a DeepAgents workflow. Checks validate bundles and execution artifacts; the `evolve` skill is intended to use run feedback to revise a workflow.

The layers are designed to keep domain and methodology content separate from runtime-specific orchestration. The pilots test this idea qualitatively; they are not yet a systematic runtime comparison.

## Repository map

- `src/harnessweaver/` — Python package and `hw` command.
- `specs/` — versioned HarnessSpec schemas.
- `pilots/` — example workflow sources, specifications, and runtime pilots.
- `benchmarks/` — validation and evaluation protocols.
- `docs/` — user guidance, design notes, and research records; see the [documentation index](docs/README.md).
- `src/harnessweaver/skills/` — the `harness` and `evolve` generation skills.
- `baselines/` and `legacy/` — pinned upstream comparison material and provenance.
- `papers/` and the external case-study snapshots are local-only and ignored by Git; their citations and source links are in [External materials](docs/external-materials.md).

## Data, credentials, and redistribution

Never commit API keys, local settings, private case data, or unreviewed run output. The repository contains historical execution evidence, copied research materials, and case-study content that need a provenance and redistribution review before a public release. The [public-release checklist](docs/PUBLIC-RELEASE-CHECKLIST.md) records the current findings and release gates.

The [MIT License](LICENSE) covers original HarnessWeaver materials only. Third-party components keep their own terms; see [Third-party notices](THIRD-PARTY-NOTICES.md). Local paper and case-study copies are excluded from Git and are not covered by the repository license.

## Development

See [docs/quickstart.md](docs/quickstart.md) for the project validation workflow. The runtime-specific READMEs under `pilots/` document pilot setup and execution. Changes to a pilot should include the relevant source, contracts, generated-workflow implications, and validation evidence.
