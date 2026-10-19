# ATAM Evaluation DeepAgents Backend

This is the DeepAgents realization of the ATAM methodology profile and report contract used by the Claude plugin in `../claude-plugin/`.

## Setup

Install the optional runtime dependencies into the repository's `harness` Conda environment:

```bash
conda run -n harness python -m pip install -r examples/atam/deepagents/requirements.txt
```

Set the provider key in the repository-root `.env` file. The model defaults to the value in the case-study `settings.yaml`; `HW_ATAM_MODEL` or `--model` can override it.

```dotenv
OPENAI_API_KEY=your-key
```

## Configuration and run

The runner loads `settings.yaml` from the root of the case study. For this example, that file is `case-studies/architecture-eval/ATAM/settings.yaml`:

```yaml
case: data/banking.json
output: ../../../examples/atam/deepagents/runs/banking-report.json
model: openai:gpt-5.4-mini
harness_spec: ../../../examples/atam/harnessspec-v0.2.yaml
streaming: true
verbose: true
```

Paths in YAML are resolved relative to the case-study root. Settings can be overridden by command-line options. The model precedence is `--model`, `HW_ATAM_MODEL`, YAML, then the built-in default.

Run with all settings from YAML:

```bash
conda run -n harness python run.py
```

Pass a case and output path explicitly, preserving the positional case argument supported by earlier versions:

```bash
conda run -n harness python run.py ../../../case-studies/architecture-eval/ATAM/data/banking.json --output ./runs/banking-report.json
```

To choose a case study explicitly (for example, when the case path is not provided), use `--case-study`. `--case` is also available as a named alternative to the positional case argument. `--streaming`/`--no-streaming` select event streaming; `--verbose`/`--no-verbose` control progress display independently:

```bash
conda run -n harness python run.py --case-study ../../../case-studies/architecture-eval/ATAM --no-streaming --no-verbose
```

## Coordination profiles

The v0.2 HarnessSpec declares workflow coordination separately from agent interaction. CLI options override each dimension independently, and the supported pairings are validated before the model is initialized:

| Workflow strategy | Agent interaction | Runtime mapping |
|---|---|---|
| `supervisor` | `one_shot_specialist_delegation` | The existing ATAM coordinator delegates once to its named analyst and evidence reviewer. |
| `sequential_pipeline` | `typed_artifact_handoffs` | Context, analysis, and review agents run in order; each consumes prior Pydantic artifacts. |
| `fan_out_fan_in` | `parallel_specialist_delegation` | Context, utility-tree, and scenario-analysis specialists run concurrently; a reviewer joins their typed outputs. |

For example:

```bash
conda run -n harness python run.py --workflow-strategy sequential_pipeline --agent-interaction typed_artifact_handoffs
conda run -n harness python run.py --workflow-strategy fan_out_fan_in --agent-interaction parallel_specialist_delegation
```

Streaming and verbose logging remain presentation settings independent of coordination. The runner prints the effective HarnessSpec path and selected values in its dimmed YAML settings block. Each report keeps the common Pydantic ATAM contract and a session-specific filename.

Each invocation prints a unique session ID, which is also attached as the LangGraph root run ID. When streaming with verbose output, the console shows subagent calls, skill instruction/reference reads, and tool calls with truncated arguments. Reports contain the session ID in their title and filename, such as `banking-report-<session-id>.json`.

The runner reads only `ATAM_Evaluation.evaluation_inputs`; reference outputs are not sent to any strategy. DeepAgents requests generated artifacts through Pydantic `ToolStrategy` schemas; the report runner attaches the original inputs and validates the final document with the shared Pydantic report contract. Pipeline handoffs and fan-out joins fail before report publication if a required typed artifact is absent. Reports require architect review before decision use.

The runtime-neutral contracts and strategy algorithms live under `src/harnessweaver/runtime/`; DeepAgents construction is isolated under `src/harnessweaver/adapters/deepagents/`. Optional provider and LangGraph dependencies are installed with `pip install -e '.[deepagents]'` when needed. Persistent peer-to-peer agent messaging and shared task-list collaboration are not mapped by this first adapter.

## Code layout

- `run.py`: CLI entry point.
- `atam_harness/config.py`: YAML settings, CLI overrides, and resolved run configuration.
- `atam_harness/models.py`: Pydantic case, report, and agent-configuration contracts. The shared `report-template.json` remains the readable example of the report shape.
- `prompts/`: editable coordinator and evaluation prompts.
- `atam_harness/agents.py` and `atam_harness/agents.yaml`: DeepAgents setup and externally defined specialists.
- `atam_harness/orchestration.py` and `prompts/orchestration.yaml`: ATAM typed stages and specialist calls for sequential and fan-out/fan-in modes.
- `atam_harness/execution.py`: streaming and non-streaming execution paths with one final-state contract.
- `atam_harness/progress.py`: console event formatting.
- `atam_harness/reports.py`: typed case loading, report composition, validation, and output serialization.
- `atam_harness/runner.py`: end-to-end run coordination.
