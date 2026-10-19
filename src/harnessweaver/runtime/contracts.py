"""Backend-independent execution request, result, and capability contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable
from uuid import UUID


class WorkflowStrategy(str, Enum):
    """Control-flow shape requested by a HarnessSpec."""

    SUPERVISOR = "supervisor"
    SEQUENTIAL_PIPELINE = "sequential_pipeline"
    FAN_OUT_FAN_IN = "fan_out_fan_in"


class AgentInteraction(str, Enum):
    """How specialist outputs are shared with the coordinator or one another."""

    ONE_SHOT_SPECIALIST_DELEGATION = "one_shot_specialist_delegation"
    TYPED_ARTIFACT_HANDOFFS = "typed_artifact_handoffs"
    PARALLEL_SPECIALIST_DELEGATION = "parallel_specialist_delegation"


SUPPORTED_PROFILES = frozenset(
    {
        (WorkflowStrategy.SUPERVISOR, AgentInteraction.ONE_SHOT_SPECIALIST_DELEGATION),
        (WorkflowStrategy.SEQUENTIAL_PIPELINE, AgentInteraction.TYPED_ARTIFACT_HANDOFFS),
        (WorkflowStrategy.FAN_OUT_FAN_IN, AgentInteraction.PARALLEL_SPECIALIST_DELEGATION),
    }
)


@dataclass(frozen=True)
class ExecutionProfile:
    """Selected workflow and interaction dimensions kept independently addressable."""

    workflow_strategy: WorkflowStrategy
    agent_interaction: AgentInteraction

    @classmethod
    def from_values(cls, strategy: str, interaction: str) -> "ExecutionProfile":
        """Parse and validate the two serialized profile fields."""
        try:
            return cls(WorkflowStrategy(strategy), AgentInteraction(interaction))
        except ValueError as exc:
            raise ValueError(f"unknown or unsupported execution profile {strategy!r}+{interaction!r}") from exc

    def __post_init__(self) -> None:
        if (self.workflow_strategy, self.agent_interaction) not in SUPPORTED_PROFILES:
            supported = ", ".join(
                f"{strategy.value}+{interaction.value}"
                for strategy, interaction in sorted(SUPPORTED_PROFILES, key=lambda pair: (pair[0].value, pair[1].value))
            )
            raise ValueError(
                f"unsupported workflow_strategy/agent_interaction combination "
                f"{self.workflow_strategy.value}+{self.agent_interaction.value}; supported combinations: {supported}"
            )


@dataclass(frozen=True)
class RunRequest:
    """Inputs to a runtime adapter; the payload contains generation inputs only."""

    run_id: UUID
    case_id: str
    inputs: Mapping[str, Any]
    profile: ExecutionProfile
    model: str
    spec_path: Path
    output_path: Path
    streaming: bool = False
    verbose: bool = False
    settings: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunResult:
    """Runtime output and fidelity facts needed to explain one execution."""

    run_id: UUID
    status: str
    output_path: Path | None
    elapsed_seconds: float | None
    capabilities: tuple[str, ...]
    approximations: tuple[str, ...] = ()
    unsupported: tuple[str, ...] = ()
    artifact: Any = None


@runtime_checkable
class RuntimeAdapter(Protocol):
    """Optional backend boundary used by examples and benchmark runners."""

    def run(self, request: RunRequest) -> RunResult: ...


def profile_from_spec(document: Mapping[str, Any], *, strategy: str | None = None, interaction: str | None = None) -> ExecutionProfile:
    """Resolve CLI overrides over the spec defaults and validate the supported pairing."""
    declared = document.get("orchestration", {})
    if not isinstance(declared, Mapping):
        raise ValueError("HarnessSpec orchestration must be a mapping")
    try:
        workflow = WorkflowStrategy(strategy or declared.get("workflow_strategy", WorkflowStrategy.SUPERVISOR.value))
        agent_style = AgentInteraction(interaction or declared.get("agent_interaction", AgentInteraction.ONE_SHOT_SPECIALIST_DELEGATION.value))
    except ValueError as exc:
        raise ValueError(f"unknown orchestration option: {exc}") from exc
    return ExecutionProfile(workflow, agent_style)
