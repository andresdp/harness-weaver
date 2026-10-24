# Quickstart — Your First Harness in 5 Minutes

**What you'll have at the end:** a `.claude/agents/` + `.claude/skills/` directory containing 3–5 domain-specialized agents and skills, generated from a one-sentence prompt, plus the results of one sample task run.

**Prerequisites:**
- A recent version of Claude Code (`claude --version`)
- Network access to `github.com`

> Unlike v1, **no environment variables or experimental flags are required.** If you see `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, that's v1 documentation.

---

## Step 1 — Add the marketplace (30 seconds)

```
/plugin marketplace add revfactory/harness
```

## Step 2 — Install the plugin (30 seconds)

```
/plugin install harness@harness-marketplace
```

**Troubleshooting FAQ — install not showing up:** Check with `/plugin list`. If it's missing, re-run from Step 1; if it's present but disabled, run `/plugin enable harness@harness-marketplace`.

## Step 3 — Generate a harness from one sentence (2 minutes)

```
claude "build a harness for a fintech risk assessment team"
```

Other examples (all of these work):
- `claude "build a harness for an e-commerce fraud-detection workflow"`
- `claude "design an agent team for technical due diligence on open-source repositories"`

**Expected output:** a current-state audit (Phase 0) report → a proposal for execution mode and architecture → confirmation that 3–5 agent files + skills + an orchestrator were created.

## Step 4 — Verify the generated files (30 seconds)

```bash
ls -la .claude/agents/ .claude/skills/
```

**Troubleshooting FAQ — nothing was generated:** Check whether the plugin is enabled (Step 2 FAQ). If it's enabled but the skill doesn't trigger, make the trigger keywords explicit, like "build a harness".

## Step 5 — Run a sample task (90 seconds)

Hand a realistic ticket-style prompt to your new team:

```
claude "Ticket FIN-427: A new corporate client (mid-sized manufacturer, $80M revenue, Korea)
has applied for a $5M working capital line. Perform a risk assessment covering
(1) red flags in credit history, (2) sector concentration relative to the existing
portfolio, and (3) regulatory exposure (FTC, FSC), and produce a one-page memo with
a go/no-go recommendation."
```

The orchestrator skill triggers and routes the work through the team pattern it generated (for risk work, typically Producer-Reviewer or Expert Pool).

**Cost note:** Multi-agent runs can consume tens of thousands to hundreds of thousands of tokens per task. Generated orchestrators are designed to keep the default scale restrained and only expand when you ask for "thorough" or "exhaustive" runs. To set a token target yourself, include a budget directive like "+500k" in the prompt — workflow-mode harnesses use it to scale execution.

## Next steps

- If the results disappoint: `"run a harness retrospective"` → `/harness:evolve` generalizes the feedback and applies it
- If the project has a v1 harness: `"check my harness"` → it will automatically propose migration ([migration-v1-to-v2_EN.md](migration-v1-to-v2_EN.md))
- Can't or don't want to use the marketplace/plugin? Install the skills by copying files instead — see the [manual setup guide](manual-setup_EN.md), including for agents other than Claude Code
