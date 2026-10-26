# Execution sandbox: run-atam-deepagents-banking-20261025T225711

Target: **deepagents**. Pilot: **atam**. Case: **banking**. Bundle: `/Users/adiazpace/Documents/GitHub/harness-weaver/pilots/atam/generated/atam-hw-oauth-1/build/deepagents`.

`input/` holds only the case's generation inputs (evaluation_inputs). Evaluator-only data was not copied.

## Run

```shell
cd /Users/adiazpace/Documents/GitHub/harness-weaver-sandboxes/run-atam-deepagents-banking-20261025T225711
./run.sh    # provider keys come from the environment or a .env file placed in this directory
```

The launcher prints live progress and records its exit status and finish time under `record/`. Each DeepAgents stage or final Claude report receives at most one repair attempt for JSON/schema errors, based only on deterministic structural validation. Pilot-specific evaluation and reference-leakage findings are never sent back to the model. Each execution sandbox is single-use; create a fresh one for every attempt so old artifacts cannot be mistaken for new results. Claude runs also save the complete JSONL event stream in `output/transcript.jsonl`.

## Afterwards

From the repository root with your HarnessWeaver Python environment active (or prefix `hw` with `conda run -n <environment> --no-capture-output`):

```shell
hw check /Users/adiazpace/Documents/GitHub/harness-weaver-sandboxes/run-atam-deepagents-banking-20261025T225711
hw sandbox record /Users/adiazpace/Documents/GitHub/harness-weaver-sandboxes/run-atam-deepagents-banking-20261025T225711
```

`check` writes `check.json` next to this file; `record` copies the sandbox record, outputs and check result into `docs/cain-2027/evidence/run-atam-deepagents-banking-20261025T225711/`. A report schema failure may trigger one automatic Claude repair in the launcher; review `record/check-before-repair.json` and final `check.json`. DeepAgents applies the same one-retry limit to each stage artifact it validates.
