"""Thin DeepAgents construction/execution adapter over runtime-neutral contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from time import monotonic
from typing import Annotated, Any, TypedDict
from uuid import UUID

from harnessweaver.runtime import (
    ArtifactEnvelope,
    RunRequest,
    RunResult,
    WorkflowOperations,
    WorkflowStrategy,
    execute_workflow,
)


def _merge_results(left: dict[str, ArtifactEnvelope], right: dict[str, ArtifactEnvelope]) -> dict[str, ArtifactEnvelope]:
    """Merge specialist outputs from the same parallel LangGraph super-step."""
    return {**left, **right}


class _FanOutState(TypedDict):
    """Shared graph state with a reducer for independent specialist results."""

    inputs: Mapping[str, Any]
    results: Annotated[dict[str, ArtifactEnvelope], _merge_results]
    joined: Any


def execute_fan_out_fan_in(operations: WorkflowOperations, inputs: Mapping[str, Any]) -> Any:
    """Run DeepAgents specialists as parallel LangGraph nodes behind a join barrier."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError("LangGraph is required for fan_out_fan_in; install the 'deepagents' extra") from exc

    specialists = tuple(operations.specialists)
    if not specialists:
        raise ValueError("fan_out_fan_in requires at least one declared specialist")
    if "join" in specialists:
        raise ValueError("'join' is reserved for the fan_out_fan_in synthesis node")

    graph = StateGraph(_FanOutState)
    for specialist in specialists:
        def run_specialist(state: _FanOutState, *, role: str = specialist) -> dict[str, Any]:
            # Validate each branch result before it can enter the graph's shared state.
            artifact = operations.run_specialist(role, state["inputs"])
            envelope = ArtifactEnvelope(role, artifact)
            envelope.to_json_value()
            return {"results": {role: envelope}}

        graph.add_node(specialist, run_specialist)

    def join_specialists(state: _FanOutState) -> dict[str, Any]:
        # Multi-source edges ensure this node starts only after every branch finishes.
        ordered = tuple(state["results"][role] for role in specialists)
        joined = operations.join(state["inputs"], ordered)
        ArtifactEnvelope("fan_out_fan_in_join", joined).to_json_value()
        return {"joined": joined}

    graph.add_node("join", join_specialists)
    for specialist in specialists:
        graph.add_edge(START, specialist)
    graph.add_edge(list(specialists), "join")
    graph.add_edge("join", END)
    result = graph.compile().invoke({"inputs": inputs, "results": {}})
    return result["joined"]


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
        if request.profile.workflow_strategy is WorkflowStrategy.FAN_OUT_FAN_IN:
            artifact = execute_fan_out_fan_in(operations, request.inputs)
        else:
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
