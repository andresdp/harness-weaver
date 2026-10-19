from pathlib import Path
import unittest

from harnessweaver.spec import SpecLoadError, load_spec, validate_spec


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "atam" / "harnessspec.yaml"
EXAMPLE_V02 = ROOT / "examples" / "atam" / "harnessspec-v0.2.yaml"


class SpecValidationTests(unittest.TestCase):
    def test_atam_example_is_valid_and_references_exist(self):
        document = load_spec(EXAMPLE)
        self.assertEqual(validate_spec(document, EXAMPLE), [])

    def test_v02_atam_ir_models_method_and_semantic_state(self):
        document = load_spec(EXAMPLE_V02)
        self.assertEqual(validate_spec(document, EXAMPLE_V02), [])
        self.assertEqual(document["spec_version"], "0.2")
        self.assertIn("methodology", document)
        self.assertIn("semantic_state", document)
        self.assertTrue(document["semantic_state"]["assessments"][0]["evidence_refs"])

    def test_unknown_version_is_actionable(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            spec = Path(directory) / "unknown.json"
            spec.write_text('{"spec_version":"9.0"}', encoding="utf-8")
            with self.assertRaisesRegex(SpecLoadError, "unsupported spec_version '9.0'"):
                load_spec(spec)

    def test_missing_fields_and_unknown_role_are_reported(self):
        document = {
            "spec_version": "0.1", "id": "broken", "domain": "example",
            "workflow": {"id": "w", "purpose": "test"}, "sources": [],
            "roles": [], "stages": [{"id": "s", "role": "missing", "purpose": "test", "inputs": [], "outputs": []}],
            "artifacts": [], "verification": [], "human_gates": [], "runtime_requirements": [],
        }
        del document["domain"]
        messages = [str(issue) for issue in validate_spec(document)]
        self.assertTrue(any("unknown role 'missing'" in message for message in messages))
        self.assertTrue(any("'domain' is a required property" in message for message in messages))

    def test_missing_local_reference_is_reported(self):
        document = load_spec(EXAMPLE)
        document["sources"][0]["ref"] = "missing.py"
        issues = validate_spec(document, EXAMPLE)
        self.assertTrue(any("missing.py" in issue.message for issue in issues))

    def test_v02_checks_source_skill_and_input_artifact_references(self):
        document = load_spec(EXAMPLE_V02)
        document["sources"][0]["ref"] = "missing-source.py"
        document["roles"][0]["skill_refs"] = ["missing-skill.md"]
        document["artifacts"][0]["ref"] = "missing-input.json"

        messages = [str(issue) for issue in validate_spec(document, EXAMPLE_V02)]
        self.assertTrue(any("missing-source.py" in message for message in messages))
        self.assertTrue(any("missing-skill.md" in message for message in messages))
        self.assertTrue(any("missing-input.json" in message for message in messages))

    def test_v02_rejects_missing_methodology_and_invalid_semantic_status(self):
        document = load_spec(EXAMPLE_V02)
        del document["methodology"]
        document["semantic_state"]["assessments"][0]["status"] = "finished"

        messages = [str(issue) for issue in validate_spec(document)]
        self.assertTrue(any("'methodology' is a required property" in message for message in messages))
        self.assertTrue(any("finished" in message for message in messages))

    def test_v02_accepts_each_declared_orchestration_profile(self):
        document = load_spec(EXAMPLE_V02)
        for strategy, interaction in (
            ("supervisor", "one_shot_specialist_delegation"),
            ("sequential_pipeline", "typed_artifact_handoffs"),
            ("fan_out_fan_in", "parallel_specialist_delegation"),
        ):
            document["orchestration"] = {"workflow_strategy": strategy, "agent_interaction": interaction}
            self.assertEqual(validate_spec(document, EXAMPLE_V02), [])

    def test_v02_rejects_unsupported_orchestration_pairing(self):
        document = load_spec(EXAMPLE_V02)
        document["orchestration"] = {
            "workflow_strategy": "sequential_pipeline",
            "agent_interaction": "one_shot_specialist_delegation",
        }
        messages = [str(issue) for issue in validate_spec(document)]
        self.assertTrue(any("unsupported workflow_strategy/agent_interaction combination" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
