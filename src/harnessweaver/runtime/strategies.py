"""Bounded runtime-neutral algorithms for supported coordination profiles."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from .contracts import ExecutionProfile, WorkflowStrategy


@dataclass(frozen=True)
class ArtifactEnvelope:
    """Typed intermediate result passed between declared workflow stages."""

    producer: str
    artifact: Any
    _json_value: Any = field(default=None, init=False, repr=False, compare=False)
    _validated: bool = field(default=False, init=False, repr=False, compare=False)

    def to_json_value(self) -> Any:
        """Ensure a stage result can be handed off as structured data."""
        if not self._validated:
            dump = getattr(self.artifact, "model_dump", None)
            if not callable(dump):
                raise TypeError(f"artifact from {self.producer!r} must be a Pydantic model")
            value = dump(mode="json")
            json.dumps(value)
            object.__setattr__(self, "_json_value", value)
            object.__setattr__(self, "_validated", True)
        return self._json_value


class WorkflowOperations(Protocol):
    """Domain-specific agent calls used by the shared strategy algorithms."""

    @property
    def pipeline_stages(self) -> Sequence[str]: ...

    @property
    def specialists(self) -> Sequence[str]: ...

    def run_supervisor(self, inputs: Mapping[str, Any]) -> Any: ...

    def run_stage(self, stage: str, inputs: Mapping[str, Any], handoffs: tuple[ArtifactEnvelope, ...]) -> Any: ...

    def run_specialist(self, specialist: str, inputs: Mapping[str, Any]) -> Any: ...

    def join(self, inputs: Mapping[str, Any], results: tuple[ArtifactEnvelope, ...]) -> Any: ...


def execute_workflow(profile: ExecutionProfile, operations: WorkflowOperations, inputs: Mapping[str, Any]) -> Any:
    """Execute a supported workflow, requiring typed complete handoffs before returning."""
    if profile.workflow_strategy is WorkflowStrategy.SUPERVISOR:
        return operations.run_supervisor(inputs)

    if profile.workflow_strategy is WorkflowStrategy.SEQUENTIAL_PIPELINE:
        if not operations.pipeline_stages:
            raise ValueError("sequential_pipeline requires at least one declared stage")
        handoffs: list[ArtifactEnvelope] = []
        for stage in operations.pipeline_stages:
            result = operations.run_stage(stage, inputs, tuple(handoffs))
            envelope = ArtifactEnvelope(stage, result)
            envelope.to_json_value()
            handoffs.append(envelope)
        return handoffs[-1].artifact

    if profile.workflow_strategy is WorkflowStrategy.FAN_OUT_FAN_IN:
        specialists = tuple(operations.specialists)
        if not specialists:
            raise ValueError("fan_out_fan_in requires at least one declared specialist")
        results: dict[str, ArtifactEnvelope] = {}
        with ThreadPoolExecutor(max_workers=len(specialists), thread_name_prefix="hw-specialist") as pool:
            futures = {pool.submit(operations.run_specialist, specialist, inputs): specialist for specialist in specialists}
            try:
                for future in as_completed(futures):
                    specialist = futures[future]
                    envelope = ArtifactEnvelope(specialist, future.result())
                    envelope.to_json_value()
                    results[specialist] = envelope
            except Exception:
                for future in futures:
                    future.cancel()
                raise
        # Restore declaration order so joins do not depend on completion timing.
        ordered = tuple(results[name] for name in specialists)
        joined = operations.join(inputs, ordered)
        envelope = ArtifactEnvelope("fan_out_fan_in_join", joined)
        envelope.to_json_value()
        return joined

    raise ValueError(f"unsupported workflow strategy: {profile.workflow_strategy}")
