import json
import tempfile
import unittest
from pathlib import Path

import yaml

from harnessweaver.hosts.deepagents import run_stages
from harnessweaver.wiring import WiringError, load_wiring


SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["summary"],
    "properties": {"summary": {"type": "string"}},
}


def write_bundle(root: Path, *, wiring: dict | None = None) -> Path:
    """Create a two-stage DeepAgents bundle following the target pattern."""
    bundle = root / "bundle"
    for number, name, artifacts in ((1, "context", ["01_context.json"]), (2, "report", ["02_report.json"])):
        stage = bundle / f"stage{number}-{name}"
        (stage / "skills" / f"{name}-task").mkdir(parents=True)
        (stage / "AGENTS.md").write_text(
            f"# {name} Agent\n\nDo not perform later stages.\n\n## Mandatory Completion Protocol\n"
            + "".join(f"- /artifacts/{artifact}\n" for artifact in artifacts),
            encoding="utf-8",
        )
        (stage / "skills" / f"{name}-task" / "SKILL.md").write_text(
            f"---\nname: {name}-task\ndescription: Produce the {name} artifact.\n---\n\n# {name}\n", encoding="utf-8"
        )
    (bundle / "contracts").mkdir()
    (bundle / "contracts" / "report.schema.json").write_text(json.dumps(SCHEMA), encoding="utf-8")
    document = wiring or {
        "wiring_version": "0.1",
        "spec": {"path": "../harnessspec.yaml", "id": "demo", "version": "0.2"},
        "inputs": [{"port": "architecture-context", "path": "/artifacts/00_architecture-context.json"}],
        "stages": [
            {"number": 1, "dir": "stage1-context", "handoff_prompt": "Read the input and write the context.",
             "artifacts": ["01_context.json"]},
            {"number": 2, "dir": "stage2-report", "handoff_prompt": "Write the report from the context.",
             "artifacts": ["02_report.json"], "schemas": {"02_report.json": "contracts/report.schema.json"}},
        ],
        "output": {"artifact": "02_report.json", "schema": "contracts/report.schema.json"},
        "human_gates": [{"id": "expert-review", "after_stage": 2}],
    }
    (bundle / "wiring.yaml").write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return bundle


class FakeStageAgent:
    """Writes the given artifacts into the workspace, standing in for a model-driven stage."""

    def __init__(self, workspace: Path, writes: dict[str, str], log: list[str], name: str):
        self.workspace, self.writes, self.log, self.name = workspace, writes, log, name

    def invoke(self, payload):
        self.log.append(self.name)
        self.prompts = payload["messages"][0]["content"]
        for relative, content in self.writes.items():
            target = self.workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return {"messages": []}


def fake_factory(outputs: dict[str, dict[str, str]], log: list[str]):
    def factory(stage_dir: Path, workspace: Path):
        return FakeStageAgent(workspace, outputs.get(stage_dir.name, {}), log, stage_dir.name)
    return factory


GOOD_OUTPUTS = {
    "stage1-context": {"artifacts/01_context.json": json.dumps({"scope": "bank"})},
    "stage2-report": {"artifacts/02_report.json": json.dumps({"summary": "draft"})},
}


class WiringTests(unittest.TestCase):
    def test_loads_a_valid_wiring_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiring = load_wiring(write_bundle(Path(tmp)))
        self.assertEqual([stage.dir for stage in wiring.stages], ["stage1-context", "stage2-report"])
        self.assertEqual(wiring.inputs[0].port, "architecture-context")
        self.assertEqual(wiring.output_artifact, "02_report.json")
        self.assertEqual(wiring.human_gates[0].after_stage, 2)

    def test_rejects_inconsistent_wiring_with_every_problem_listed(self):
        bad = {
            "wiring_version": "9",
            "spec": {"id": "demo"},
            "inputs": [{"port": "x", "path": "relative.json"}],
            "stages": [
                {"number": 2, "dir": "stage2-report", "handoff_prompt": "", "artifacts": ["../escape.json"]},
                {"number": 2, "dir": "stage2-report", "handoff_prompt": "Again.", "artifacts": ["02_report.json"],
                 "schemas": {"03_other.json": "contracts/report.schema.json"}},
            ],
            "output": {"artifact": "99_missing.json"},
            "human_gates": [{"id": "g", "after_stage": 7}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(WiringError) as raised:
                load_wiring(write_bundle(Path(tmp), wiring=bad))
        text = str(raised.exception)
        for expected in ("wiring_version", "/artifacts/", "numbered 1..N", "handoff_prompt", "plain JSON filename",
                         "duplicate", "not an artifact of stage 2", "output.artifact", "after_stage"):
            self.assertIn(expected, text)


class StageHostTests(unittest.TestCase):
    def run_host(self, outputs, **kwargs):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        bundle = write_bundle(root)
        input_dir = root / "input"
        input_dir.mkdir()
        (input_dir / "architecture-context.json").write_text(json.dumps({"ATAM_Evaluation": {"evaluation_inputs": {}}}))
        log: list[str] = []
        result = run_stages(bundle, input_dir, root / "workspace", root / "output", fake_factory(outputs, log), **kwargs)
        return result, log, root

    def test_runs_stages_in_order_and_publishes_the_validated_output(self):
        result, log, root = self.run_host(GOOD_OUTPUTS)
        self.assertEqual(result.status, "awaiting_review")
        self.assertEqual(log, ["stage1-context", "stage2-report"])
        # Inputs are placed at their declared virtual paths before stage 1.
        self.assertTrue((root / "workspace/artifacts/00_architecture-context.json").is_file())
        self.assertEqual(json.loads(result.output_path.read_text()), {"summary": "draft"})
        record = json.loads((root / "output/host-record.json").read_text())
        self.assertEqual([stage["status"] for stage in record["stages"]], ["completed", "completed"])
        self.assertEqual(record["human_gates"], [{"id": "expert-review", "after_stage": 2, "status": "pending"}])

    def test_stops_at_the_first_stage_missing_a_declared_artifact(self):
        outputs = {"stage1-context": {}, **{k: v for k, v in GOOD_OUTPUTS.items() if k != "stage1-context"}}
        result, log, root = self.run_host(outputs)
        self.assertEqual(result.status, "failed")
        self.assertEqual(log, ["stage1-context"])
        self.assertIn("01_context.json is missing", result.stages[0].problems[0])
        self.assertIsNone(result.output_path)
        self.assertFalse((root / "output/02_report.json").exists())

    def test_rejects_invalid_json_and_schema_violations(self):
        for bad, expected in (("{not json", "not valid JSON"), (json.dumps({"other": 1}), "violates contracts/report.schema.json")):
            outputs = {**GOOD_OUTPUTS, "stage2-report": {"artifacts/02_report.json": bad}}
            result, _, _ = self.run_host(outputs)
            self.assertEqual(result.status, "failed")
            self.assertIn(expected, " ".join(result.stages[1].problems))

    def test_missing_input_port_fails_before_any_stage_runs(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "input").mkdir()
        log: list[str] = []
        result = run_stages(write_bundle(root), root / "input", root / "workspace", root / "output", fake_factory(GOOD_OUTPUTS, log))
        self.assertEqual(result.status, "failed")
        self.assertEqual(log, [])
        self.assertIn("architecture-context", result.problems[0])

    def test_gate_before_the_last_stage_stops_unless_explicitly_bypassed(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        bundle = write_bundle(root)
        wiring = yaml.safe_load((bundle / "wiring.yaml").read_text())
        wiring["human_gates"] = [{"id": "context-review", "after_stage": 1}]
        (bundle / "wiring.yaml").write_text(yaml.safe_dump(wiring))
        (root / "input").mkdir()
        (root / "input/architecture-context.json").write_text("{}")
        log: list[str] = []
        stopped = run_stages(bundle, root / "input", root / "ws1", root / "out1", fake_factory(GOOD_OUTPUTS, log))
        self.assertEqual((stopped.status, log), ("awaiting_review", ["stage1-context"]))
        bypassed = run_stages(bundle, root / "input", root / "ws2", root / "out2", fake_factory(GOOD_OUTPUTS, log),
                              continue_past_gates=True)
        self.assertEqual(bypassed.status, "completed")
        self.assertEqual(bypassed.human_gates[0]["status"], "bypassed (unattended run)")


class DeepAgentsIntegrationTests(unittest.TestCase):
    def test_real_stage_agent_writes_artifacts_through_the_composite_backend(self):
        try:
            from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
            from langchain_core.messages import AIMessage
            from harnessweaver.hosts.deepagents import build_stage_agent
        except ImportError as exc:  # pragma: no cover - optional backend
            self.skipTest(f"DeepAgents extra not installed: {exc}")

        class ScriptedModel(GenericFakeChatModel):
            def bind_tools(self, tools, **kwargs):
                return self

        def scripted(artifact: str, content: dict):
            # One write_file tool call per stage, then a final message.
            return ScriptedModel(messages=iter([
                AIMessage(content="", tool_calls=[{"name": "write_file", "id": "call-1",
                          "args": {"file_path": f"/artifacts/{artifact}", "content": json.dumps(content)}}]),
                AIMessage(content="done"),
            ]))

        models = {"stage1-context": scripted("01_context.json", {"scope": "bank"}),
                  "stage2-report": scripted("02_report.json", {"summary": "draft"})}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_bundle(root)
            (root / "input").mkdir()
            (root / "input/architecture-context.json").write_text("{}")
            result = run_stages(bundle, root / "input", root / "workspace", root / "output",
                                lambda stage_dir, workspace: build_stage_agent(stage_dir, workspace, models[stage_dir.name]))
            self.assertEqual(result.status, "awaiting_review", result.stages)
            self.assertEqual(json.loads((root / "workspace/artifacts/02_report.json").read_text()), {"summary": "draft"})
            # Stage definitions are mounted read-only; nothing is written back into the bundle.
            self.assertFalse(any(path.name.endswith(".json") for path in (bundle / "stage1-context").rglob("*")))


if __name__ == "__main__":
    unittest.main()
