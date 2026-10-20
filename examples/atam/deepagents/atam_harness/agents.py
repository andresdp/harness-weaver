"""Load external specialist definitions and construct the ATAM DeepAgent."""

from pathlib import Path
from typing import Any

import yaml

from .models import AtamReportPayload, DeepAgentDefinitions, DeepAgentSubagent
from .filesystem import atam_filesystem_permissions
from .paths import AGENT_DEFINITIONS_PATH, EXAMPLE_DIR
from .prompts import load_prompt


def load_subagents(path: Path = AGENT_DEFINITIONS_PATH) -> list[DeepAgentSubagent]:
    """Read specialist definitions from YAML and validate each definition."""
    raw_definitions = yaml.safe_load(path.read_text(encoding="utf-8"))
    definitions = DeepAgentDefinitions.model_validate(raw_definitions)
    return definitions.subagents


def build_deep_agent(
    model_name: str,
    request_timeout_seconds: float,
    *,
    name: str | None = None,
    system_prompt: str,
    schema: type[Any],
    subagents: list[dict[str, Any]] | None = None,
) -> Any:
    """Create an ATAM DeepAgent with the shared model, tools, and workspace setup."""
    try:
        from deepagents import create_deep_agent
        from deepagents.backends.filesystem import FilesystemBackend
        from langchain.agents.structured_output import ToolStrategy
        from langchain.chat_models import init_chat_model
    except ImportError as exc:
        raise RuntimeError(
            "DeepAgents is required for this backend; install examples/atam/deepagents/requirements.txt"
        ) from exc

    # Resolve the LangChain chat model explicitly so the provider is visible in settings.
    chat_model = init_chat_model(model_name, timeout=request_timeout_seconds)
    agent_options: dict[str, Any] = {
        "model": chat_model,
        "system_prompt": system_prompt,
        "backend": FilesystemBackend(root_dir=str(EXAMPLE_DIR), virtual_mode=True),
        "skills": ["./skills/"],
        # ToolStrategy returns validation feedback to the model for correction.
        "response_format": ToolStrategy(schema, handle_errors=True),
        # Only the Python runner writes reports; agents read the skills they need.
        "permissions": atam_filesystem_permissions(),
    }
    if name is not None:
        agent_options["name"] = name
    if subagents is not None:
        agent_options["subagents"] = subagents
    return create_deep_agent(**agent_options)


def build_agent(model_name: str, request_timeout_seconds: float = 180) -> Any:
    """Create the ATAM coordinator with its external specialists and report schema."""
    subagents = [definition.model_dump(mode="python") for definition in load_subagents()]
    return build_deep_agent(
        model_name,
        request_timeout_seconds,
        system_prompt=load_prompt("system.md"),
        schema=AtamReportPayload,
        subagents=subagents,
    )
