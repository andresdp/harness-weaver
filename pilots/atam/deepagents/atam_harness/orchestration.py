"""ATAM-specific DeepAgents operations for the shared runtime strategies."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from harnessweaver.adapters.deepagents import execute_agent
from harnessweaver.runtime import ArtifactEnvelope, RunRequest, WorkflowOperations, WorkflowStrategy

from .agents import build_agent, build_deep_agent
from .models import (
    AtamArchitectureApproachesArtifact,
    AtamContextArtifact,
    AtamPlanningArtifact,
    AtamReportPayload,
    AtamScenarioAnalysisArtifact,
    AtamUtilityTreeArtifact,
)
from .paths import EXAMPLE_DIR
from .progress import log_progress, progress_context
from .prompts import build_task_prompt, load_prompt


ORCHESTRATION_PROMPTS = EXAMPLE_DIR / "prompts" / "orchestration.yaml"


class AtamDeepAgentsOperations(WorkflowOperations):
    """Materialize ATAM roles and typed handoffs using the chosen coordination profile."""

    def __init__(self, request: RunRequest) -> None:
        self.request = request
        self._orchestration_prompts = yaml.safe_load(ORCHESTRATION_PROMPTS.read_text(encoding="utf-8"))
        # Supervisor mode builds its task prompt in one read; staged modes load
        # and cache the shared evaluation instructions when composing a stage.
        self._evaluation_prompt: str | None = None
        self._system_prompt = load_prompt(
            "system.md"
            if request.profile.workflow_strategy is WorkflowStrategy.SUPERVISOR
            else "system_explicit_stages.md"
        )

    @property
    def pipeline_stages(self) -> Sequence[str]:
        return (
            "establish-context",
            "build-utility-tree",
            "identify-approaches",
            "analyze-scenarios",
            "synthesize-and-review",
        )

    @property
    def specialists(self) -> Sequence[str]:
        return ("context", "utility", "scenario")

    def run_supervisor(self, inputs: Mapping[str, Any]) -> AtamReportPayload:
        """Use the existing coordinator and specialist definitions for supervisor mode."""
        timeout = self.request.settings.get("request_timeout_seconds", 180)
        state = self._execute(
            build_agent(self.request.model, timeout),
            build_task_prompt(dict(inputs)),
            "ATAM coordinator",
        )
        return AtamReportPayload.model_validate(self._structured_response(state, "ATAM coordinator"))

    def run_stage(self, stage: str, inputs: Mapping[str, Any], handoffs: tuple[ArtifactEnvelope, ...]) -> Any:
        """Run one declared pipeline stage and pass prior Pydantic artifacts as JSON."""
        prompts = self._orchestration_prompts["sequential_pipeline"]["stages"]
        if stage == "establish-context":
            schema, context = AtamContextArtifact, {}
        elif stage == "build-utility-tree":
            schema = AtamUtilityTreeArtifact
            context = {"evaluation_context": self._artifact_value(handoffs, "establish-context")}
        elif stage == "identify-approaches":
            schema = AtamArchitectureApproachesArtifact
            context = {
                "evaluation_context": self._artifact_value(handoffs, "establish-context"),
                "utility_tree": self._artifact_value(handoffs, "build-utility-tree"),
            }
        elif stage == "analyze-scenarios":
            schema = AtamScenarioAnalysisArtifact
            context = {
                "evaluation_context": self._artifact_value(handoffs, "establish-context"),
                "utility_tree": self._artifact_value(handoffs, "build-utility-tree"),
                "architecture_approaches": self._artifact_value(handoffs, "identify-approaches"),
            }
        elif stage == "synthesize-and-review":
            schema = AtamReportPayload
            context = {
                "evaluation_context": self._artifact_value(handoffs, "establish-context"),
                "utility_tree": self._artifact_value(handoffs, "build-utility-tree"),
                "architecture_approaches": self._artifact_value(handoffs, "identify-approaches"),
                "scenario_analysis": self._artifact_value(handoffs, "analyze-scenarios"),
            }
        else:
            raise ValueError(f"unknown ATAM pipeline stage: {stage}")
        prompt = self._stage_prompt(prompts[stage], inputs, context)
        agent = self._build_structured_agent(f"atam-{stage}", schema)
        state = self._execute(agent, prompt, f"ATAM {stage}")
        return schema.model_validate(self._structured_response(state, stage))

    def run_specialist(self, specialist: str, inputs: Mapping[str, Any]) -> Any:
        """Run one isolated fan-out specialist with a typed result contract."""
        prompt = self._orchestration_prompts["fan_out_fan_in"]["specialists"].get(specialist)
        schemas = {
            "context": AtamContextArtifact,
            "utility": AtamPlanningArtifact,
            "scenario": AtamScenarioAnalysisArtifact,
        }
        if prompt is None or specialist not in schemas:
            raise ValueError(f"unknown ATAM fan-out specialist: {specialist}")
        agent = self._build_structured_agent(f"atam-{specialist}", schemas[specialist])
        state = self._execute(agent, self._stage_prompt(prompt, inputs, {}), f"ATAM {specialist}")
        return schemas[specialist].model_validate(self._structured_response(state, specialist))

    def join(self, inputs: Mapping[str, Any], results: tuple[ArtifactEnvelope, ...]) -> AtamReportPayload:
        """Have an evidence reviewer join all branch artifacts to the shared report model."""
        context = {item.producer: item.to_json_value() for item in results}
        prompt = self._stage_prompt(self._orchestration_prompts["fan_out_fan_in"]["join"], inputs, context)
        agent = self._build_structured_agent("atam-fan-in-review", AtamReportPayload)
        state = self._execute(agent, prompt, "ATAM fan-in reviewer")
        return AtamReportPayload.model_validate(self._structured_response(state, "fan-in reviewer"))

    def _build_structured_agent(self, name: str, schema: type[Any]) -> Any:
        """Build a role-scoped DeepAgent with the same skills and read-only workspace."""
        return build_deep_agent(
            self.request.model,
            self.request.settings.get("request_timeout_seconds", 180),
            name=name,
            system_prompt=self._system_prompt,
            schema=schema,
        )

    def _execute(self, agent: Any, prompt: str, label: str) -> Mapping[str, Any]:
        """Execute using one UI path for streamed and quiet runs."""
        console, context = progress_context(self.request.verbose)
        state = {"active_agent": label}
        with context as status:
            return execute_agent(
                agent,
                prompt,
                run_id=uuid4(),
                streaming=self.request.streaming,
                verbose=self.request.verbose,
                label=label,
                event_callback=lambda event, _name: log_progress(console, status, event, state),
            )

    @staticmethod
    def _structured_response(state: Mapping[str, Any], name: str) -> Any:
        response = state.get("structured_response")
        if response is None:
            raise ValueError(f"{name} DeepAgents call returned no structured response")
        return response

    @staticmethod
    def _artifact_value(handoffs: tuple[ArtifactEnvelope, ...], producer: str) -> Any:
        for artifact in handoffs:
            if artifact.producer == producer:
                return artifact.to_json_value()
        raise ValueError(f"required typed artifact handoff {producer!r} is missing")

    def _stage_prompt(self, instructions: str, inputs: Mapping[str, Any], handoffs: Mapping[str, Any]) -> str:
        """Keep the source case input and typed prior artifacts explicit in every call."""
        if self._evaluation_prompt is None:
            self._evaluation_prompt = load_prompt("evaluate_architecture.md")
        payload = {"evaluation_inputs": dict(inputs), "typed_handoffs": dict(handoffs)}
        return f"{self._evaluation_prompt}\n\nStage instructions:\n{instructions}\n\nStructured inputs:\n{json.dumps(payload, indent=2, ensure_ascii=False)}"
