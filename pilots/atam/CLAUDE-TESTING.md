# Claude testing handoff for the ATAM prototype

> **Superseded for the CAIN 2027 runs (2026-10-24).** Generation and Claude-target runs now use the generation and execution sandboxes in [docs/cain-2027/APPROACH.md](../../docs/cain-2027/APPROACH.md), with a `RUNBOOK.md` per sandbox. Section A below still describes the hand-maintained reference plugin. Section B's prompt is replaced by the `harness` skill's gates and `harness-answers.yaml`.

Live Claude checks are deferred. This guide prepares two later experiments: running the generated ATAM plugin, and asking Claude to generate a plugin from the shared HarnessSpec. Keep the resulting runs separate and note the Claude Code version, model, date, and any changes made to the generated files.

## A. Try the generated ATAM plugin

From the repository root, validate and launch the local plugin:

```bash
claude plugin validate pilots/atam/claude-plugin
claude --plugin-dir pilots/atam/claude-plugin
```

In the Claude Code session, use `/atam-evaluation:evaluate-architecture` with an evaluation-input-only JSON file or paste a small architecture description. Use `/atam-evaluation:check-evaluation` on the resulting draft. Check that the report follows the ATAM template, distinguishes evidence from assumptions, shows gaps, and asks for architect review. This is a qualitative smoke test; it is not evidence of ATAM completeness or accuracy.

If using the repository's banking case, give Claude only `ATAM_Evaluation.evaluation_inputs` from `case-studies/architecture-eval/ATAM/data/banking.json`. Never provide `ground_truth_outputs` to the generation or review session. If the plugin cannot select that field without reading the whole JSON, prepare an input-only copy first.

Create that safe copy from the repository root with:

```bash
conda run -n harness python -c 'import json; from pathlib import Path; source=Path("case-studies/architecture-eval/ATAM/data/banking.json"); data=json.loads(source.read_text()); target=Path("/tmp/hw-atam-evaluation-inputs.json"); target.write_text(json.dumps({"ATAM_Evaluation":{"evaluation_inputs":data["ATAM_Evaluation"]["evaluation_inputs"]}}, indent=2) + "\n"); print(target)'
```

Use `/tmp/hw-atam-evaluation-inputs.json` for the plugin smoke test. The extraction writes only the generation input field.

## B. Ask Claude to generate the ATAM plugin

Use a scratch directory so the generation experiment does not overwrite the maintained plugin. From the repository root, make the HarnessWeaver design skills available to Claude Code in that scratch project:

```bash
mkdir -p /tmp/hw-atam-generation/.claude/skills
ln -s "$PWD/src/harnessweaver/skills/harness" /tmp/hw-atam-generation/.claude/skills/harness
```

Start Claude Code in `/tmp/hw-atam-generation` and use a prompt like:

```text
Use the harness skill to materialize a Claude Code plugin for the ATAM harness
described by the HarnessSpec at:
<absolute-repository-path>/pilots/atam/harnessspec-v0.2.yaml

Read the referenced methodology, domain skills, report template, and the
evaluation-input-only case data. Keep this as an ATAM evaluation prototype.
Preserve the evaluation-input boundary: never read or copy ground_truth_outputs
into generation context or generated plugin assets. Put the generated plugin in
./generated/atam-plugin. Keep methodology progress distinct from agent/runtime
activity, preserve evidence gaps and uncertainty, and report any HarnessSpec
requirements the Claude plugin cannot represent. Do not edit the maintained
repository files.
```

Replace `<absolute-repository-path>` with the checkout's full path. If Claude Code asks for directory access, grant read access to the repository and write access only to the scratch project. After generation, review its source references and verify the generated directory independently:

```bash
claude plugin validate /tmp/hw-atam-generation/generated/atam-plugin
```

Then launch that generated plugin with `claude --plugin-dir /tmp/hw-atam-generation/generated/atam-plugin` and repeat the smoke test in section A. Compare it with `pilots/atam/claude-plugin/` against the same input-only case: required report sections, evidence traceability, explicit unknowns, and disclosed fidelity gaps. Keep the generated files and observations as experiment artifacts; do not replace the maintained plugin based on one run.

## Record the experiment

For each attempt, save the Claude Code version, model, date, exact prompt, input-file hash, generated plugin path, validation result, run output, and any manual edits. Record failures as well as successful runs. The ATAM prototype is a report-drafting aid and requires software-architect review before decision use.
