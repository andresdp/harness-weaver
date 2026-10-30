# Anonymous reviewer artifact

This clean snapshot contains the HarnessWeaver implementation and specifications, ATAM and SARA pilot material, generated bundles (including Revfactory baseline materializations), minimal case inputs, and recorded execution evidence. It has a single anonymous root commit and no source-repository history.

## Reproduce

Install Python 3.10 or newer, then install the project and DeepAgents dependencies:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[deepagents]'
```

Create execution sandboxes from the repository root using these saved materializations:

### ATAM / Banking

```sh
hw sandbox create-execution atam --target claude --bundle pilots/atam/generated/atam-hw-oauth-1/build/claude --case banking
hw sandbox create-execution atam --target deepagents --bundle pilots/atam/generated/atam-hw-oauth-1/build/deepagents --case banking --model openai:gpt-5.4-mini
hw sandbox create-execution atam --target claude --bundle pilots/atam/generated/atam-revfactory-en-claude-1/build/claude --case banking
```

### SARA / CampusBike

```sh
hw sandbox create-execution sara --target claude --bundle pilots/sara/generated/sara-hw-claude-2/build/claude --case campus-bike
hw sandbox create-execution sara --target deepagents --bundle pilots/sara/generated/sara-hw-deepagents-1/build/deepagents --case campus-bike --model openai:gpt-5.4-mini
hw sandbox create-execution sara --target claude --bundle pilots/sara/generated/sara-revfactory-en-claude-1/build/claude --case campus-bike
```

Each command prints the sandbox path. Change into that directory and run `./run.sh`. After completion, return to the repository and run `hw check <sandbox>` and `hw sandbox record <sandbox>`. Historical execution records are in `docs/cain-2027/evidence/`.

Claude targets use Claude Code subscription OAuth. DeepAgents targets require credentials for the selected model provider.

## Input and redistribution boundary

The ATAM Banking case contains generation inputs only; evaluator-only reference outputs were removed. The SARA CampusBike case contains the project description and requirements, with an empty evaluator-only section. Full third-party repositories and compiled paper PDFs are excluded. SARA provenance is documented under `pilots/sara/sources/`. Generated SARA bundles are retained as experiment artifacts; this does not change upstream licenses or establish additional redistribution rights. Revfactory attribution and license information remain in `THIRD-PARTY-NOTICES.md` and the baseline directory.

## Anonymity

The snapshot is built with an anonymous root commit and sanitized local paths/session identifiers. Its manuscript copy omits the author-identifying ReArch citation. Inspect the final anonymous mirror and its rendered manuscript before sharing.
