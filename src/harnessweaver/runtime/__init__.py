"""Runtime-neutral contracts shared by optional harness adapters."""

from .contracts import (
    AgentInteraction,
    ExecutionProfile,
    RunRequest,
    RunResult,
    RuntimeAdapter,
    WorkflowStrategy,
    profile_from_spec,
)
from .strategies import ArtifactEnvelope, WorkflowOperations, execute_workflow

__all__ = [
    "AgentInteraction",
    "ArtifactEnvelope",
    "ExecutionProfile",
    "RunRequest",
    "RunResult",
    "RuntimeAdapter",
    "WorkflowStrategy",
    "WorkflowOperations",
    "execute_workflow",
    "profile_from_spec",
]
