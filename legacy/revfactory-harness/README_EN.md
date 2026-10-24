<p align="center">
  <img src="https://img.shields.io/badge/Version-2.1.0-brightgreen.svg" alt="Version">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-purple.svg" alt="Claude Code Plugin">
  <img src="https://img.shields.io/badge/Execution_Modes-3-teal.svg" alt="3 Execution Modes">
  <img src="https://img.shields.io/badge/Patterns-6+Quality-orange.svg" alt="Patterns">
</p>

<p align="center">
  <a href="https://revfactory.github.io/harness-animation/">
    <img src="harness_reel_en.gif" alt="Harness in 15 seconds: one request becomes an agent team" width="800">
  </a>
  <br>
  <sub>15-second motion reel · <a href="https://revfactory.github.io/harness-animation/">Watch the full 2-minute interactive walkthrough (Korean) →</a></sub>
</p>

# HarnessWeaver — Runtime-Neutral Harness Design

> HarnessWeaver designs and validates agent harnesses from user intent, domain knowledge, and methodology, then maps them to supported runtime forms. The active skill source in this checkout is `src/harnessweaver/skills/`; the upstream Claude Code plugin is a separate distribution path.

## Upstream Claude Code plugin background

The details below describe the originating `revfactory/harness` plugin and its Claude Code-specific behavior. They are distribution and runtime examples, not portable HarnessWeaver contracts. For the current product direction and implementation roadmap, see [STRATEGY.md](../../STRATEGY.md) and [the roadmap](../../docs/harnessweaver-implementation-roadmap.md).

### What's new in upstream v2

v2 is a ground-up rebuild for the current Claude Code multi-agent runtime:

- **Three native execution modes.** v1 knew two modes built on the experimental `TeamCreate` API, which no longer exists. v2 targets what actually ships today:
  1. **Workflow orchestration** — deterministic scripts (`pipeline()` / `parallel()` / schemas / budgets) for fan-outs, verification loops, and large-scale runs
  2. **Persistent agent collaboration** — named agents + `SendMessage` + shared task lists, with context retained across turns
  3. **Sub-agent delegation** — lightweight one-shot parallel dispatch
- **Workflow-native quality patterns.** Adversarial verification, judge panels, loop-until-dry, multi-modal sweeps, completeness critics — codified so generated harnesses filter out plausible-but-wrong output.
- **No experimental flags.** The `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` dependency is gone entirely.
- **Sane model policy.** v1 pinned every agent to `model: "opus"`. v2 selects a tier per agent — fable / opus / sonnet — based on the task's complexity, duration, autonomy, and latency needs, and forbids unjustified blanket pins.
- **`/harness:evolve` actually ships.** The evolution mechanism v1 only documented is now a real skill: it captures the delta between your initial and current harness, generalizes feedback, and feeds it back into agents/skills/orchestrators.
- **v1 migration built in.** The factory detects v1 artifacts (`TeamCreate`, `TeamDelete`, experimental flags) and offers a mechanical migration path.

## Core features

- **Agent team design** — six architecture patterns (Pipeline, Fan-out/Fan-in, Expert Pool, Producer-Reviewer, Supervisor, Hierarchical Delegation), each mapped to its best v2 execution mode
- **Skill generation** — context-efficient skills via Progressive Disclosure
- **Orchestration** — data-passing protocols (structured schemas, files, messages, tasks), error handling, resume support
- **Verification** — trigger evals, dry runs, with-skill vs. without-skill A/B testing (optionally as a workflow itself)
- **Evolution** — `/harness:evolve` turns usage feedback into measurable next-generation improvements

## Workflow

```
Phase 0: Audit existing harness (new / extend / maintain — v1 artifacts detected here)
Phase 1: Domain analysis (incl. control-flow shape of the work)
Phase 2: Execution mode & team architecture design
Phase 3: Agent definitions (.claude/agents/)
Phase 4: Skill generation (.claude/skills/)
Phase 5: Orchestration & CLAUDE.md pointer
Phase 6: Verification & testing
Phase 7: Maintenance — evolution via /harness:evolve
```

## Install

### Via marketplace

```shell
/plugin marketplace add revfactory/harness
/plugin install harness@harness-marketplace
```

### As global skills

```shell
cp -r src/harnessweaver/skills/harness ~/.claude/skills/harness
cp -r src/harnessweaver/skills/evolve ~/.claude/skills/evolve
```

### Install from this repository

The harness and evolve skills, installable without the marketplace or plugin system — including on agents other than Claude Code (Cursor, Gemini CLI, OpenCode, …):

```shell
cp -r /path/to/harness-weaver/src/harnessweaver/skills/harness .claude/skills/harness
cp -r /path/to/harness-weaver/src/harnessweaver/skills/evolve   .claude/skills/evolve
```

See [src/harnessweaver/skills](../../src/harnessweaver/skills) and the [manual setup guide](manual-setup_EN.md) for details.

Prefer ready-made? Browse [harness-100](https://github.com/revfactory/harness-100) — 100 pre-built harnesses across 10 domains (v1-generation; see the [setup guide](manual-setup_EN.md#ready-made-harnesses-the-harness-100-collection) for caveats and v2 regeneration prompts).

No environment variables or experimental flags required.

## Usage

```
하네스 구성해줘
build a harness for this project
design an agent team for <domain>
```

After using a generated harness:

```
하네스 회고해줘 / evolve the harness with this feedback
```

### Choosing an execution mode

| Mode | Primitive | When |
|------|-----------|------|
| **Workflow orchestration** | `Workflow` scripts | Control flow is deterministic: enumerable fan-outs, verification loops, large scale, structured outputs |
| **Persistent agents** | `Agent(name:)` + `SendMessage` + tasks | Long-lived specialists that keep context; iterative feedback and negotiation |
| **Sub-agent delegation** | one-shot `Agent` calls | Fire-and-forget parallel work; results only |

The factory picks the mode from the **shape of the control flow**, not from team size — and mixes modes per phase when that fits better.

## Generated artifacts

```
your-project/
├── .claude/
│   ├── agents/          # agent definitions (who)
│   │   ├── analyst.md
│   │   ├── builder.md
│   │   └── qa.md
│   └── skills/          # skills (how) + one orchestrator (who-when-in-what-order)
│       ├── analyze/SKILL.md
│       └── build/SKILL.md
└── CLAUDE.md            # minimal pointer: trigger rule + change history
```

## Migrating from v1

See [migration-v1-to-v2.md](migration-v1-to-v2.md). Summary: remove `TeamCreate`/`TeamDelete`/broadcast/flag references, convert fan-outs to Workflow scripts, rewrite remaining collaboration with named agents + `SendMessage`, drop blanket `model: "opus"` pins. The factory automates this when it detects v1 artifacts (Phase 0).

## Prior results (v1)

A controlled A/B on 15 software-engineering tasks measured the effect of structured pre-configuration on LLM code-agent output quality: mean quality 49.5 → 79.3 (+60%), 15/15 win rate, −32% output variance (n=15, author-run, see [revfactory/claude-code-harness](https://github.com/revfactory/claude-code-harness)). Treat these as author-measured numbers; run your own pilot for adoption decisions.

## License

Apache 2.0
