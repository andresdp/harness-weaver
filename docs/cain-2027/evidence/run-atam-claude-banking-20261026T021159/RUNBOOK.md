# Execution sandbox: run-atam-claude-banking-20261026T021159

Target: **claude**. Pilot: **atam**. Case: **banking**. Bundle: `/Users/adiazpace/Documents/GitHub/harness-weaver/pilots/atam/generated/atam-revfactory-en-claude-1/build/claude`.

`input/` holds only the case's generation inputs (architecture-context). Evaluator-only data was not copied.

## Run

```shell
cd /Users/adiazpace/Documents/GitHub/harness-weaver-sandboxes/run-atam-claude-banking-20261026T021159
ISOLATION=settings ./run.sh    # Claude subscription OAuth; raw transcript is saved in output/
```

The launcher prints live progress and records its exit status and finish time under `record/`. Each DeepAgents stage or final Claude report receives at most one repair attempt for JSON/schema errors, based only on deterministic structural validation. Pilot-specific evaluation and reference-leakage findings are never sent back to the model. Claude execution sandboxes are single-use because the Claude session ID is fixed. For DeepAgents, `./run.sh --clean` clears the prior workspace, outputs and run records, then reruns the full pipeline from stage 1 in the same sandbox; it does not resume the failed model conversation or skip completed stages. Use `--clean` before rerunning in place so old artifacts cannot be mistaken for new results. Claude runs also save the complete JSONL event stream in `output/transcript.jsonl`.

## Afterwards

From the repository root with your HarnessWeaver Python environment active (or prefix `hw` with `conda run -n <environment> --no-capture-output`):

```shell
hw check /Users/adiazpace/Documents/GitHub/harness-weaver-sandboxes/run-atam-claude-banking-20261026T021159
hw sandbox record /Users/adiazpace/Documents/GitHub/harness-weaver-sandboxes/run-atam-claude-banking-20261026T021159
```

`check` writes `check.json` next to this file; `record` copies the sandbox record, outputs and check result into `docs/cain-2027/evidence/run-atam-claude-banking-20261026T021159/`. A report schema failure may trigger one automatic Claude repair in the launcher; review `record/check-before-repair.json` and final `check.json`. DeepAgents applies the same one-retry limit to each stage artifact it validates.
