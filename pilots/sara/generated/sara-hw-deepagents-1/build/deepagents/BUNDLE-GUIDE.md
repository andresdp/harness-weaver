# sara DeepAgents runtime bundle

This folder is a portable **deepagents** bundle generated for the `sara` pilot.

## What it contains

A generated DeepAgents runtime implementation with stage instructions, orchestration wiring, artifact contracts, and a materialization report.

## Structure

`wiring.yaml` maps the pipeline; `stage*/` contains each stage's agent instructions and skills; `contracts/` contains artifact schemas; `README.md` has domain details.

## How to run it

From the HarnessWeaver repository root, create an isolated execution sandbox, replacing the bundle path, case name, and model:

```shell
hw sandbox create-execution sara --target deepagents --bundle <path-to-this-bundle> --case <case> --model <provider:model>
```

Configure the provider credentials in the environment or sandbox `.env`, then run `./run.sh` there. The execution runbook lists checks and recording steps.

The ZIP next to this bundle folder contains this guide and the complete bundle tree. Keep the guide with the files when moving or sharing the bundle.
