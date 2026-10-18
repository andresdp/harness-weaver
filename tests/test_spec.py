from pathlib import Path
import unittest

from harnessweaver.spec import SpecLoadError, load_spec, validate_spec


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "atam" / "harnessspec.yaml"


class SpecValidationTests(unittest.TestCase):
    def test_atam_example_is_valid_and_references_exist(self):
        document = load_spec(EXAMPLE)
        self.assertEqual(validate_spec(document, EXAMPLE), [])

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


if __name__ == "__main__":
    unittest.main()
