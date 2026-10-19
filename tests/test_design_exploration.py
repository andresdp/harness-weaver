import unittest
from pathlib import Path

from harnessweaver.spec import load_spec, validate_spec


class DesignExplorationProfileTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve().parents[1] / "examples/design-exploration/harnessspec.yaml"
        self.spec = load_spec(self.path)

    def test_profile_validates_and_source_files_resolve(self):
        self.assertEqual(validate_spec(self.spec, self.path), [])

    def test_add_is_declared_and_rearch_remains_a_contrast(self):
        self.assertEqual(self.spec["methodology"]["id"], "add-informed-design-exploration")
        notes = " ".join(self.spec["methodology"]["adaptations"])
        self.assertIn("ReArch", notes)
        self.assertTrue(any(source["id"] == "rearch-contrast" for source in self.spec["sources"]))

    def test_profile_requires_case_inputs_and_architect_gate(self):
        self.assertEqual(self.spec["semantic_state"]["assessments"][0]["status"], "unknown")
        self.assertEqual(self.spec["semantic_state"]["gaps"][0]["status"], "open")
        self.assertEqual(self.spec["artifacts"][0]["ref"], "artifact:design-brief-input")
        self.assertEqual(self.spec["human_gates"][0]["id"], "architect-design-review")
        self.assertIn("architecture-alternatives", self.spec["stages"][1]["outputs"])
        self.assertIn("decision-record", self.spec["stages"][2]["outputs"])


if __name__ == "__main__":
    unittest.main()
