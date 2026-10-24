import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmarks.saam import pilot
from harnessweaver.spec import load_spec, validate_spec


def valid_prediction():
    # Keep test scenario output faithful to the case source used by the checker.
    config = pilot.read_json(pilot.CONFIG_PATH)
    source_doc = pilot.read_json(pilot.resolve(config["source_case"]))["SAAM_Evaluation_Extract"]
    source = source_doc["ground_truth_outputs"]
    def cite(pointer):
        return {"evidence_refs": [{"source_pointer": pointer}]}
    return {"SAAM_Evaluation": {
        "scenarios": [{"scenario_id": item["scenario_id"], "scenario_text": item["scenario_text"]} for item in source["scenarios"]],
        "scenario_classification": [{"scenario_id": f"S-{i:02d}", "classification": "Direct" if i == 2 else "Indirect", **cite(f"/scenario_inputs/{i - 1}/scenario_text")} for i in range(1, 7)],
        "scenario_evaluations": [{"scenario_id": sid, **cite("/architecture_description/architectures/0/key_components/0/component_name")} for sid in ("S-01", "S-03", "S-04", "S-05", "S-06")],
        "scenario_interactions": [],
        "overall_results": {
            "architectural_strengths": [{"statement": "A source-grounded strength", **cite("/system_context/system_name")}],
            "architectural_weaknesses": [{"statement": "A source-grounded weakness", **cite("/architecture_description/documentation_level")}],
            "modifiability_assessment": {"statement": "A bounded assessment", **cite("/evaluation_focus/primary_quality_attribute")},
        },
        "recommendations": [{"statement": "A supported recommendation", **cite("/architecture_description/architectures/0/key_components/0/component_name")}],
    }}


class SaamPilotTests(unittest.TestCase):
    def test_saam_harnessspec_v02_validates(self):
        spec_path = Path(__file__).resolve().parents[1] / "pilots/saam/harnessspec.yaml"
        self.assertEqual(validate_spec(load_spec(spec_path), spec_path), [])

    def test_prepare_excludes_evaluator_truth_and_is_unique(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(pilot, "RUNS_DIR", Path(tmp)):
            run = pilot.prepare("isolated-1", "baseline")
            input_text = (run / "evaluation_input.json").read_text()
            manifest = json.loads((run / "manifest.json").read_text())
            input_data = json.loads(input_text)["SAAM_Evaluation_Extract"]["evaluation_inputs"]
            self.assertNotIn("ground_truth_outputs", input_text)
            self.assertNotIn("scenario_classification", input_text)
            self.assertEqual([item["scenario_id"] for item in input_data["scenario_inputs"]], [f"S-{i:02d}" for i in range(1, 7)])
            self.assertTrue(all(set(item) == {"scenario_id", "scenario_text"} for item in input_data["scenario_inputs"]))
            self.assertEqual(manifest["scenario_input_provenance"]["count"], 6)
            self.assertFalse(manifest["scenario_input_provenance"]["evaluation_outputs_exposed"])
            self.assertNotIn("scenario_evaluations", input_text)
            self.assertNotIn("scenario_interactions", input_text)
            self.assertNotIn("recommendations", input_text)
            self.assertEqual(manifest["partial_reference"]["represented_scenarios"], 6)
            self.assertEqual(manifest["partial_reference"]["known_total_scenarios"], 15)
            self.assertIsNone(manifest["cost_usd"])
            with self.assertRaises(FileExistsError):
                pilot.prepare("isolated-1", "spec-guided")

    def test_checks_represented_scenario_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prediction.json"
            prediction = valid_prediction()
            path.write_text(json.dumps(prediction))
            self.assertEqual(pilot.check(path), [])
            prediction["SAAM_Evaluation"]["scenario_evaluations"].append({"scenario_id": "S-02", "affected_components": ["unknown"], "evidence_refs": [{"source_pointer": "/scenario_inputs/1/scenario_text"}]})
            path.write_text(json.dumps(prediction))
            self.assertEqual(pilot.check(path), [])  # S-02 has no extracted evaluation reference.
            prediction["SAAM_Evaluation"]["scenario_evaluations"].append({"scenario_id": "S-09"})
            path.write_text(json.dumps(prediction))
            self.assertTrue(any("unavailable scenario S-09" in item for item in pilot.check(path)))

    def test_checks_evaluation_fields_against_source_key_evaluations(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prediction.json"
            prediction = valid_prediction()
            prediction["SAAM_Evaluation"]["scenario_evaluations"][0]["affected_components"] = ["invented.dll"]
            path.write_text(json.dumps(prediction))
            self.assertTrue(any("scenario_evaluations[S-01].affected_components differs" in item for item in pilot.check(path)))

    def test_checks_source_scenario_text_and_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prediction.json"
            prediction = valid_prediction()
            result = prediction["SAAM_Evaluation"]
            result["scenarios"][0]["scenario_text"] = "rewritten scenario"
            result["scenarios"].append(dict(result["scenarios"][1]))
            path.write_text(json.dumps(prediction))
            problems = pilot.check(path)
            self.assertTrue(any("scenario_text differs from source" in item for item in problems))
            self.assertTrue(any("duplicate scenario ID S-02" in item for item in problems))

    def test_checks_evidence_pointers_against_generation_visible_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prediction.json"
            prediction = valid_prediction()
            result = prediction["SAAM_Evaluation"]
            result["scenario_classification"][0]["evidence_refs"][0]["source_pointer"] = "/ground_truth_outputs/scenario_classification/0"
            result["scenario_evaluations"][0]["evidence_refs"] = []
            path.write_text(json.dumps(prediction))
            problems = pilot.check(path)
            self.assertTrue(any("evidence pointer does not resolve" in item for item in problems))
            self.assertTrue(any("must cite at least one generation-input evidence pointer" in item for item in problems))
            result["scenario_classification"][0]["evidence_refs"][0]["source_pointer"] = "/architecture_description/architectures/0/key_components/0"
            result["scenario_evaluations"][0]["evidence_refs"] = [{"source_pointer": "/scenario_inputs/0/scenario_text"}]
            path.write_text(json.dumps(prediction))
            self.assertTrue(any("must point to a non-empty scalar source value" in item for item in pilot.check(path)))

    def test_json_pointer_rejects_non_rfc_escapes_and_array_indices(self):
        document = {"scenario_inputs": [{"scenario_text": "source text"}], "a~1b": "valid escaped key"}
        self.assertEqual(pilot.resolve_json_pointer(document, "/a~01b"), "valid escaped key")
        for pointer in (
            "/scenario_inputs/00/scenario_text",
            "/scenario_inputs/٠/scenario_text",
            "/scenario_inputs/0/scenario~2text",
            "/scenario_inputs/0/scenario~",
        ):
            with self.subTest(pointer=pointer), self.assertRaises(ValueError):
                pilot.resolve_json_pointer(document, pointer)

    def test_checker_reports_non_object_items_in_evidence_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prediction.json"
            prediction = valid_prediction()
            result = prediction["SAAM_Evaluation"]
            result["scenario_interactions"].append(None)
            result["recommendations"].append("unsupported shape")
            path.write_text(json.dumps(prediction))
            problems = pilot.check(path)
            self.assertTrue(any("scenario_interactions[0] must be an object" in item for item in problems))
            self.assertTrue(any("recommendations[1] must be an object" in item for item in problems))

    def test_checker_reports_non_object_overall_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prediction.json"
            prediction = valid_prediction()
            prediction["SAAM_Evaluation"]["overall_results"] = "bad"
            path.write_text(json.dumps(prediction))
            problems = pilot.check(path)
            self.assertIn("overall_results must be an object", problems)

    def test_checks_missing_classifications_and_interaction_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prediction.json"
            prediction = valid_prediction()
            result = prediction["SAAM_Evaluation"]
            result["scenario_classification"].pop()
            result["scenario_interactions"].append({"interacting_scenarios": ["S-01", "S-09"]})
            path.write_text(json.dumps(prediction))
            problems = pilot.check(path)
            self.assertTrue(any("missing represented classifications" in item for item in problems))
            self.assertTrue(any("references unavailable scenarios: S-09" in item for item in problems))

    def test_execution_record_is_write_once_and_inside_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            run.mkdir()
            (run / "manifest.json").write_text("{}")
            prediction = run / "prediction.json"
            prediction.write_text("{}")
            kwargs = dict(arm="baseline", runtime="test", model="model-x", settings={}, prediction=prediction)
            target = pilot.record_execution(run, **kwargs)
            record = json.loads(target.read_text())
            self.assertIsNone(record["cost_usd"])
            self.assertIsNone(record["latency_seconds"])
            with self.assertRaises(FileExistsError):
                pilot.record_execution(run, **kwargs)
            outside = Path(tmp) / "outside.json"
            outside.write_text("{}")
            with self.assertRaises(ValueError):
                pilot.record_execution(Path(tmp) / "run", **{**kwargs, "prediction": outside})

    def test_execution_record_rejects_nested_credentials_before_writing(self):
        for settings in (
            {"headers": {"Authorization": "Bearer hidden"}},
            {"cookies": ["session=hidden"]},
            {"tls": {"private-key": "hidden"}},
            {"provider_config": "sk-proj-1234567890abcdefghijkl"},
        ):
            with self.subTest(settings=settings), tempfile.TemporaryDirectory() as tmp:
                run = Path(tmp) / "run"
                run.mkdir()
                (run / "manifest.json").write_text("{}")
                prediction = run / "prediction.json"
                prediction.write_text("{}")
                with self.assertRaisesRegex(ValueError, "must not contain credentials"):
                    pilot.record_execution(
                        run, arm="baseline", runtime="test", model="model-x", settings=settings,
                        prediction=prediction,
                    )
                self.assertFalse((run / "execution.json").exists())

    def test_failed_execution_can_be_recorded_without_prediction(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            run.mkdir()
            (run / "manifest.json").write_text("{}")
            record_path = pilot.record_execution(
                run, arm="baseline", runtime="langchain-single-call", model="model-x",
                settings={}, prediction=run / "prediction.json", status="failed", error_type="TimeoutError",
            )
            record = json.loads(record_path.read_text())
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["error_type"], "TimeoutError")
            self.assertIsNone(record["prediction"])

    def test_blind_review_packet_hides_arm_labels_and_preserves_paired_input(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(pilot, "RUNS_DIR", Path(tmp)):
            for run_id, arm in (("b", "baseline"), ("g", "spec-guided")):
                run = Path(tmp) / run_id
                run.mkdir()
                input_path = run / "evaluation_input.json"
                input_path.write_text('{"input": 1}')
                prediction = run / "prediction.json"
                prediction.write_text(json.dumps({"SAAM_Evaluation": valid_prediction()["SAAM_Evaluation"]}))
                (run / "manifest.json").write_text(json.dumps({"evaluation_input_sha256": pilot.sha256(input_path)}))
                (run / "execution.json").write_text(json.dumps({
                    "arm": arm, "prediction": "prediction.json", "prediction_sha256": pilot.sha256(prediction),
                }))
            packet = pilot.prepare_blind_review("packet-1", "b", "g")
            for reviewer in ("reviewer-1", "reviewer-2"):
                folder = packet / reviewer
                reports = list(folder.glob("P-*.json"))
                self.assertEqual(len(reports), 2)
                self.assertTrue(all("arm" not in report.read_text() for report in reports))
                self.assertTrue((folder / "case-input.json").is_file())
            key = json.loads((Path(tmp) / ".review-keys/packet-1.json").read_text())
            self.assertEqual(set(key.values()), {"baseline", "spec-guided"})


class SaamRunnerSchemaTests(unittest.TestCase):
    def test_runner_passes_treatment_in_system_message(self):
        from benchmarks.saam.runner import build_messages

        messages = build_messages("SAAM treatment prompt", {"system_context": {"system_name": "WRCS"}})
        self.assertEqual(messages[0][0], "system")
        self.assertIn("SAAM treatment prompt", messages[0][1])
        self.assertEqual(messages[1][0], "human")
        self.assertIn("WRCS", messages[1][1])

    def test_shared_pydantic_output_contract_validates(self):
        from benchmarks.saam.runner import SaamEvaluation

        report = SaamEvaluation.model_validate({
            "scenarios": [{"scenario_id": "S-01", "scenario_text": "source text"}],
            "scenario_classification": [{"scenario_id": "S-01", "classification": "Direct", "rationale": "supported", "evidence_refs": [{"source_pointer": "/scenario_inputs/0/scenario_text"}]}],
            "scenario_evaluations": [], "scenario_interactions": [],
            "overall_results": {"architectural_strengths": [], "architectural_weaknesses": [], "modifiability_assessment": None},
            "recommendations": [],
        })
        self.assertEqual(report.scenarios[0].scenario_id, "S-01")

    def test_runner_records_model_initialization_failure_and_prompt_sources(self):
        from benchmarks.saam import runner

        with tempfile.TemporaryDirectory() as tmp, patch.object(pilot, "RUNS_DIR", Path(tmp)):
            with patch("langchain.chat_models.init_chat_model", side_effect=RuntimeError("provider setup failed")):
                with self.assertRaisesRegex(RuntimeError, "provider setup failed"):
                    runner.generate("failed-initialization", "baseline", "fake:model")

            record = json.loads((Path(tmp) / "failed-initialization" / "execution.json").read_text())
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["error_type"], "RuntimeError")
            self.assertEqual(record["settings"]["prompt_files"], ["baseline_prompt.md"])
            self.assertIsNone(record["prediction"])

    def test_runner_records_provider_failure_latency(self):
        from benchmarks.saam import runner

        class FailingModel:
            def with_structured_output(self, _schema):
                return self

            def invoke(self, _messages):
                raise TimeoutError("provider timed out")

        with tempfile.TemporaryDirectory() as tmp, patch.object(pilot, "RUNS_DIR", Path(tmp)):
            with patch("langchain.chat_models.init_chat_model", return_value=FailingModel()):
                with self.assertRaisesRegex(TimeoutError, "provider timed out"):
                    runner.generate("failed-provider-call", "baseline", "fake:model")

            record = json.loads((Path(tmp) / "failed-provider-call" / "execution.json").read_text())
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["error_type"], "TimeoutError")
            self.assertIsInstance(record["latency_seconds"], float)


if __name__ == "__main__":
    unittest.main()
