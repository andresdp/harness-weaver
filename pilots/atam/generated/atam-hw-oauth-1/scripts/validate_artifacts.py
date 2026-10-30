#!/usr/bin/env python3
"""Deterministic checks for the ATAM evaluation harness artifacts.

Usage:
  validate_artifacts.py prepare-input RAW_JSON WORKSPACE   # normalize the case input into 00_evaluation_inputs.json
  validate_artifacts.py check WORKSPACE [--stage N]        # check artifacts 00..N; N=6 includes 06_review_findings.json (default 6)
Options:
  --contracts DIR   directory holding the *.schema.json contracts (default: ../references/contracts next to this
                    script, else ../contracts)
  --json            print the result as JSON

Exit codes: 0 = no failures (warnings allowed), 1 = failures, 2 = usage or missing file,
3 = reference-boundary violation in the input (ground_truth_outputs or evaluation_results present).

Verification ids printed with each finding refer to the HarnessSpec (V1..V8). Standard library only; uses the
`jsonschema` package for schema validation when it is installed.
"""
import argparse
import json
import pathlib
import re
import sys

ARTIFACTS = {
    0: ("00_evaluation_inputs.json", "evaluation-inputs.schema.json"),
    1: ("01_context.json", "context.schema.json"),
    2: ("02_utility_tree.json", "utility-tree.schema.json"),
    3: ("03_approaches.json", "approaches.schema.json"),
    4: ("04_analysis.json", "analysis.schema.json"),
    5: ("05_atam_report.json", "atam-report.schema.json"),
    6: ("06_review_findings.json", "review-findings.schema.json"),
}
FORBIDDEN_INPUT_KEYS = ("ground_truth_outputs", "evaluation_results")
ARCHITECT_REVIEW = "architect_review.json"


class Result:
    def __init__(self):
        self.items = []

    def fail(self, vid, where, msg):
        self.items.append({"level": "FAIL", "verification": vid, "location": where, "message": msg})

    def warn(self, vid, where, msg):
        self.items.append({"level": "WARN", "verification": vid, "location": where, "message": msg})

    @property
    def failed(self):
        return any(i["level"] == "FAIL" for i in self.items)


# --------------------------------------------------------------------------- schema validation
def _type_ok(value, t):
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "null": value is None,
    }[t]


def _mini_validate(value, schema, root, path, errors):
    """Validate the JSON Schema subset the harness contracts use."""
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        return _mini_validate(value, root["$defs"][name], root, path, errors)
    if "anyOf" in schema:
        if not any(not _collect(value, s, root, path) for s in schema["anyOf"]):
            errors.append((path, "does not match any allowed alternative"))
        return
    t = schema.get("type")
    if t and not _type_ok(value, t):
        errors.append((path, f"expected {t}, got {type(value).__name__}"))
        return
    if "const" in schema and value != schema["const"]:
        errors.append((path, f"must equal {schema['const']!r}"))
    if "enum" in schema and value not in schema["enum"]:
        errors.append((path, f"{value!r} is not one of {schema['enum']}"))
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append((path, "string is shorter than minLength"))
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append((path, f"{value!r} does not match {schema['pattern']}"))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append((path, f"needs at least {schema['minItems']} item(s)"))
        if "items" in schema:
            for i, item in enumerate(value):
                _mini_validate(item, schema["items"], root, f"{path}[{i}]", errors)
    if isinstance(value, dict):
        if len(value) < schema.get("minProperties", 0):
            errors.append((path, "object has too few properties"))
        for req in schema.get("required", []):
            if req not in value:
                errors.append((path, f"missing required property {req!r}"))
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for k, v in value.items():
            if k in props:
                _mini_validate(v, props[k], root, f"{path}.{k}", errors)
            elif extra is False:
                errors.append((path, f"unexpected property {k!r}"))
            elif isinstance(extra, dict):
                _mini_validate(v, extra, root, f"{path}.{k}", errors)


def _collect(value, schema, root, path):
    errs = []
    _mini_validate(value, schema, root, path, errs)
    return errs


def schema_errors(value, schema):
    try:
        import jsonschema  # type: ignore
        validator = jsonschema.Draft202012Validator(schema)
        return [("$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in e.absolute_path), e.message)
                for e in validator.iter_errors(value)]
    except ImportError:
        return _collect(value, schema, schema, "$")


# --------------------------------------------------------------------------- helpers
_TOKEN = re.compile(r'\.([^.\[\]]+)|\[(\d+)\]|\["([^"]+)"\]|^([^.\[\]]+)')


def resolve_path(doc, ref):
    """Resolve a JSON path such as evaluation_inputs.business_context.business_goals[0]."""
    pos, cur = 0, doc
    while pos < len(ref):
        m = _TOKEN.match(ref, pos)
        if not m or m.end() == pos:
            return False
        key = m.group(1) or m.group(3) or m.group(4)
        if m.group(2) is not None:
            idx = int(m.group(2))
            if not isinstance(cur, list) or idx >= len(cur):
                return False
            cur = cur[idx]
        else:
            if not isinstance(cur, dict) or key not in cur:
                return False
            cur = cur[key]
        pos = m.end()
    return True


def find_keys(node, names, path="$"):
    hits = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in names:
                hits.append(f"{path}.{k}")
            hits.extend(find_keys(v, names, f"{path}.{k}"))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            hits.extend(find_keys(v, names, f"{path}[{i}]"))
    return hits


def norm(text):
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def load(path, res, vid="V2"):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        res.fail(vid, path.name, f"invalid JSON: {exc}")
        return None


def contracts_dir(arg):
    if arg:
        return pathlib.Path(arg)
    here = pathlib.Path(__file__).resolve().parent
    for cand in (here.parent / "references" / "contracts", here.parent / "contracts"):
        if cand.is_dir():
            return cand
    return here.parent / "contracts"


# --------------------------------------------------------------------------- prepare-input
def prepare_input(raw_path, workspace, cdir):
    raw = json.loads(pathlib.Path(raw_path).read_text(encoding="utf-8"))
    hits = find_keys(raw, FORBIDDEN_INPUT_KEYS)
    if hits:
        print("REFERENCE BOUNDARY VIOLATION [V1]: the input contains evaluator-only or generated results at "
              + ", ".join(hits) + ". Supply an input-only copy (evaluation_inputs and optional metadata).")
        return 3
    body = raw.get("ATAM_Evaluation", raw) if isinstance(raw, dict) else raw
    if not isinstance(body, dict) or "evaluation_inputs" not in body:
        print("INPUT ERROR: expected an object with 'evaluation_inputs' (optionally wrapped in 'ATAM_Evaluation').")
        return 2
    out = {k: body[k] for k in ("title", "metadata", "evaluation_inputs") if k in body}
    dropped = sorted(set(body) - set(out))
    errs = schema_errors(out, json.loads((cdir / ARTIFACTS[0][1]).read_text()))
    if errs:
        for p, m in errs:
            print(f"FAIL [V2] 00_evaluation_inputs.json {p}: {m}")
        return 1
    ws = pathlib.Path(workspace)
    ws.mkdir(parents=True, exist_ok=True)
    (ws / ARTIFACTS[0][0]).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {ws / ARTIFACTS[0][0]}" + (f"; ignored top-level keys: {dropped}" if dropped else ""))
    return 0


# --------------------------------------------------------------------------- check
def check(workspace, max_stage, cdir):
    ws = pathlib.Path(workspace)
    res = Result()
    docs = {}
    for n, (fname, sname) in ARTIFACTS.items():
        if n > max_stage:
            continue
        doc = load(ws / fname, res)
        if doc is None:
            if not (ws / fname).exists():
                res.fail("V2", fname, "artifact is missing")
            continue
        docs[n] = doc
        for p, m in schema_errors(doc, json.loads((cdir / sname).read_text())):
            res.fail("V4" if n == 5 else "V2", f"{fname} {p}", m)
        if n > 0:
            for hit in find_keys(doc, ("ground_truth_outputs",)):
                res.fail("V1", f"{fname} {hit}", "evaluator-only reference key present")
    if 0 in docs:
        for hit in find_keys(docs[0], FORBIDDEN_INPUT_KEYS):
            res.fail("V1", f"00_evaluation_inputs.json {hit}", "reference-boundary violation in input")
    inputs = docs.get(0, {})
    review_record = (ws / ARCHITECT_REVIEW).exists()

    def check_refs(fname, where, item):
        refs = item.get("source_refs", []) or []
        if item.get("basis") == "observed" and not refs:
            res.fail("V3", f"{fname} {where}", "observed item cites no source_refs")
        for r in refs:
            if not resolve_path(inputs, r):
                res.fail("V3", f"{fname} {where}", f"source_ref {r!r} does not resolve in 00_evaluation_inputs.json")

    gaps_by_stage = {}
    ids = {"BD": set(), "AE": set(), "AP": set(), "SC": set(), "Q": set()}

    c = docs.get(1)
    if isinstance(c, dict):
        gaps_by_stage[1] = c.get("gaps", [])
        check_refs(ARTIFACTS[1][0], "system_scope", c.get("system_scope", {}))
        for key, prefix in (("business_drivers", "BD"), ("architecture_evidence", "AE"), ("open_questions", "Q")):
            for i, it in enumerate(c.get(key, [])):
                if it.get("id") in ids[prefix]:
                    res.fail("V3", f"01_context.json {key}[{i}]", f"duplicate id {it.get('id')}")
                ids[prefix].add(it.get("id"))
                check_refs(ARTIFACTS[1][0], f"{key}[{i}]", it)
        for st in ("context_status", "driver_status", "architecture_evidence_status"):
            v = (c.get(st) or {}).get("value")
            if v in ("missing", "partial") and not c.get("gaps"):
                res.warn("V7", f"01_context.json {st}", f"status is {v} but no gap is recorded")

    u = docs.get(2)
    utility_text = {}
    if isinstance(u, dict):
        gaps_by_stage[2] = u.get("gaps", [])
        raw_ids_used = set()
        for ni, node in enumerate(u.get("quality_attribute_nodes", [])):
            for d in node.get("driver_ids", []):
                if d not in ids["BD"]:
                    res.fail("V3", f"02_utility_tree.json quality_attribute_nodes[{ni}].driver_ids", f"{d} not in 01_context.json")
            for ci, ch in enumerate(node.get("children", [])):
                where = f"quality_attribute_nodes[{ni}].children[{ci}]"
                sid = ch.get("scenario_id")
                if sid in ids["SC"]:
                    res.fail("V3", f"02_utility_tree.json {where}", f"duplicate scenario_id {sid}")
                ids["SC"].add(sid)
                utility_text[sid] = ch.get("scenario_description")
                check_refs(ARTIFACTS[2][0], where, ch)
                if ch.get("raw_scenario_id"):
                    raw_ids_used.add(ch["raw_scenario_id"])
                if (ch.get("priority_tuple") is None) != (ch.get("priority_basis") is None):
                    res.fail("V6", f"02_utility_tree.json {where}", "priority_tuple and priority_basis must both be set or both be null")
                if ch.get("response_measure") is None and ch.get("response_measure_basis") != "missing":
                    res.fail("V6", f"02_utility_tree.json {where}", "null response_measure requires response_measure_basis 'missing'")
                if ch.get("response_measure") is None or ch.get("priority_tuple") is None:
                    if not any(g.get("affected_activity") == "build-utility-tree" for g in u.get("gaps", [])):
                        res.fail("V7", f"02_utility_tree.json {where}", "null response measure or priority without a build-utility-tree gap")
        order = u.get("analysis_order", [])
        for sid in order:
            if sid not in ids["SC"]:
                res.fail("V8", "02_utility_tree.json analysis_order", f"{sid} is not a scenario in the tree")
        for sid in ids["SC"] - set(order):
            res.fail("V8", "02_utility_tree.json analysis_order", f"scenario {sid} is missing from analysis_order")
        for i, sc in enumerate(u.get("scenarios", [])):
            if sc.get("scenario_id") not in ids["SC"]:
                res.fail("V3", f"02_utility_tree.json scenarios[{i}]", f"{sc.get('scenario_id')} is not in the tree")
        raw = (inputs.get("evaluation_inputs") or {}).get("raw_candidate_scenarios") or []
        gap_text = " ".join(norm(g.get("description", "")) for g in u.get("gaps", []))
        for rs in raw:
            rid = rs.get("id") if isinstance(rs, dict) else None
            if rid and rid not in raw_ids_used and norm(rid) not in gap_text:
                res.warn("V8", "02_utility_tree.json", f"raw candidate scenario {rid} is neither refined nor explained in a gap")

    a = docs.get(3)
    if isinstance(a, dict):
        gaps_by_stage[3] = a.get("gaps", [])
        for i, ap in enumerate(a.get("approaches", [])):
            if ap.get("id") in ids["AP"]:
                res.fail("V3", f"03_approaches.json approaches[{i}]", f"duplicate id {ap.get('id')}")
            ids["AP"].add(ap.get("id"))
            for e in ap.get("evidence_ids", []):
                if e not in ids["AE"]:
                    res.fail("V3", f"03_approaches.json approaches[{i}].evidence_ids", f"{e} not in 01_context.json")
            if ap.get("basis") == "inferred" and not ap.get("inference_note"):
                res.fail("V6", f"03_approaches.json approaches[{i}]", "inferred approach without inference_note")

    raw_text = {}
    for rs in (inputs.get("evaluation_inputs") or {}).get("raw_candidate_scenarios") or []:
        if isinstance(rs, dict) and rs.get("id"):
            raw_text[rs["id"]] = rs.get("description")

    an = docs.get(4)
    finding_ids_04 = set()
    if isinstance(an, dict):
        gaps_by_stage[4] = an.get("gaps", [])
        known = ids["BD"] | ids["AE"] | ids["AP"] | ids["SC"] | ids["Q"]
        covered = set()
        for i, rec in enumerate(an.get("analysis_records", [])):
            where = f"04_analysis.json analysis_records[{i}]"
            sid = rec.get("scenario_id")
            covered.add(sid)
            if ids["SC"] and sid not in ids["SC"]:
                res.fail("V3", where, f"scenario_id {sid} not in 02_utility_tree.json")
            ref = rec.get("scenario_reference", {})
            if ref.get("id") != sid:
                res.fail("V8", where, "scenario_reference.id must equal scenario_id")
            if norm(ref.get("text", "")) not in (norm(utility_text.get(sid, "")), norm(raw_text.get(sid, "") or "")):
                res.fail("V8", where, "scenario_reference.text is not the verbatim scenario text from 02_utility_tree.json")
            for ap in rec.get("approach_ids", []):
                if ap not in ids["AP"]:
                    res.fail("V3", where, f"approach {ap} not in 03_approaches.json")
            for e in rec.get("evidence_ids", []):
                if e not in ids["AE"]:
                    res.fail("V3", where, f"evidence {e} not in 01_context.json")
            for kind, items in (rec.get("findings") or {}).items():
                for j, f in enumerate(items):
                    fid = f.get("id")
                    if fid in finding_ids_04:
                        res.fail("V3", f"{where}.findings.{kind}[{j}]", f"duplicate finding id {fid}")
                    finding_ids_04.add(fid)
                    for e in f.get("evidence_ids", []):
                        if e not in known and not resolve_path(inputs, e):
                            res.fail("V3", f"{where}.findings.{kind}[{j}]", f"evidence {e!r} resolves to no id or input path")
        for un in an.get("unanalyzed_scenarios", []):
            covered.add(un.get("scenario_id"))
        if isinstance(u, dict):
            for sid in u.get("analysis_order", []):
                if sid not in covered:
                    res.fail("V8", "04_analysis.json", f"scenario {sid} is neither analyzed nor listed as unanalyzed")

    rep = docs.get(5)
    if isinstance(rep, dict) and isinstance(rep.get("ATAM_Evaluation"), dict):
        body = rep["ATAM_Evaluation"]
        if 0 in docs and body.get("evaluation_inputs") != inputs.get("evaluation_inputs"):
            res.fail("V4", "05_atam_report.json ATAM_Evaluation.evaluation_inputs", "differs from the supplied evaluation_inputs")
        results = body.get("evaluation_results") or {}
        sem = results.get("semantic_state") or {}
        for st in ("context_status", "driver_status", "architecture_evidence_status", "scenario_analysis_status", "report_status"):
            ev = (sem.get(st) or {}).get("evidence") or []
            if any(not str(e).strip() for e in ev):
                res.fail("V5", f"05_atam_report.json semantic_state.{st}", "empty evidence entry")
        if (sem.get("report_status") or {}).get("value") == "reviewed" and not review_record:
            res.fail("V5", "05_atam_report.json semantic_state.report_status", f"'reviewed' without {ARCHITECT_REVIEW}")
        if (sem.get("scenario_analysis_status") or {}).get("value") == "reviewed" and not review_record:
            res.fail("V5", "05_atam_report.json semantic_state.scenario_analysis_status", f"'reviewed' without {ARCHITECT_REVIEW}")
        if (sem.get("report_status") or {}).get("value") == "not_started":
            res.fail("V5", "05_atam_report.json semantic_state.report_status", "a written report cannot be not_started")
        report_gaps = " || ".join(norm(g.get("description", "")) for g in sem.get("gaps", []))
        for stage, gaps in gaps_by_stage.items():
            for g in gaps:
                if norm(g.get("description", "")) not in report_gaps:
                    res.fail("V7", "05_atam_report.json semantic_state.gaps",
                             f"gap {g.get('id')} from stage {stage} is not carried into the report")
        tree_ids = {ch.get("scenario_id") for n in (results.get("utility_tree") or {}).get("quality_attribute_nodes", [])
                    for ch in n.get("children", [])}
        rep_findings = set()
        for i, rec in enumerate(results.get("analysis_records", [])):
            rid = (rec.get("scenario_reference") or {}).get("id")
            if rid not in tree_ids and rid not in raw_text:
                res.fail("V8", f"05_atam_report.json analysis_records[{i}]", f"scenario {rid} is not in the utility tree or raw scenarios")
            for items in (rec.get("findings") or {}).values():
                rep_findings |= {f.get("id") for f in items}
        if isinstance(an, dict):
            if len(results.get("analysis_records", [])) != len(an.get("analysis_records", [])):
                res.fail("V8", "05_atam_report.json analysis_records", "record count differs from 04_analysis.json")
            if rep_findings != finding_ids_04:
                res.fail("V6", "05_atam_report.json analysis_records", "finding ids differ from 04_analysis.json: "
                         f"missing {sorted(finding_ids_04 - rep_findings)}, added {sorted(rep_findings - finding_ids_04)}")

    rv = docs.get(6)
    if isinstance(rv, dict) and rv.get("ready_for_architect_review"):
        blocking = {"structure", "semantic_state", "evidence_traceability", "reference_boundary"}
        failing = {ck.get("id") for ck in rv.get("checks", []) if ck.get("result") == "fail" and ck.get("category") in blocking}
        remaining = set((rv.get("revision") or {}).get("remaining_failures", []))
        if failing & remaining or (failing and not (rv.get("revision") or {}).get("applied")):
            res.fail("V6", "06_review_findings.json ready_for_architect_review",
                     f"true while blocking checks remain failed: {sorted(failing & remaining or failing)}")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("prepare-input")
    p1.add_argument("raw")
    p1.add_argument("workspace")
    p2 = sub.add_parser("check")
    p2.add_argument("workspace")
    p2.add_argument("--stage", type=int, default=6, choices=range(0, 7))
    for p in (p1, p2):
        p.add_argument("--contracts")
        p.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    cdir = contracts_dir(args.contracts)
    if not cdir.is_dir():
        print(f"contracts directory not found: {cdir}")
        return 2
    if args.cmd == "prepare-input":
        try:
            return prepare_input(args.raw, args.workspace, cdir)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"INPUT ERROR: {exc}")
            return 2
    res = check(args.workspace, args.stage, cdir)
    if args.json:
        print(json.dumps({"failed": res.failed, "findings": res.items}, indent=2))
    else:
        for i in res.items:
            print(f"{i['level']} [{i['verification']}] {i['location']}: {i['message']}")
        n_f = sum(i["level"] == "FAIL" for i in res.items)
        print(f"summary: {n_f} failure(s), {len(res.items) - n_f} warning(s) (checked up to stage {args.stage})")
    return 1 if res.failed else 0


if __name__ == "__main__":
    sys.exit(main())
