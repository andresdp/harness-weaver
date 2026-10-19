import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from benchmarks.saam import pilot
from harnessweaver.spec import load_spec, validate_spec


def valid_prediction():
    return {"SAAM_Evaluation": {
        "scenarios": [{"scenario_id": f"S-{i:02d}", "scenario_text": "represented"} for i in range(1, 7)],
        "scenario_classification": [{"scenario_id": f"S-{i:02d}", "classification": "Direct" if i == 2 else "Indirect"} for i in range(1, 7)],
        "scenario_evaluations": [{"scenario_id": sid} for sid in ("S-01", "S-03", "S-04", "S-05", "S-06")],
        "scenario_interactions": [], "overall_results": {}, "recommendations": []
    }}


class SaamPilotTests(unittest.TestCase):
    def test_saam_harnessspec_v02_validates(self):
        spec_path = Path(__file__).resolve().parents[1] / "examples/saam/harnessspec.yaml"
        self.assertEqual(validate_spec(load_spec(spec_path), spec_path), [])

    def test_prepare_excludes_evaluator_truth_and_is_unique(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(pilot, "RUNS_DIR", Path(tmp)):
            run = pilot.prepare("isolated-1", "baseline")
            input_text = (run / "evaluation_input.json").read_text()
            manifest = json.loads((run / "manifest.json").read_text())
            self.assertNotIn("ground_truth_outputs", input_text)
            self.assertNotIn("scenario_classification", input_text)
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
            prediction["SAAM_Evaluation"]["scenario_evaluations"].append({"scenario_id": "S-02", "affected_components": ["unknown"]})
            path.write_text(json.dumps(prediction))
            self.assertEqual(pilot.check(path), [])  # S-02 has no extracted evaluation reference.
            prediction["SAAM_Evaluation"]["scenario_evaluations"].append({"scenario_id": "S-09"})
            path.write_text(json.dumps(prediction))
            self.assertTrue(any("unavailable scenario S-09" in item for item in pilot.check(path)))

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


if __name__ == "__main__":
    unittest.main()
