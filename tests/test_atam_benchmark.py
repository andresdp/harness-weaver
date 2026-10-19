import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmarks.atam import pilot


class AtamBenchmarkTests(unittest.TestCase):
    def test_report_checker_accepts_current_typed_atam_report_envelope(self):
        prediction = {
            "ATAM_Evaluation": {
                "evaluation_inputs": {
                    "raw_candidate_scenarios": [{"id": "RS-1", "description": "A file is updated."}],
                },
                "evaluation_results": {
                    "architectural_approaches": [{"approach_name": "A", "description": "Evidence", "addressed_attributes": ["modifiability"]}],
                    "utility_tree": {"quality_attribute_nodes": [{"attribute_name": "modifiability"}]},
                    "scenarios": [{"scenario_text": "A user updates a module."}],
                    "analysis_records": [{
                        "scenario_reference": {"id": "RS-1", "text": "A file is updated."},
                        "findings": {"risks": [], "non_risks": [], "sensitivity_points": [], "tradeoff_points": []},
                    }],
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(json.dumps(prediction))
            self.assertEqual(pilot.check(path), [])

    def test_run_record_tracks_profile_status_and_rejects_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "manifest.json").write_text("{}")
            failed = pilot.record_execution(
                run_dir, "spec-guided", "deepagents", "provider:model", {"temperature": 0}, None,
                None, None, workflow_strategy="fan_out_fan_in",
                agent_interaction="parallel_specialist_delegation", status="failed",
            )
            record = json.loads(failed.read_text())
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["workflow_strategy"], "fan_out_fan_in")
            self.assertEqual(record["agent_interaction"], "parallel_specialist_delegation")
            self.assertIsNone(record["output_path"])

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "manifest.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "must not contain credentials"):
                pilot.record_execution(
                    run_dir, "spec-guided", "deepagents", "provider:model", {"provider": {"access_token": "hidden"}}, None,
                    None, None, workflow_strategy="supervisor",
                    agent_interaction="one_shot_specialist_delegation", status="failed",
                )

    def test_prepare_records_actual_spec_version_and_unique_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pilot, "RUNS_DIR", Path(tmp) / "runs"):
                run_dir = pilot.prepare("spec-version-check")
            manifest = json.loads((run_dir / "manifest.json").read_text())
            self.assertEqual(manifest["harness_spec_version"], "0.2")
            self.assertNotIn("ground_truth_outputs", (run_dir / "evaluation_input.json").read_text())


if __name__ == "__main__":
    unittest.main()
