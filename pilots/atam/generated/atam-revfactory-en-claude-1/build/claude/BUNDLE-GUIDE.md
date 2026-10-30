# atam Claude Code runtime bundle

This folder is a portable **claude** bundle generated for the `atam` pilot.

## What it contains

A generated Claude Code implementation of the domain workflow, including its orchestrator instructions, domain skills and agents, validation helpers, and materialization report when present.

## Structure

`CLAUDE.md` is the entry point; `.claude/agents/` and `.claude/skills/` hold runtime instructions; supporting contracts and scripts remain beside them.

## How to run it

From the HarnessWeaver repository root, create an isolated execution sandbox, replacing the bundle path and case name:

```shell
hw sandbox create-execution atam --target claude --bundle <path-to-this-bundle> --case <case>
```

Then follow the printed runbook; for Claude OAuth, run `ISOLATION=settings ./run.sh` inside that execution sandbox.

The ZIP next to this bundle folder contains this guide and the complete bundle tree. Keep the guide with the files when moving or sharing the bundle.
