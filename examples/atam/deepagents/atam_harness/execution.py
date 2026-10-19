"""Invoke a DeepAgent either with event streaming or as one blocking operation."""

from typing import Any
from uuid import UUID

from harnessweaver.adapters.deepagents import execute_agent as execute_deep_agent

from .progress import log_progress, progress_context
from .prompts import build_task_prompt


def stream_agent(agent: Any, inputs: dict[str, Any], *, run_id: UUID, verbose: bool) -> dict[str, Any]:
    """Stream graph events for live progress and return the final state."""
    console, status_context = progress_context(verbose)
    progress_state = {"active_agent": "ATAM coordinator"}
    with status_context as status:
        return execute_deep_agent(
            agent,
            build_task_prompt(inputs),
            run_id=run_id,
            streaming=True,
            verbose=verbose,
            label="ATAM coordinator",
            event_callback=lambda event, _name: log_progress(console, status, event, progress_state),
        )


def invoke_agent(agent: Any, inputs: dict[str, Any], *, run_id: UUID) -> dict[str, Any]:
    """Run synchronously without exposing intermediate graph events."""
    return execute_deep_agent(agent, build_task_prompt(inputs), run_id=run_id)


def execute_agent(
    agent: Any,
    inputs: dict[str, Any],
    *,
    run_id: UUID,
    streaming: bool,
    verbose: bool,
) -> dict[str, Any]:
    """Select an execution mode while preserving a single final-state contract."""
    if streaming:
        return stream_agent(agent, inputs, run_id=run_id, verbose=verbose)
    return invoke_agent(agent, inputs, run_id=run_id)
