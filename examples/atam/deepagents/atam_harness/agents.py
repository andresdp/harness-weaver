"""Load external specialist definitions and construct the ATAM DeepAgent."""

from pathlib import Path
from typing import Any

import yaml

from .models import AtamReportPayload, DeepAgentDefinitions, DeepAgentSubagent
from .paths import AGENT_DEFINITIONS_PATH, EXAMPLE_DIR
from .prompts import load_prompt


def load_subagents(path: Path = AGENT_DEFINITIONS_PATH) -> list[DeepAgentSubagent]:
    """Read specialist definitions from YAML and validate each definition."""
    raw_definitions = yaml.safe_load(path.read_text(encoding="utf-8"))
    definitions = DeepAgentDefinitions.model_validate(raw_definitions)
    return definitions.subagents


def build_agent(model_name: str) -> Any:
    """Create the DeepAgent after all runtime and external agent configuration is resolved."""
    try:
        from deepagents import FilesystemPermission, create_deep_agent
        from deepagents.backends.filesystem import FilesystemBackend
        from langchain.agents.structured_output import ToolStrategy
        from langchain.chat_models import init_chat_model
    except ImportError as exc:
        raise RuntimeError(
            "DeepAgents is required for this backend; install examples/atam/deepagents/requirements.txt"
        ) from exc

    # Resolve the LangChain chat model explicitly so the provider is visible in settings.
    chat_model = init_chat_model(model_name)
    subagents = [definition.model_dump(mode="python") for definition in load_subagents()]
    return create_deep_agent(
        model=chat_model,
        system_prompt=load_prompt("system.md"),
        backend=FilesystemBackend(root_dir=str(EXAMPLE_DIR), virtual_mode=True),
        skills=["./skills/"],
        subagents=subagents,
        # ToolStrategy returns validation feedback to the model for correction.
        response_format=ToolStrategy(AtamReportPayload, handle_errors=True),
        # The agent can read supporting material but only the Python runner writes reports.
        permissions=[FilesystemPermission(operations=["write"], paths=["/**"], mode="deny")],
    )
