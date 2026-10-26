import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmarks.atam import pilot


def valid_semantic_state():
    return {
        "context_status": {"value": "sufficient", "evidence": ["Scope is in the supplied inputs."]},
        "driver_status": {"value": "partial", "evidence": ["Some quality drivers are supplied."]},
        "architecture_evidence_status": {"value": "partial", "evidence": ["Architecture evidence is incomplete."]},
        "scenario_analysis_status": {"value": "reviewed", "evidence": ["The evidence reviewer checked the analysis."]},
        "report_status": {"value": "draft", "evidence": ["Architect review is still pending."]},
        "gaps": [],
    }


class AtamBenchmarkTests(unittest.TestCase):
    def test_report_checker_accepts_current_typed_atam_report_envelope(self):
        prediction = {
            "ATAM_Evaluation": {
                "evaluation_inputs": {
                    "raw_candidate_scenarios": [{"id": "RS-1", "description": "A file is updated."}],
                },
                "evaluation_results": {
                    "semantic_state": valid_semantic_state(),
                    "architectural_approaches": [{"approach_name": "A", "description": "Evidence", "addressed_attributes": ["modifiability"]}],
                    "utility_tree": {"quality_attribute_nodes": [{
                        "attribute_name": "modifiability",
                        "children": [{
                            "scenario_id": "MOD-1",
                            "scenario_description": "A user updates a module.",
                            "origin": {
                                "kind": "raw_candidate_scenario",
                                "source_scenario_id": "RS-1",
                                "basis": "observed",
                                "source_refs": ["evaluation_inputs.raw_candidate_scenarios[0]"],
                            },
                        }],
                    }]},
                    "scenarios": [{
                        "id": "MOD-1",
                        "scenario_text": "A user updates a module.",
                        "primary_quality_attribute": ["modifiability"],
                        "origin": {
                            "kind": "raw_candidate_scenario",
                            "source_scenario_id": "RS-1",
                            "basis": "observed",
                            "source_refs": ["evaluation_inputs.raw_candidate_scenarios[0]"],
                        },
                    }],
                    "analysis_records": [{
                        "scenario_reference": {"id": "MOD-1", "text": "A user updates a module."},
                        "findings": {"risks": [], "non_risks": [], "sensitivity_points": [], "tradeoff_points": []},
                    }],
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "report.json"
            path.write_text(json.dumps(prediction))
            (root / "source_case.json").write_text(json.dumps({
                "ATAM_Evaluation": {
                    "evaluation_inputs": {
                        "raw_candidate_scenarios": [{"id": "RS-1", "description": "A file is updated."}],
                    },
                },
            }))
            config = root / "pilot.json"
            config.write_text(json.dumps({
                "source_case": "source_case.json",
                "required_sections": ["architectural_approaches", "utility_tree", "scenarios", "analysis_records"],
                "required_finding_groups": ["risks", "non_risks", "sensitivity_points", "tradeoff_points"],
            }))
            with patch.object(pilot, "CONFIG_PATH", config):
                self.assertEqual(pilot.check(path), [])

                # Analysis references must resolve by stable report ID, not by matching source prose.
                prediction["ATAM_Evaluation"]["evaluation_results"]["analysis_records"][0]["scenario_reference"] = {
                    "text": "  A user   updates a module.  ",
                }
                path.write_text(json.dumps(prediction))
                problems = pilot.check(path)
                self.assertTrue(any("scenario_reference.id must resolve" in problem for problem in problems))

                prediction["ATAM_Evaluation"]["evaluation_results"]["analysis_records"][0]["scenario_reference"] = {
                    "id": "MISSING",
                    "text": "A different scenario.",
                }
                path.write_text(json.dumps(prediction))
                problems = pilot.check(path)
                self.assertTrue(any("scenario_reference.id must resolve" in problem for problem in problems))

    def test_report_checker_does_not_trust_prediction_embedded_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "report.json"
            prediction = {
                "ATAM_Evaluation": {
                    "evaluation_inputs": {"raw_candidate_scenarios": [{"id": "FAKE", "description": "Forged source."}]},
                    "evaluation_results": {
                        "semantic_state": valid_semantic_state(),
                        "architectural_approaches": [{"approach_name": "A", "description": "Evidence", "addressed_attributes": ["modifiability"]}],
                        "utility_tree": {"quality_attribute_nodes": [{
                            "attribute_name": "modifiability",
                            "children": [{
                                "scenario_id": "GEN-1",
                                "scenario_description": "A generated scenario.",
                                "origin": {
                                    "kind": "raw_candidate_scenario",
                                    "source_scenario_id": "FAKE",
                                    "basis": "observed",
                                    "source_refs": ["evaluation_inputs.raw_candidate_scenarios[0]"],
                                },
                            }],
                        }]},
                        "scenarios": [{
                            "id": "GEN-1",
                            "scenario_text": "A generated scenario.",
                            "primary_quality_attribute": ["modifiability"],
                            "origin": {
                                "kind": "raw_candidate_scenario",
                                "source_scenario_id": "FAKE",
                                "basis": "observed",
                                "source_refs": ["evaluation_inputs.raw_candidate_scenarios[0]"],
                            },
                        }],
                        "analysis_records": [{
                            "scenario_reference": {"id": "GEN-1", "text": "A generated scenario."},
                            "findings": {"risks": [], "non_risks": [], "sensitivity_points": [], "tradeoff_points": []},
                        }],
                    },
                },
            }
            path.write_text(json.dumps(prediction))
            (root / "source_case.json").write_text(json.dumps({
                "ATAM_Evaluation": {"evaluation_inputs": {"raw_candidate_scenarios": [{"id": "RS-1", "description": "A real source."}]}},
            }))
            config = root / "pilot.json"
            config.write_text(json.dumps({
                "source_case": "source_case.json",
                "required_sections": ["architectural_approaches", "utility_tree", "scenarios", "analysis_records"],
                "required_finding_groups": ["risks", "non_risks", "sensitivity_points", "tradeoff_points"],
            }))
            with patch.object(pilot, "CONFIG_PATH", config):
                problems = pilot.check(path)
            self.assertTrue(any("source_scenario_id is not a raw source scenario ID" in problem for problem in problems))

    def test_report_checker_requires_semantic_state_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "report.json"
            prediction = {
                "ATAM_Evaluation": {
                    "evaluation_results": {
                        "semantic_state": valid_semantic_state(),
                        "architectural_approaches": [],
                        "utility_tree": {"quality_attribute_nodes": []},
                        "scenarios": [],
                        "analysis_records": [],
                    }
                }
            }
            prediction["ATAM_Evaluation"]["evaluation_results"]["semantic_state"]["context_status"]["evidence"] = []
            path.write_text(json.dumps(prediction))
            source_case = root / "source_case.json"
            source_case.write_text(json.dumps({"ATAM_Evaluation": {"evaluation_inputs": {"raw_candidate_scenarios": [{"id": "RS-1", "description": "A source scenario."}]}}}))
            config = root / "pilot.json"
            config.write_text(json.dumps({
                "source_case": "source_case.json",
                "required_sections": ["architectural_approaches", "utility_tree", "scenarios", "analysis_records"],
                "required_finding_groups": ["risks", "non_risks", "sensitivity_points", "tradeoff_points"],
            }))
            with patch.object(pilot, "CONFIG_PATH", config):
                problems = pilot.check(path)
            self.assertTrue(any("semantic_state.context_status.evidence" in problem for problem in problems))

            semantic_state = prediction["ATAM_Evaluation"]["evaluation_results"]["semantic_state"]
            semantic_state["context_status"]["evidence"] = ["Valid evidence."]
            semantic_state["scenario_analysis_status"]["evidence"] = ["  "]
            semantic_state["report_status"]["value"] = "published"
            path.write_text(json.dumps(prediction))
            with patch.object(pilot, "CONFIG_PATH", config):
                problems = pilot.check(path)
            self.assertTrue(any("semantic_state.scenario_analysis_status.evidence" in problem for problem in problems))
            self.assertTrue(any("semantic_state.report_status.value" in problem for problem in problems))

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

        for unsafe_settings in (
            {"provider": {"access_token": "hidden"}},
            {"headers": {"Authorization": "Bearer hidden"}},
            {"cookies": ["session=hidden"]},
            {"tls": {"private-key": "hidden"}},
            {"provider_config": "sk-proj-1234567890abcdefghijkl"},
        ):
            with self.subTest(unsafe_settings=unsafe_settings), tempfile.TemporaryDirectory() as tmp:
                run_dir = Path(tmp)
                (run_dir / "manifest.json").write_text("{}")
                with self.assertRaisesRegex(ValueError, "must not contain credentials"):
                    pilot.record_execution(
                        run_dir, "spec-guided", "deepagents", "provider:model", unsafe_settings, None,
                        None, None, workflow_strategy="supervisor",
                        agent_interaction="one_shot_specialist_delegation", status="failed",
                    )
                self.assertFalse((run_dir / "execution.json").exists())

    def test_prepare_records_actual_spec_version_and_unique_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pilot, "RUNS_DIR", Path(tmp) / "runs"):
                run_dir = pilot.prepare("spec-version-check")
            manifest = json.loads((run_dir / "manifest.json").read_text())
            self.assertEqual(manifest["harness_spec_version"], "0.2")
            self.assertNotIn("ground_truth_outputs", (run_dir / "evaluation_input.json").read_text())


if __name__ == "__main__":
    unittest.main()
