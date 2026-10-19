import json
import unittest
from pathlib import Path

from examples.atam.deepagents.run import (
    AtamReportPayload,
    _build_prompt,
    _compose_report,
    _load_case,
    _validate_report,
)


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "case-studies/architecture-eval/ATAM/data/banking.json"
REPORT_TEMPLATE = ROOT / "examples/atam/report-template.json"


class AtamDemoTests(unittest.TestCase):
    def test_generation_prompt_contains_only_evaluation_inputs(self):
        # Reference outputs are held back to avoid leaking expected answers into generation.
        evaluation_inputs = _load_case(CASE)
        source_case = json.loads(CASE.read_text(encoding="utf-8"))
        reference_outputs = source_case["ATAM_Evaluation"]["ground_truth_outputs"]
        prompt = _build_prompt(evaluation_inputs)

        self.assertIn(evaluation_inputs["system_description"], prompt)
        self.assertNotIn("ground_truth_outputs", prompt)
        self.assertNotIn(json.dumps(reference_outputs, indent=2), prompt)

    def test_report_validator_requires_template_sections(self):
        # A syntactically valid report still needs every section in the shared contract.
        template = json.loads(REPORT_TEMPLATE.read_text(encoding="utf-8"))
        report = {"ATAM_Evaluation": template["ATAM_Evaluation"]}
        _validate_report(report)

        report["ATAM_Evaluation"]["evaluation_results"].pop("analysis_records")
        with self.assertRaisesRegex(ValueError, "analysis_records"):
            _validate_report(report)

    def test_pydantic_response_is_composed_with_original_inputs(self):
        # The model owns generated sections; the runner preserves the source inputs verbatim.
        payload = AtamReportPayload.model_validate(
            {
                "metadata": {
                    "system_name": "Event framework",
                    "date": None,
                    "ref": None,
                    "evaluator_organization": None,
                    "phase_1_attendees": [],
                    "phase_2_attendees": [],
                },
                "evaluation_results": {
                    "utility_tree": {"root": "Utility", "quality_attribute_nodes": []},
                    "architectural_approaches": [],
                    "analysis_records": [],
                    "scenarios": [],
                },
            }
        )
        inputs = {"system_description": "An event framework"}

        report = _compose_report(inputs, payload)

        self.assertEqual(report["ATAM_Evaluation"]["evaluation_inputs"], inputs)
        self.assertEqual(report["ATAM_Evaluation"]["metadata"]["system_name"], "Event framework")
        self.assertIn("analysis_records", report["ATAM_Evaluation"]["evaluation_results"])


if __name__ == "__main__":
    unittest.main()
