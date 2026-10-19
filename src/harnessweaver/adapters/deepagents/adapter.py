"""Thin DeepAgents construction/execution adapter over runtime-neutral contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from time import monotonic
from typing import Any
from uuid import UUID

from harnessweaver.runtime import RunRequest, RunResult, WorkflowOperations, execute_workflow


def create_deep_agent(**kwargs: Any) -> Any:
    """Create a DeepAgent only when this optional backend is explicitly used."""
    try:
        from deepagents import create_deep_agent as factory
    except ImportError as exc:
        raise RuntimeError("DeepAgents is required for this adapter; install the 'deepagents' extra") from exc
    return factory(**kwargs)


def execute_agent(
    agent: Any,
    prompt: str,
    *,
    run_id: UUID,
    streaming: bool = False,
    verbose: bool = False,
    label: str = "DeepAgent",
    event_callback: Callable[[Mapping[str, Any], str], None] | None = None,
) -> Mapping[str, Any]:
    """Invoke or stream one DeepAgent and return its final state consistently."""
    config = {"configurable": {"thread_id": str(run_id)}}
    if not streaming:
        return agent.invoke({"messages": [{"role": "user", "content": prompt}]}, config=config)

    final_state: Mapping[str, Any] | None = None
    events = agent.stream(
        {"messages": [{"role": "user", "content": prompt}]},
        config=config,
        stream_mode=["updates", "values"],
        subgraphs=True,
        version="v2",
    )
    for event in events:
        if event.get("type") == "values" and isinstance(event.get("data"), Mapping):
            final_state = event["data"]
        elif verbose and event_callback is not None:
            event_callback(event, label)
    if final_state is None:
        raise ValueError(f"{label} stream ended without a final state")
    return final_state


class DeepAgentsRuntimeAdapter:
    """Map runtime-neutral requests to an injected domain workflow over DeepAgents."""

    runtime_name = "deepagents"

    def __init__(self, operations_factory: Callable[[RunRequest], WorkflowOperations]):
        self._operations_factory = operations_factory

    def run(self, request: RunRequest) -> RunResult:
        """Execute a selected strategy and return the typed domain artifact plus fidelity."""
        started = monotonic()
        operations = self._operations_factory(request)
        artifact = execute_workflow(request.profile, operations, request.inputs)
        return RunResult(
            run_id=request.run_id,
            status="succeeded",
            output_path=request.output_path,
            elapsed_seconds=monotonic() - started,
            capabilities=("deepagents", request.profile.workflow_strategy.value, request.profile.agent_interaction.value),
            approximations=("Specialists are one-shot; persistent peer-to-peer state is not provided.",),
            unsupported=("Persistent Claude-style agent messaging and shared task-list collaboration.",),
            artifact=artifact,
        )
