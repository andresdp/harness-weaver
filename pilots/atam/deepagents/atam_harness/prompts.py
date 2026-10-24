"""Load editable prompt assets and combine them with case inputs."""

import json
from typing import Any

from .paths import EXAMPLE_DIR


PROMPTS_DIR = EXAMPLE_DIR / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt file relative to this backend, independent of the working directory."""
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def build_task_prompt(evaluation_inputs: dict[str, Any]) -> str:
    """Serialize the allowed case inputs into the model's task prompt."""
    instructions = load_prompt("evaluate_architecture.md")
    return f"{instructions}\n\nEvaluation inputs:\n{json.dumps(evaluation_inputs, indent=2)}"
