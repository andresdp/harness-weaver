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

Each invocation prints a unique session ID, which is also attached as the LangGraph root run ID. When streaming with verbose output, the console shows subagent calls, skill instruction/reference reads, and tool calls with truncated arguments. Reports contain the session ID in their title and filename, such as `banking-report-<session-id>.json`.

The runner reads only `ATAM_Evaluation.evaluation_inputs`; reference outputs are not sent to the agent. The coordinator delegates analysis to `quality-attribute-analyst`, then asks `evidence-reviewer` to check coverage and evidence before returning the report. DeepAgents requests generated metadata and ATAM findings through a Pydantic `ToolStrategy`; the runner attaches the original inputs and validates the final document with the Pydantic report contract. Reports require architect review before decision use.

## Code layout

- `run.py`: CLI entry point.
- `atam_harness/config.py`: YAML settings, CLI overrides, and resolved run configuration.
- `atam_harness/models.py`: Pydantic case, report, and agent-configuration contracts. The shared `report-template.json` remains the readable example of the report shape.
- `prompts/`: editable coordinator and evaluation prompts.
- `atam_harness/agents.py` and `atam_harness/agents.yaml`: DeepAgents setup and externally defined specialists.
- `atam_harness/execution.py`: streaming and non-streaming execution paths with one final-state contract.
- `atam_harness/progress.py`: console event formatting.
- `atam_harness/reports.py`: typed case loading, report composition, validation, and output serialization.
- `atam_harness/runner.py`: end-to-end run coordination.
