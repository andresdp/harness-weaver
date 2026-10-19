import tempfile
import threading
import unittest
from pathlib import Path
from uuid import uuid4

from harnessweaver.adapters.deepagents import DeepAgentsRuntimeAdapter, execute_agent
from harnessweaver.runtime import AgentInteraction, ExecutionProfile, RunRequest, WorkflowStrategy


class ReportArtifact:
    def model_dump(self, mode="python"):
        return {"report": "typed"}


class Operations:
    pipeline_stages = ()
    specialists = ()

    def run_supervisor(self, inputs):
        return ReportArtifact()

    def run_stage(self, stage, inputs, handoffs):
        raise AssertionError("not used")

    def run_specialist(self, specialist, inputs):
        raise AssertionError("not used")

    def join(self, inputs, results):
        raise AssertionError("not used")


class ParallelOperations(Operations):
    specialists = ("context", "analysis", "evidence")

    def __init__(self):
        self.barrier = threading.Barrier(len(self.specialists))

    def run_specialist(self, specialist, inputs):
        self.barrier.wait(timeout=2)
        return ReportArtifact()

    def join(self, inputs, results):
        return ReportArtifact()


class FakeAgent:
    def invoke(self, payload, config):
        self.invoke_call = (payload, config)
        return {"structured_response": ReportArtifact()}

    def stream(self, payload, config, **kwargs):
        self.stream_call = (payload, config, kwargs)
        yield {"type": "updates", "data": {"agent": {}}}
        yield {"type": "values", "data": {"structured_response": ReportArtifact()}}


class DeepAgentsRuntimeTests(unittest.TestCase):
    def test_adapter_returns_typed_artifact_and_fidelity_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = RunRequest(
                run_id=uuid4(), case_id="case", inputs={"description": "input only"},
                profile=ExecutionProfile(WorkflowStrategy.SUPERVISOR, AgentInteraction.ONE_SHOT_SPECIALIST_DELEGATION),
                model="provider:model", spec_path=Path(tmp) / "spec.yaml", output_path=Path(tmp) / "report.json",
            )
            result = DeepAgentsRuntimeAdapter(lambda _request: Operations()).run(request)
        self.assertEqual(result.status, "succeeded")
        self.assertEqual(result.artifact.model_dump(), {"report": "typed"})
        self.assertIn("deepagents", result.capabilities)
        self.assertTrue(result.unsupported)

    def test_streaming_and_invoke_keep_one_final_state_shape(self):
        agent = FakeAgent()
        for streaming in (False, True):
            calls = []
            result = execute_agent(agent, "prompt", run_id=uuid4(), streaming=streaming, verbose=True,
                                   event_callback=lambda event, label: calls.append((event["type"], label)))
            self.assertIsInstance(result["structured_response"], ReportArtifact)
            self.assertEqual(len(calls), 1 if streaming else 0)

    def test_deepagents_fan_out_uses_parallel_langgraph_nodes_before_join(self):
        operations = ParallelOperations()
        with tempfile.TemporaryDirectory() as tmp:
            request = RunRequest(
                run_id=uuid4(),
                case_id="case",
                inputs={"source": "input only"},
                profile=ExecutionProfile(
                    WorkflowStrategy.FAN_OUT_FAN_IN,
                    AgentInteraction.PARALLEL_SPECIALIST_DELEGATION,
                ),
                model="provider:model",
                spec_path=Path(tmp) / "spec.yaml",
                output_path=Path(tmp) / "report.json",
            )
            result = DeepAgentsRuntimeAdapter(lambda _request: operations).run(request)

        self.assertEqual(result.artifact.model_dump(), {"report": "typed"})
        self.assertIn("fan_out_fan_in", result.capabilities)

    def test_atam_harness_spec_declares_supervisor_default(self):
        from harnessweaver.spec import load_spec
        spec = load_spec(Path(__file__).resolve().parents[1] / "examples/atam/harnessspec-v0.2.yaml")
        self.assertEqual(spec["orchestration"]["workflow_strategy"], "supervisor")


if __name__ == "__main__":
    unittest.main()
