# Execution sandbox: run-atam-claude-banking-20261025T205340

Target: **claude**. Pilot: **atam**. Case: **banking**. Bundle: `/Users/adiazpace/Documents/GitHub/harness-weaver/pilots/atam/generated/atam-hw-oauth-1/build/claude`.

`input/` holds only the case's generation inputs (architecture-context). Evaluator-only data was not copied.

## Run

```shell
cd /Users/adiazpace/Documents/GitHub/harness-weaver-sandboxes/run-atam-claude-banking-20261025T205340
./run.sh    # you run this one; export ANTHROPIC_API_KEY for the default ISOLATION=bare, or use ISOLATION=settings
```

## Afterwards

From the repository root:

```shell
conda run -n harness hw check /Users/adiazpace/Documents/GitHub/harness-weaver-sandboxes/run-atam-claude-banking-20261025T205340
conda run -n harness hw sandbox record /Users/adiazpace/Documents/GitHub/harness-weaver-sandboxes/run-atam-claude-banking-20261025T205340
```

`check` writes `check.json` next to this file; `record` copies the sandbox record, outputs and check result into `docs/cain-2027/evidence/run-atam-claude-banking-20261025T205340/`.
