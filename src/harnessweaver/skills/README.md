# HarnessWeaver generation skills

Two [Agent Skills](https://agentskills.io) used by a coding agent (for example Claude Code) to generate and revise agent harnesses:

| Skill | What it does |
|---|---|
| **harness** | Interactive generation. Takes authored sources (intent, methodology, domain knowledge) or harvests them from an existing application. Designs a HarnessSpec, asks which runtime target(s) to generate (**Claude Code**, **DeepAgents**, or both), and materializes each target from the same spec with a materialization report. |
| **evolve** | Revision. Classifies run results and feedback, changes the right layer (sources, spec, target mapping or host), and regenerates the affected targets through `harness`. |

```text
sources/ (intent, methodology, domain)                 harness-answers.yaml (optional, replays gate answers)
        │                                                        │
        ▼                                                        ▼
  harness: G0 intake → G1 clarify → G2/G3 design → HarnessSpec + design-notes.md (hw validate)
        │
        ▼  G4 target? G5 specifics, G6 confirm
  ┌─────┴───────────────────────────┐
  ▼                                 ▼
build/claude/                     build/deepagents/
 .claude/agents, .claude/skills,   stage{N}-*/AGENTS.md + skills/,
 CLAUDE.md                         wiring.yaml (+ port-manifest.md for an existing app)
 materialization-report.md         materialization-report.md
        │                                 │
        ▼                                 ▼
   Claude Code CLI              HarnessWeaver stage host / existing app
        └──────────── results, reviews ──▶ evolve ──▶ sources/spec ──▶ harness (regenerate)
```

## Layout

```text
src/harnessweaver/skills/
├── README.md
├── harness/
│   ├── SKILL.md                         # runtime-neutral procedure and gates
│   └── references/
│       ├── question-gates.md            # gates G0–G6 and the answers file
│       ├── intake-and-harvest.md        # design inputs; harvesting from an existing app
│       ├── materialization-report.md    # fidelity report template
│       ├── targets/
│       │   ├── claude-code.md           # Claude Code project target
│       │   ├── deepagents.md            # DeepAgents stage-pipeline target
│       │   ├── deepagents-target-pattern.md
│       │   └── deepagents-mapping-table.md
│       └── execution-modes.md, orchestrator-template.md, workflow-recipes.md,
│           model-selection-guide.md, qa-agent-guide.md        # Claude Code details
│           team-patterns.md, team-examples.md,
│           skill-writing-guide.md, skill-testing-guide.md     # shared design guidance
└── evolve/
    └── SKILL.md
```

## Installing into a coding agent

Copy (or symlink) both skills into the agent's skill directory:

```shell
cp -r /path/to/harness-weaver/src/harnessweaver/skills/harness .claude/skills/harness
cp -r /path/to/harness-weaver/src/harnessweaver/skills/evolve  .claude/skills/evolve
```

For the DeepAgents target, also install the official [langchain-skills](https://github.com/langchain-ai/langchain-skills). The target reference defers to them on code-side questions:

```shell
npx skills add langchain-ai/langchain-skills --skill '*' --yes
```

Other agents that support Agent Skills can use the same directories (see [the setup guide](../../../legacy/revfactory-harness/manual-setup_EN.md) for per-agent paths). The Claude Code target's orchestration details (`Workflow`, `Agent(name:)`, `SendMessage`) are Claude Code–native; the rest of the method is portable.

## Provenance

The skill materials originated in [revfactory/harness](https://github.com/revfactory/harness) (harness v2.1.0). HarnessWeaver changed them in four ways:

- the runtime-neutral HarnessSpec design phase;
- the question gates with target selection;
- the DeepAgents target (formerly a separate `deepagents-port` skill, merged on 2026-10-24);
- materialization reports.

Upstream changes are not synchronized automatically. Reconcile them against HarnessWeaver's contracts and record the upstream release here.
