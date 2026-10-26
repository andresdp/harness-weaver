"""Structural test fixture for the harness self-tests.

This is NOT case data: every statement is a labelled placeholder whose only purpose is to exercise the
artifact contracts, gates, projection, checks and finalize. Never use it as evaluation input.
"""
import copy

PH = "Placeholder (contract test only): "


def evaluation_input(with_ground_truth=False):
    doc = {"ATAM_Evaluation": {
        "title": "ATAM Evaluation — CONTRACT-TEST-0001",
        "metadata": {"system_name": "Placeholder System", "phase_1_attendees": [], "phase_2_attendees": []},
        "evaluation_inputs": {
            "system_description": PH + "component A forwards requests to component B.",
            "phase_2_architectural_context": {
                "hardware_view_description": [PH + "component A sends messages to component B over a message queue."],
                "runtime_constraints": [PH + "components run on separate hosts."]},
            "raw_candidate_scenarios": [
                {"id": "RS-01", "description": PH + "component B becomes unavailable during normal operation."},
                {"id": "RS-02", "description": PH + "request volume increases."}],
            "business_context": {
                "business_goals": [PH + "keep accepting requests when a component fails."],
                "technical_constraints": [],
                "architectural_drivers": ["Availability", "Performance"]}}}}
    if with_ground_truth:
        doc["ATAM_Evaluation"]["ground_truth_outputs"] = {"risks": []}
    return doc


def gap(stage, n, scenario=None, activity="build-utility-tree"):
    return {"id": f"G-{stage}-{n}", "gap_type": "unknown",
            "description": PH + (f"no response measure is supplied for scenario {scenario}." if scenario
                                 else "stakeholder priorities are not supplied."),
            "affected_activity": activity,
            "missing_evidence": "A response measure or stakeholder priority statement.",
            "resolution_question": "Which measure or priority applies?"}


def context():
    status = {"value": "partial", "evidence": ["The inputs contain a system description and two raw scenarios."]}
    return {
        "system_scope": {"summary": PH + "A forwards requests to B.", "basis": "observed",
                         "source_refs": ["evaluation_inputs.system_description"]},
        "business_drivers": [
            {"id": "BD-1", "statement": PH + "keep accepting requests when a component fails.",
             "kind": "business_goal", "basis": "observed",
             "source_refs": ["evaluation_inputs.business_context.business_goals[0]"]}],
        "architecture_evidence": [
            {"id": "AE-1", "statement": PH + "A sends messages to B over a message queue.", "kind": "connector",
             "basis": "observed",
             "source_refs": ["evaluation_inputs.phase_2_architectural_context.hardware_view_description[0]"]},
            {"id": "AE-2", "statement": PH + "components run on separate hosts.", "kind": "deployment",
             "basis": "observed",
             "source_refs": ["evaluation_inputs.phase_2_architectural_context.runtime_constraints[0]"]}],
        "open_questions": [],
        "context_status": status, "driver_status": copy.deepcopy(status),
        "architecture_evidence_status": copy.deepcopy(status),
        "gaps": [gap(1, 1, activity="establish-context")]}


def _scenario(sid, rs, qa_ref):
    return {"scenario_id": sid, "refinement": PH + qa_ref,
            "scenario_description": PH + f"scenario {sid}; response measure unspecified in the inputs.",
            "scenario_type": "Use Case",
            "origin": {"kind": "raw_candidate_scenario", "source_scenario_id": rs, "basis": "observed",
                       "source_refs": [f"evaluation_inputs.raw_candidate_scenarios[{int(rs[-1]) - 1}]"]},
            "stimulus": PH + "stimulus", "environment": PH + "normal operation", "response": PH + "response",
            "response_measure": {"value": None, "basis": "unspecified", "source_refs": []},
            "priority_tuple": None, "driver_ids": ["BD-1"], "evidence_ids": ["AE-1"]}


def utility_tree():
    return {"root": "Utility", "quality_attribute_nodes": [
        {"attribute_name": "Availability", "driver_ids": ["BD-1"], "children": [_scenario("AV1", "RS-01", "failover")]},
        {"attribute_name": "Performance", "driver_ids": [], "children": [_scenario("PF1", "RS-02", "load")]}],
        "gaps": [gap(2, 1, "AV1"), gap(2, 2, "PF1")]}


def approaches():
    return {"approaches": [{
        "id": "AP-1", "approach_name": "Message queue between A and B",
        "description": PH + "asynchronous messaging decouples A from B.", "basis": "observed",
        "inference_note": None, "evidence_ids": ["AE-1"],
        "addressed_attributes": [{"quality_attribute": "Availability",
                                  "rationale": PH + "A can enqueue while B is down.", "basis": "inferred",
                                  "evidence_ids": ["AE-1"]}]}], "gaps": []}


def analysis(variant="clean"):
    tree = utility_tree()
    sc = {c["scenario_id"]: c for n in tree["quality_attribute_nodes"] for c in n["children"]}

    def rec(rid, sid, qa, risk):
        return {"record_id": rid, "scenario_id": sid, "approach_ids": ["AP-1"], "evidence_ids": ["AE-1"],
                "scenario_reference": {"id": sid, "text": sc[sid]["scenario_description"], "type": "Use Case"},
                "quality_attribute": qa, "environment": PH + "normal operation", "stimulus": PH + "stimulus",
                "response_measure": "unspecified: no response measure supplied",
                "architectural_decisions": [PH + "A sends messages to B over a queue (evidence: AE-1)"],
                "reasoning": PH + "the queue buffers messages; attainment cannot be determined without a measure.",
                "findings": {"risks": [risk], "non_risks": [],
                             "sensitivity_points": [{"id": f"S-{rid[-1]}", "parameter": "queue capacity",
                                                     "correlated_attribute": qa, "evidence_ids": ["AE-1"]}],
                             "tradeoff_points": []}}
    r1 = {"id": "R-1", "description": PH + "queue retention while B is down is not described.",
          "rationale": PH + "the supplied material does not establish message retention.",
          "basis": "observed" if variant == "absence_observed" else "inferred", "evidence_ids": ["AE-1"]}
    r2 = {"id": "R-2", "description": (PH + "the queue will not handle the load at peak volume."
                                       if variant == "perf_claim" else
                                       PH + "queue behaviour under increased volume is uncertain."),
          "rationale": PH + "no workload or response-time target is supplied, so attainment cannot be determined.",
          "basis": "inferred", "evidence_ids": ["AE-1", "AP-1"]}
    if variant == "gap_in_measure":
        r2 = dict(r2)
    out = {"analysis_records": [rec("AR-1", "AV1", "Availability", r1), rec("AR-2", "PF1", "Performance", r2)],
           "unanalyzed_scenarios": [],
           "scenario_analysis_status": {"value": "partial", "evidence": ["Both utility-tree scenarios analyzed; no architect review recorded."]},
           "gaps": [gap(4, 1, "PF1", activity="analyze-scenarios")]}
    if variant == "gap_in_measure":
        out["analysis_records"][1]["response_measure"] = "unspecified (see gap G-2-2)"
    return out
