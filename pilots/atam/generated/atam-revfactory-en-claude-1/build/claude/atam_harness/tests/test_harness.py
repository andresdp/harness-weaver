"""Self-tests for the ATAM harness runtime. Run from the bundle root:

    python3 -m unittest discover -s atam_harness/tests -v

They use only the labelled placeholder fixture in fixture.py and a fake `claude` executable, and write only
under atam_harness/tests/_tmp/ (removed afterwards).
"""
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import atam  # noqa: E402
import fixture  # noqa: E402

TMP = HERE / "_tmp"
RUN = HERE.parent / "run.py"
FAKE = HERE / "fake_claude.py"


def run_pipeline(name, scenario, extra=()):
    base = TMP / name
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True)
    inp = base / "input.json"
    inp.write_text(json.dumps(fixture.evaluation_input()))
    ws = base / "_workspace"
    env = dict(os.environ, ATAM_WORKSPACE=str(ws), FAKE_SCENARIO=scenario)
    proc = subprocess.run([sys.executable, str(RUN), "--input", str(inp), "--run-id", f"TEST-{name}",
                           "--claude", str(FAKE), *extra], capture_output=True, text=True, env=env)
    return proc, ws


def agent_calls(ws):
    p = ws / ".runtime" / "fake_calls.txt"
    return p.read_text().split() if p.exists() else []


class PipelineTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP, ignore_errors=True)

    def test_clean_run_still_executes_revision_stage(self):
        proc, ws = run_pipeline("clean", "clean")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(agent_calls(ws), [atam.STAGE_BY_ID[s]["agent"] for s in atam.STAGE_IDS[1:]])
        final = atam.load_json(ws / atam.F06)
        self.assertFalse(final["revision"]["applied"])
        self.assertEqual(final["revision"]["changed_locations"], [])
        self.assertEqual(final["revision"]["remaining_failures"], [])
        self.assertTrue(final["ready_for_architect_review"])
        self.assertTrue(final["readiness_basis"]["stage_order_verified"])
        initial = atam.load_json(ws / atam.F06I)
        self.assertNotIn("ready_for_architect_review", initial)
        report = atam.load_json(ws / atam.F05)
        res = report["ATAM_Evaluation"]["evaluation_results"]
        self.assertEqual(res["semantic_state"]["report_status"]["value"], "draft")
        r1 = res["analysis_records"][0]["findings"]["risks"][0]["rationale"]
        self.assertTrue(r1.endswith("(evidence: AE-1; basis: inferred)"), r1)
        r2 = res["analysis_records"][1]["findings"]["risks"][0]["rationale"]
        self.assertTrue(r2.endswith("(evidence: AE-1, AP-1; basis: inferred)"), r2)
        outside = json.dumps({k: v for k, v in res.items() if k != "semantic_state"})
        self.assertNotRegex(outside, r"\bG-\d")
        ledger = atam.load_ledger(ws)
        order = [e["stage"] for e in ledger["events"] if e["event"] == "complete"]
        self.assertEqual(order, atam.STAGE_IDS)

    def test_absence_labelled_observed_is_corrected_by_revision(self):
        proc, ws = run_pipeline("absence", "absence_observed")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        initial = atam.load_json(ws / atam.F06I)
        fails = [c for c in initial["checks"] if c["result"] == "fail"]
        self.assertTrue(any(c["check_id"] == "UNC-ABSENCE-BASIS" for c in fails), fails)
        final = atam.load_json(ws / atam.F06)
        self.assertTrue(final["revision"]["applied"])
        self.assertIn("/ATAM_Evaluation/evaluation_results/analysis_records/0/findings/risks/0/rationale",
                      final["revision"]["changed_locations"])
        self.assertTrue(final["ready_for_architect_review"])

    def test_unmeasured_performance_claim_blocks_readiness(self):
        proc, ws = run_pipeline("perf", "perf_claim")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        final = atam.load_json(ws / atam.F06)
        self.assertFalse(final["ready_for_architect_review"])
        self.assertIn("UNC-PERF-ATTAINMENT", [r["check_id"] for r in final["revision"]["remaining_failures"]])

    def test_gap_id_in_analysis_fails_stage4_gate(self):
        proc, ws = run_pipeline("gapid", "gap_in_measure")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("gap identifier G-2-2 outside a gap record", proc.stderr)
        self.assertFalse((ws / atam.F05D).exists())

    def test_stray_write_fails_scope_gate(self):
        proc, ws = run_pipeline("stray", "stray_write")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("write scope: ws:notes.txt was created", proc.stderr)

    def test_synthesizer_cannot_edit_projection(self):
        proc, ws = run_pipeline("editdraft", "edit_draft")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("differs from the deterministic projection", proc.stderr)

    def test_reviewer_check_cannot_pass_without_change(self):
        proc, ws = run_pipeline("cheat", "reviewer_cheat")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("is marked pass but nothing changed at that location", proc.stderr)

    def test_dry_run_changes_nothing(self):
        proc, ws = run_pipeline("dry", "clean", ["--dry-run"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("stage7-revise_report", proc.stdout)
        self.assertFalse(ws.exists())


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.base = TMP / self.id().split(".")[-1]
        shutil.rmtree(self.base, ignore_errors=True)
        self.base.mkdir(parents=True)
        self.ws = self.base / "_workspace"

    def intake(self, doc):
        inp = self.base / "input.json"
        inp.write_text(json.dumps(doc))
        return atam.main(["--workspace", str(self.ws), "intake", "--input", str(inp), "--run-id", "T"])

    def test_intake_refuses_reference_outputs(self):
        self.assertEqual(self.intake(fixture.evaluation_input(with_ground_truth=True)), 2)
        self.assertFalse((self.ws / atam.F00).exists())

    def test_stage_order_is_enforced(self):
        self.assertEqual(self.intake(fixture.evaluation_input()), 0)
        self.assertEqual(atam.main(["--workspace", str(self.ws), "stage", "begin", "stage2-build_utility_tree"]), 1)
        self.assertEqual(atam.main(["--workspace", str(self.ws), "stage", "begin", "stage1-establish_context"]), 0)
        self.assertEqual(atam.main(["--workspace", str(self.ws), "stage", "begin", "stage7-revise_report"]), 1)

    def test_finalize_refuses_outside_stage7(self):
        self.assertEqual(self.intake(fixture.evaluation_input()), 0)
        self.assertEqual(atam.main(["--workspace", str(self.ws), "finalize"]), 1)

    def test_source_ref_resolution(self):
        doc = fixture.evaluation_input()["ATAM_Evaluation"]
        self.assertEqual(atam.resolve_ref(doc, "evaluation_inputs.raw_candidate_scenarios[1].id"), "RS-02")
        with self.assertRaises(KeyError):
            atam.resolve_ref(doc, "evaluation_inputs.raw_candidate_scenarios[9]")
        self.assertEqual(atam.resolve_ref({"evaluation_inputs": {"a.b": 1}}, 'evaluation_inputs["a.b"]'), 1)

    def test_suffix_format(self):
        self.assertTrue(atam.SUFFIX_RE.search("x (evidence: AE-1, AE-2; basis: observed)"))
        self.assertFalse(atam.SUFFIX_RE.search("x (evidence: AE-1, G-4-1; basis: observed)"))
        self.assertFalse(atam.SUFFIX_RE.search("x (evidence: AE-1,AE-2; basis: observed)"))
        self.assertFalse(atam.SUFFIX_RE.search("x (evidence: AE-1; basis: assumption)"))


if __name__ == "__main__":
    unittest.main()
