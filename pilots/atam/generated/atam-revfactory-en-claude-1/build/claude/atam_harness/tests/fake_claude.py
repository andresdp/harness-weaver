#!/usr/bin/env python3
"""Stand-in for `claude -p --agent <name>` used by the self-tests to drive run.py end to end.

It writes the placeholder fixture artifacts a well-behaved stage agent would write, so the tests exercise
the real ledger, gates, projection, checks and finalize. FAKE_SCENARIO selects the behaviour.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import atam  # noqa: E402
import fixture  # noqa: E402

agent = sys.argv[sys.argv.index("--agent") + 1]
ws = atam.DEFAULT_WS
scenario = os.environ.get("FAKE_SCENARIO", "clean")
calls = ws / ".runtime" / "fake_calls.txt"
calls.parent.mkdir(parents=True, exist_ok=True)
with calls.open("a") as fh:
    fh.write(agent + "\n")


def write(name, obj):
    atam.dump_json(ws / name, obj)


if agent == "atam-context-analyst":
    write(atam.F01, fixture.context())
    if scenario == "stray_write":
        (ws / "notes.txt").write_text("scratch")
elif agent == "atam-utility-tree-builder":
    write(atam.F02, fixture.utility_tree())
elif agent == "atam-approach-analyst":
    write(atam.F03, fixture.approaches())
elif agent == "atam-scenario-analyst":
    write(atam.F04, fixture.analysis(scenario))
elif agent == "atam-report-synthesizer":
    atam.main(["--workspace", str(ws), "project-draft"])
    if scenario == "edit_draft":
        d = atam.load_json(ws / atam.F05D)
        d["ATAM_Evaluation"]["evaluation_results"]["analysis_records"][0]["reasoning"] += " Extra claim."
        write(atam.F05D, d)
elif agent == "atam-evaluation-checker":
    report = atam.load_json(ws / atam.F05D)
    checks = atam.run_checks(ws, report, "initial")
    reviewer = {"check_id": "EVID-R1", "category": "evidence_traceability", "source": "reviewer",
                "result": "pass", "location": "", "finding": "Findings trace to cited evidence.", "correction": None}
    if scenario == "reviewer_cheat":
        reviewer = {"check_id": "UNC-R1", "category": "uncertainty", "source": "reviewer", "result": "warn",
                    "location": "/ATAM_Evaluation/evaluation_results/analysis_records/1/findings/risks/0/description",
                    "finding": "Wording overstates certainty.", "correction": "Qualify the wording."}
    checks.append(reviewer)
    write(atam.F06I, {"review_stage": "initial", "run_id": atam.load_ledger(ws)["run_id"],
                      "reviewed_report": atam.F05D, "checks": checks,
                      "summary": {r: sum(c["result"] == r for c in checks) for r in ("pass", "warn", "fail")}})
elif agent == "atam-report-reviser":
    atam.main(["--workspace", str(ws), "start-final"])
    final = atam.load_json(ws / atam.F05)
    initial = atam.load_json(ws / atam.F06I)
    if scenario == "absence_observed":
        risk = final["ATAM_Evaluation"]["evaluation_results"]["analysis_records"][0]["findings"]["risks"][0]
        risk["rationale"] = risk["rationale"].replace("basis: observed)", "basis: inferred)")
        write(atam.F05, final)
    reviewer = []
    for c in initial["checks"]:
        if c["source"] == "reviewer":
            c = dict(c)
            if c["result"] != "pass":
                c["result"], c["resolution"] = "pass", "Claimed fixed."  # only the cheat scenario gets here
            reviewer.append(c)
    write(atam.F06, {"review_stage": "final", "run_id": initial["run_id"], "reviewed_report": atam.F05,
                     "checks": reviewer, "summary": {"pass": 0, "warn": 0, "fail": 0},
                     "ready_for_architect_review": True})  # deliberately wrong; finalize must overwrite it
    atam.main(["--workspace", str(ws), "finalize"])
print(json.dumps({"type": "result", "is_error": False, "result": f"fake {agent} done"}))
