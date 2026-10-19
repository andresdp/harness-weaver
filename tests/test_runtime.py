import threading
import unittest

from harnessweaver.runtime import (
    AgentInteraction,
    ExecutionProfile,
    WorkflowStrategy,
    execute_workflow,
)


class TypedArtifact:
    def __init__(self, stage, value):
        self.stage = stage
        self.value = value

    def model_dump(self, mode="python"):
        return {"stage": self.stage, "value": self.value}


class FakeOperations:
    pipeline_stages = ("context", "analysis", "review")
    specialists = ("utility", "scenario", "evidence")

    def __init__(self):
        self.handoffs = []
        self.completed = []
        self.lock = threading.Lock()
        self.specialist_barrier = threading.Barrier(len(self.specialists))

    def run_supervisor(self, inputs):
        return TypedArtifact("report", inputs["case"])

    def run_stage(self, stage, inputs, handoffs):
        self.handoffs.append((stage, tuple(item.producer for item in handoffs)))
        return TypedArtifact(stage, inputs["case"])

    def run_specialist(self, specialist, inputs):
        with self.lock:
            self.completed.append(specialist)
        # Every branch must be active together for the fan-out profile to pass.
        self.specialist_barrier.wait(timeout=2)
        return TypedArtifact(specialist, inputs["case"])

    def join(self, inputs, results):
        return TypedArtifact("joined", [item.producer for item in results])


class RuntimeStrategyTests(unittest.TestCase):
    def test_sequential_pipeline_passes_prior_typed_artifacts_in_order(self):
        operations = FakeOperations()
        profile = ExecutionProfile(WorkflowStrategy.SEQUENTIAL_PIPELINE, AgentInteraction.TYPED_ARTIFACT_HANDOFFS)

        result = execute_workflow(profile, operations, {"case": "banking"})

        self.assertEqual(result.stage, "review")
        self.assertEqual(operations.handoffs, [("context", ()), ("analysis", ("context",)), ("review", ("context", "analysis"))])

    def test_fanout_requires_complete_join_in_declaration_order(self):
        operations = FakeOperations()
        profile = ExecutionProfile(WorkflowStrategy.FAN_OUT_FAN_IN, AgentInteraction.PARALLEL_SPECIALIST_DELEGATION)

        result = execute_workflow(profile, operations, {"case": "banking"})

        self.assertCountEqual(operations.completed, operations.specialists)
        self.assertEqual(result.value, ["utility", "scenario", "evidence"])

    def test_supervisor_uses_one_shot_delegation_contract(self):
        profile = ExecutionProfile(WorkflowStrategy.SUPERVISOR, AgentInteraction.ONE_SHOT_SPECIALIST_DELEGATION)
        result = execute_workflow(profile, FakeOperations(), {"case": "banking"})
        self.assertEqual(result.value, "banking")

    def test_untyped_pipeline_result_fails_before_later_stage(self):
        operations = FakeOperations()
        operations.run_stage = lambda stage, inputs, handoffs: {"untyped": True}
        profile = ExecutionProfile(WorkflowStrategy.SEQUENTIAL_PIPELINE, AgentInteraction.TYPED_ARTIFACT_HANDOFFS)

        with self.assertRaisesRegex(TypeError, "must be a Pydantic model"):
            execute_workflow(profile, operations, {"case": "banking"})


if __name__ == "__main__":
    unittest.main()
