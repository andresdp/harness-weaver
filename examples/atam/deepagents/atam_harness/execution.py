"""Invoke a DeepAgent either with event streaming or as one blocking operation."""

from typing import Any
from uuid import UUID

from .progress import log_progress, progress_context
from .prompts import build_task_prompt


def stream_agent(agent: Any, inputs: dict[str, Any], *, run_id: UUID, verbose: bool) -> dict[str, Any]:
    """Stream graph events for live progress and return the final state."""
    console, status_context = progress_context(verbose)
    final_state: dict[str, Any] | None = None
    progress_state = {"active_agent": "ATAM coordinator"}
    with status_context as status:
        for event in agent.stream(
            {"messages": [{"role": "user", "content": build_task_prompt(inputs)}]},
            config={"run_id": run_id},
            stream_mode=["updates", "values"],
            subgraphs=True,
            version="v2",
        ):
            if event.get("type") == "values":
                data = event.get("data")
                if isinstance(data, dict):
                    final_state = data
            elif verbose:
                log_progress(console, status, event, progress_state)
    if final_state is None:
        raise ValueError("DeepAgents stream ended without a final state")
    return final_state


def invoke_agent(agent: Any, inputs: dict[str, Any], *, run_id: UUID) -> dict[str, Any]:
    """Run synchronously without exposing intermediate graph events."""
    return agent.invoke(
        {"messages": [{"role": "user", "content": build_task_prompt(inputs)}]},
        config={"run_id": run_id},
    )


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
