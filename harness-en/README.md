# HarnessWeaver — English Agent Skills

The HarnessWeaver English skill set for designing and evolving agent harnesses, with a separate DeepAgents mapping guide.

The active skill sources in this checkout live under `harness-en/skills/`:

| Skill | Directory | What it does |
|-------|-----------|--------------|
| **harness** | `harness-en/skills/harness/` | Designs a task-specific harness from project and domain context. It uses HarnessSpec for reusable or complex designs and keeps runtime output adapter-specific. |
| **evolve** | `harness-en/skills/evolve/` | Generalizes feedback and routes changes to the spec, runtime adapter, domain guidance, or project harness while preserving history. |
| **deepagents-port** | `harness-en/skills/deepagents-port/` | Maps a HarnessSpec or existing harness to DeepAgents stages, skills, JSON contracts, and a backend handoff; reports fidelity limits. |

## Runtime choices

The architect can choose a skill-oriented harness or a DeepAgents backend when the selected adapter supports the declared design. When a HarnessSpec is present, it guides either form. The current DeepAgents skill emits a backend handoff and mapping report; it does not claim that every application is wired or executable without application-specific work.

1. Use `harness` to design the domain workflow and select the target form.
2. For DeepAgents, use `deepagents-port` to map the spec into stage instructions, skills, JSON artifact contracts, and a `port-manifest.md`; application wiring remains a separate integration step.

**Prerequisite for porting:** the coding agent doing the port should also have the official [langchain-skills](https://github.com/langchain-ai/langchain-skills) installed (`deep-agents-core`, `deep-agents-orchestration`, `deep-agents-memory`, `langgraph-human-in-the-loop`, …), since `deepagents-port` defers to them for all code-side decisions:

```shell
npx skills add langchain-ai/langchain-skills --skill '*' --yes
```

```
harness skill ──► .claude/ harness (test in Claude Code)
                          │
                          ▼  deepagents-port (Phase B)
              stage{N}/AGENTS.md + skills/*/SKILL.md
              + JSON contracts + port-manifest.md ──► DeepAgents app
```

## Quick install

### Claude Code (project-level)

```shell
cd your-project
cp -r /path/to/harness-weaver/harness-en/skills/harness .claude/skills/harness
cp -r /path/to/harness-weaver/harness-en/skills/evolve   .claude/skills/evolve
```

### Claude Code (user-level, all projects)

```shell
cp -r /path/to/harness-weaver/harness-en/skills/harness ~/.claude/skills/harness
cp -r /path/to/harness-weaver/harness-en/skills/evolve   ~/.claude/skills/evolve
```

### Other agents (Agent Skills standard)

These skills follow the [Agent Skills](https://agentskills.io) open standard, so they work with any agent that supports it. See [the setup guide](../../docs/manual-setup_EN.md) for per-agent paths:

- **Cursor**: `.agents/skills/` or `~/.agents/skills/`
- **Gemini CLI**: `.gemini/skills/` or `~/.gemini/skills/`
- **OpenCode**: `.opencode/skills/` or `~/.config/opencode/skills/` (also reads `.claude/skills/`)
- **Others** (Amp, OpenHands, and more): see [agentskills.io](https://agentskills.io)

> **Note on portability:** The skills' guidance is portable across agents, but it references Claude Code–specific capabilities — the `Workflow` tool, `Agent(name:)`, `SendMessage`, task tools. Agents without these tools can still follow the general methodology (domain analysis, team patterns, skill writing, verification), but the full multi-agent orchestration described is Claude Code–native. The `evolve` skill needs only git + the file system, so it is fully portable.

## Verifying the install

After copying, ask your agent in any project:

```
build a harness for this project
```

The harness skill should trigger on that request. To test evolve:

```
run a harness retrospective
```

## What's inside

```
 harness-en/
├── README.md                  # this file
└── skills/
    ├── harness/               # the factory skill
    │   ├── SKILL.md           # 8-step procedure, principles, artifact checklist
    │   └── references/        # 9 deep-dive reference documents
    │       ├── execution-modes.md
    │       ├── model-selection-guide.md
    │       ├── orchestrator-template.md
    │       ├── qa-agent-guide.md
    │       ├── skill-testing-guide.md
    │       ├── skill-writing-guide.md
    │       ├── team-examples.md
    │       ├── team-patterns.md
    │       └── workflow-recipes.md
    └── evolve/                # the evolution skill
        └── SKILL.md
```

## Version

Tracks the main repo: harness v2.1.0. Translation of the Korean originals at the same release.

## Relationship to the main repo

This checkout's active English skills are in `harness-en/skills/`. They are not generated from a root `skills/` directory in this repository. The skill materials originated in the [revfactory/harness project](https://github.com/revfactory/harness); check that project for its own plugin/marketplace distribution:

```shell
/plugin marketplace add revfactory/harness
/plugin install harness@harness-marketplace
```

For the full English documentation set — quickstart, v1→v2 migration, and manual setup — see [`docs/`](../../docs/).
