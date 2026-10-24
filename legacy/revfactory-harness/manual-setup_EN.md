# Manual Setup Guide — Installing Harness Skills Without the Marketplace

This guide covers installing the harness skills by **copying files directly** into your project or home directory — no Claude Code plugin marketplace, no plugin system. Use this when you can't or don't want to install plugins, or when you're using a coding agent other than Claude Code.

For the standard marketplace install, see [quickstart_EN.md](quickstart_EN.md). The maintained skill sources live in [`src/harnessweaver/skills/`](../../src/harnessweaver/skills/).

Set `HARNESSWEAVER_ROOT` to the local HarnessWeaver checkout before copying skills, for example `export HARNESSWEAVER_ROOT=/path/to/harness-weaver`.

---

## What you're installing

HarnessWeaver ships two generation skills (the DeepAgents and Claude Code targets are references inside `harness`):

| Skill | Location in this repo | Role |
|-------|----------------------|------|
| **harness** | `src/harnessweaver/skills/harness/` | The factory — designs an agent team + skills for your project |
| **evolve** | `src/harnessweaver/skills/evolve/` | The evolution mechanism — feeds run feedback back into the harness |

The skills in `src/harnessweaver/skills/` are the maintained source tree. Each skill has a `SKILL.md`; the harness skill also has supporting references.

## Compatibility notes

- **Skill format:** Both editions follow the [Agent Skills](https://agentskills.io) open standard — a directory containing `SKILL.md` with YAML frontmatter (`name`, `description`). Any agent that supports the standard can load them.
- **Runtime features:** The harness skill's guidance leans on Claude Code–specific capabilities: the `Workflow` tool, `Agent(name:)` spawns, `SendMessage`, task tools, `.claude/agents/` custom agent types. On other agents, the methodology (domain analysis, team patterns, skill writing, verification) still applies, but you may need to adapt tool references to your agent's equivalents. The `evolve` skill needs only git + the file system, so it is fully portable.

## Claude Code

Claude Code discovers skills from `.claude/skills/` in the project and `~/.claude/skills/` globally.

**Project-level (this project only):**

```shell
cd your-project

# Maintained skills
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/harness"         .claude/skills/harness
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/evolve"          .claude/skills/evolve
```

**User-level (all your projects):**

```shell
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/harness"         ~/.claude/skills/harness
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/evolve"          ~/.claude/skills/evolve
```

**Verify:** start `claude` in the project and type `/` — both `harness` and `evolve` should appear, and `build a harness for this project` should trigger the harness skill. Use `/doctor` to diagnose installation issues.

## Cursor

Cursor loads skills from `.agents/skills/` or `.cursor/skills/` at project level, and `~/.agents/skills/` or `~/.cursor/skills/` globally. For compatibility it also reads `.claude/skills/` and `~/.claude/skills/`.

```shell
cd your-project
mkdir -p .agents/skills
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/harness"         .agents/skills/harness
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/evolve"          .agents/skills/evolve
```

**Verify:** start Cursor, open Agent chat, type `/` and search for `harness`. Skills are discovered automatically on startup; Agent decides relevance from your request context, and you can pin a skill for a whole session via Custom Modes.

## Gemini CLI

Gemini CLI discovers skills from `~/.gemini/skills/` (user) and `.gemini/skills/` or `.agents/skills/` (workspace), with `.agents/skills/` taking precedence within a tier. Activation requires your consent in the UI.

```shell
cd your-project
mkdir -p .agents/skills
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/harness"         .agents/skills/harness
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/evolve"          .agents/skills/evolve
```

**Verify:** run `/skills list` in a session; the installed skills should appear. Use `/skills disable <name>` / `/skills enable <name>` to manage them.

## OpenCode

OpenCode searches `.opencode/skills/`, `.claude/skills/`, and `.agents/skills/` (project), plus their global equivalents under `~/.config/opencode/` and `~/.claude/`.

```shell
cd your-project
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/harness"         .claude/skills/harness
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/evolve"          .claude/skills/evolve
```

**Verify:** skills appear in the `skill` tool description; the agent loads them on demand by name.

## Other agents

Any agent that supports the [Agent Skills](https://agentskills.io) standard can consume these skills — the standard dictates the same `SKILL.md` + frontmatter format. Check your agent's docs for its skills directory:

- **Amp**: `AGENT.md`-based configuration; skills supported via the standard
- **OpenHands**: `.agents/skills/` and `~/.agents/skills/`
- **Codex**: `.codex/skills/`
- **Others**: see [agentskills.io](https://agentskills.io)

When in doubt, the `.agents/skills/` path is emerging as the cross-agent convention — several tools read it natively, and Claude Code reads `.claude/skills/`.

## Using the skills once installed

In any project:

```
build a harness for this project
design an agent team for <domain>
```

After running a generated harness:

```
run a harness retrospective
evolve the harness with this feedback
```

The factory writes its artifacts (`.claude/agents/`, `.claude/skills/`, `CLAUDE.md` entries) in the language you use in conversation — including English, regardless of which edition you installed.

## Ready-made harnesses: the harness-100 collection

If you want a harness without generating one, the author maintains [harness-100](https://github.com/revfactory/harness-100) — 100 ready-to-use harnesses (Korean + English) across 10 domains: content, DevOps, data/AI, business, education, legal, lifestyle, docs, operations, and specialized domains. Copy any of them directly:

```shell
cp -r /path/to/harness-100/en/28-security-audit/.claude/ your-project/.claude/
```

Two things to know before using them:

1. **They are v1-generation artifacts** (March 2026, predating the v2 rebuild in this repo): lowercase `skill.md` files, agent-team-only execution, no `Workflow` scripts, no model tiering. They still run under the current Claude Code runtime, but they don't follow v2 conventions.
2. **The English edition is machine-translated** from Korean and reads garbled in places; the Korean edition is the source of truth.

For v2-style prompts that regenerate selected harness-100 examples with this repo's current factory — two per category, with the expected v2 shape each would produce — see the [prompt cookbook](harness-100-prompts_EN.md).

## Companion skills for porting (langchain-skills)

The harness skill's DeepAgents target assumes the official [langchain-skills](https://github.com/langchain-ai/langchain-skills) are **installed and available to the same coding agent** that runs the port — it defers to them for code-side decisions such as factory wiring, backends, checkpointers, subagents, and interrupt/resume flows. Without them, the port still works but its Python-side output is not cross-checked against that guidance.

Install for any agent that supports the Agent Skills specification:

```shell
# any agent (Claude Code, Cursor, Codex, GitHub Copilot, …)
npx skills add langchain-ai/langchain-skills --skill '*' --yes          # project-level
npx skills add langchain-ai/langchain-skills --skill '*' --yes --global # user-level

# Claude Code plugin marketplace alternative
/plugin marketplace add langchain-ai/langchain-skills
/plugin install langchain-skills@langchain-skills
```

The relevant skills for harness porting are `deep-agents-core` (agent creation, middleware, SKILL.md format), `deep-agents-orchestration` (subagents), `deep-agents-memory` (stores/backends), and `langgraph-human-in-the-loop` (approval flows) — see the repo's README for the full list and its dedicated install script.

## Keeping skills updated

The skills are plain files, so updating means re-copying:

```shell
cd your-project
git -C /path/to/harness pull   # or download the latest copy
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/harness"         .claude/skills/harness
cp -r "$HARNESSWEAVER_ROOT/src/harnessweaver/skills/evolve"          .claude/skills/evolve
```

Consider committing the installed skills to your project's repo so teammates inherit them via version control, and so the `evolve` skill's change history stays durable.

## Uninstall

Delete the copied directories:

```shell
```

Generated harness artifacts in other projects (`.claude/agents/`, `.claude/skills/`, `CLAUDE.md` pointers) are independent of the skills that created them and keep working after uninstall.
