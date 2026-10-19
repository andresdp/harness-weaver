# ATAM Evaluation DeepAgents Backend

This is the DeepAgents realization of the same ATAM methodology profile and report contract used by the Claude plugin in `../claude-plugin/`.

## Setup

Install the optional runtime dependencies into the repository's `harness` Conda environment:

```bash
# Install the optional backend dependencies into the project's harness environment.
conda run -n harness python -m pip install -r examples/atam/deepagents/requirements.txt
```

Set `HW_ATAM_MODEL` and the provider key in the repository-root `.env` file. For example:

```dotenv
# Choose a provider:model and provide the matching provider credential.
HW_ATAM_MODEL=openai:gpt-5.4-mini
OPENAI_API_KEY=your-key
```

The runner loads `.env` without overriding environment variables already set by your shell. OpenAI and Anthropic integrations are included; use the matching `provider:model` value and API key.

## Run

From this directory, run:

```bash
# Run from this directory; the output path is created if its parent is missing.
conda run -n harness python run.py ../../../case-studies/architecture-eval/ATAM/data/banking.json --output ./runs/banking-report.json
```

The runner reads only `ATAM_Evaluation.evaluation_inputs`. Reference outputs are not passed to the agent. The report is emitted to the requested path and requires architect review before decision use.

DeepAgents requests the generated metadata and ATAM findings through a Pydantic `response_format`. The runner validates that typed response, attaches the original `evaluation_inputs`, then checks the final report against the required template sections.

This demo backend uses one Deep Agent with ATAM specialist subagents and the shared local skills. The agent's built-in filesystem writes are denied; the Python runner writes the final report after validating its structure. The shared workflow guides activity order, while DeepAgents delegates within that workflow; this does not claim semantic equivalence with the Claude plugin.
