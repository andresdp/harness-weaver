# Execution sandbox: run-atam-claude-banking-20261025T205340

Target: **claude**. Pilot: **atam**. Case: **banking**. Bundle: `${REPO_ROOT}/pilots/atam/generated/atam-hw-oauth-1/build/claude`.

The archived commands use `${REPO_ROOT}` and `${SANDBOX_DIR}` as portable placeholders; substitute the local paths before rerunning them.

`input/` holds only the case's generation inputs (architecture-context). Evaluator-only data was not copied.

## Run

```shell
cd ${SANDBOX_DIR}
./run.sh    # you run this one; export ANTHROPIC_API_KEY for the default ISOLATION=bare, or use ISOLATION=settings
```

## Afterwards

From the repository root:

```shell
conda run -n harness hw check ${SANDBOX_DIR}
conda run -n harness hw sandbox record ${SANDBOX_DIR}
```

`check` writes `check.json` next to this file; `record` copies the sandbox record, outputs and check result into `docs/cain-2027/evidence/run-atam-claude-banking-20261025T205340/`.
