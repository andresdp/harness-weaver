import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from unittest.mock import patch

from harnessweaver.runtime import AgentInteraction, ExecutionProfile, RunRequest, WorkflowStrategy
from examples.atam.deepagents.atam_harness.models import (
    AtamContextArtifact,
    AtamEvaluationResults,
    AtamPlanningArtifact,
    AtamReportPayload,
    AtamScenarioAnalysisArtifact,
)
from examples.atam.deepagents.atam_harness.orchestration import AtamDeepAgentsOperations


def metadata() -> dict[str, object]:
    return {
        "system_name": "Banking system",
        "date": None,
        "ref": None,
        "evaluator_organization": None,
        "phase_1_attendees": [],
        "phase_2_attendees": [],
    }


def empty_evaluation_results() -> dict[str, object]:
    return {
        "utility_tree": {"root": "Utility", "quality_attribute_nodes": []},
        "architectural_approaches": [],
        "analysis_records": [],
        "scenarios": [],
    }


class FakeAgent:
    def __init__(self, response):
        self.response = response
        self.prompt = None

    def invoke(self, payload, config):
        self.prompt = payload["messages"][0]["content"]
        return {"structured_response": self.response}


class AtamOrchestrationTests(unittest.TestCase):
    def make_operations(self, workflow: WorkflowStrategy) -> AtamDeepAgentsOperations:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        return AtamDeepAgentsOperations(
            RunRequest(
                run_id=uuid4(),
                case_id="banking",
                inputs={"system_description": "A banking platform"},
                profile=ExecutionProfile(
                    workflow,
                    {
                        WorkflowStrategy.SEQUENTIAL_PIPELINE: AgentInteraction.TYPED_ARTIFACT_HANDOFFS,
                        WorkflowStrategy.FAN_OUT_FAN_IN: AgentInteraction.PARALLEL_SPECIALIST_DELEGATION,
                    }[workflow],
                ),
                model="provider:model",
                spec_path=Path(temporary_directory.name) / "spec.yaml",
                output_path=Path(temporary_directory.name) / "report.json",
            )
        )

    def test_sequential_stages_return_typed_artifacts_and_receive_handoffs(self):
        operations = self.make_operations(WorkflowStrategy.SEQUENTIAL_PIPELINE)
        responses = {
            AtamContextArtifact: AtamContextArtifact.model_validate(
                {"metadata": metadata(), "scope_summary": "Banking platform", "evidence_gaps": []}
            ),
            AtamEvaluationResults: AtamEvaluationResults.model_validate(empty_evaluation_results()),
            AtamReportPayload: AtamReportPayload.model_validate(
                {"metadata": metadata(), "evaluation_results": empty_evaluation_results()}
            ),
        }
        agents = []

        def build_agent(_name, schema):
            agent = FakeAgent(responses[schema])
            agents.append(agent)
            return agent

        with patch.object(operations, "_build_structured_agent", side_effect=build_agent):
            context = operations.run_stage("context", operations.request.inputs, ())
            from harnessweaver.runtime import ArtifactEnvelope

            context_handoff = ArtifactEnvelope("context", context)
            analysis = operations.run_stage("analysis", operations.request.inputs, (context_handoff,))
            analysis_handoff = ArtifactEnvelope("analysis", analysis)
            report = operations.run_stage(
                "review", operations.request.inputs, (context_handoff, analysis_handoff)
            )

        self.assertIsInstance(context, AtamContextArtifact)
        self.assertIsInstance(analysis, AtamEvaluationResults)
        self.assertIsInstance(report, AtamReportPayload)
        self.assertIn('"context_artifact"', agents[1].prompt)
        self.assertIn('"analysis_artifact"', agents[2].prompt)

    def test_fan_out_specialists_and_join_use_typed_contracts(self):
        operations = self.make_operations(WorkflowStrategy.FAN_OUT_FAN_IN)
        responses = {
            AtamContextArtifact: AtamContextArtifact.model_validate(
                {"metadata": metadata(), "scope_summary": "Banking platform", "evidence_gaps": []}
            ),
            AtamPlanningArtifact: AtamPlanningArtifact.model_validate(
                {
                    "utility_tree": {"root": "Utility", "quality_attribute_nodes": []},
                    "architectural_approaches": [],
                    "scenarios": [],
                }
            ),
            AtamScenarioAnalysisArtifact: AtamScenarioAnalysisArtifact.model_validate(
                {"analysis_records": []}
            ),
            AtamReportPayload: AtamReportPayload.model_validate(
                {"metadata": metadata(), "evaluation_results": empty_evaluation_results()}
            ),
        }
        agents = []

        def build_agent(_name, schema):
            agent = FakeAgent(responses[schema])
            agents.append(agent)
            return agent

        with patch.object(operations, "_build_structured_agent", side_effect=build_agent):
            artifacts = {
                role: operations.run_specialist(role, operations.request.inputs)
                for role in operations.specialists
            }
            from harnessweaver.runtime import ArtifactEnvelope

            report = operations.join(
                operations.request.inputs,
                tuple(ArtifactEnvelope(role, artifacts[role]) for role in operations.specialists),
            )

        self.assertIsInstance(artifacts["utility"], AtamPlanningArtifact)
        self.assertIsInstance(artifacts["scenario"], AtamScenarioAnalysisArtifact)
        self.assertIsInstance(report, AtamReportPayload)
        self.assertIn('"context"', agents[-1].prompt)
        self.assertIn('"utility"', agents[-1].prompt)
        self.assertIn('"scenario"', agents[-1].prompt)


if __name__ == "__main__":
    unittest.main()
