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
        stages = {stage["id"]: stage for stage in self.spec["stages"]}
        self.assertEqual(stages["set-iteration-goal"]["outputs"], ["iteration-goal"])
        self.assertIn("artifact:iteration-goal", stages["develop-alternatives"]["inputs"])
        self.assertIn("architecture-alternatives", stages["develop-alternatives"]["outputs"])
        self.assertIn("decision-record", stages["compare-decisions"]["outputs"])

    def test_add_method_mapping_is_resolvable_and_records_human_review_adaptation(self):
        mapping = next(source for source in self.spec["sources"] if source["id"] == "add-method-mapping")
        mapping_path = (self.path.parent / mapping["ref"]).resolve()
        self.assertTrue(mapping_path.is_file())
        text = mapping_path.read_text(encoding="utf-8")
        for activity in (
            "Review and prioritize architectural drivers",
            "Establish the goal for the current design iteration",
            "Select architectural elements to refine or decompose",
            "Select design concepts",
            "Instantiate elements, relationships, responsibilities, and interfaces",
            "Sketch preliminary architecture views and record design decisions",
            "Analyze whether the iteration goal was achieved",
        ):
            self.assertIn(activity, text)
        self.assertIn("does not require approval after every intermediate step", text)
        self.assertIn("ReArch", text)
        criteria = (self.path.parent / "review-criteria.md").read_text(encoding="utf-8")
        self.assertIn("**Iteration control:**", criteria)


if __name__ == "__main__":
    unittest.main()
