#!/usr/bin/env python3
"""Deterministic runtime for the ATAM evaluation harness.

Owns everything that must give the same answer on every run:
  - stage0 intake (with the reference-boundary check),
  - the run ledger that orders stage0..stage7 and records each stage's outputs,
  - per-stage gates (schema + cross-artifact + write-scope checks),
  - projection of the validated artifacts into the stage-5 report draft,
  - the automated review checks used by stages 6 and 7,
  - stage-7 finalize, the only place ready_for_architect_review is computed.

Run from the bundle root:  python3 atam_harness/atam.py <command> [...]
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - environment problem, not a harness result
    sys.exit("atam.py: the 'jsonschema' package is required (pip install jsonschema)")

HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parent
CONTRACTS = ROOT / ".claude" / "skills" / "evaluate-architecture" / "references"
SCHEMAS = HARNESS_DIR / "schemas"
# ATAM_WORKSPACE exists for the harness self-tests; normal runs use <bundle>/_workspace.
DEFAULT_WS = Path(os.environ["ATAM_WORKSPACE"]).resolve() if os.environ.get("ATAM_WORKSPACE") else ROOT / "_workspace"
LEDGER = "run_ledger.json"
RUNTIME = ".runtime"

ACTIVITIES = ["establish-context", "build-utility-tree", "identify-approaches",
              "analyze-scenarios", "synthesize-and-review"]
CATEGORIES = ["structure", "semantic_state", "evidence_traceability",
              "uncertainty", "method_coverage", "reference_boundary"]
# Every category blocks readiness (check-evaluation skill, "Evidence and readiness rules").
BLOCKING_CATEGORIES = list(CATEGORIES)
CHECK_PREFIX = {"STRUCT": "structure", "SEM": "semantic_state", "EVID": "evidence_traceability",
                "UNC": "uncertainty", "COV": "method_coverage", "REF": "reference_boundary"}

F00, F01, F02, F03, F04 = ("00_evaluation_inputs.json", "01_context.json", "02_utility_tree.json",
                          "03_approaches.json", "04_analysis.json")
F05D, F06I, F05, F06 = ("05_atam_report_draft.json", "06_review_findings_initial.json",
                        "05_atam_report.json", "06_review_findings.json")

STAGES = [
    {"id": "stage0-intake", "agent": None, "skill": None, "activity": "establish-context",
     "reads": [], "writes": [F00]},
    {"id": "stage1-establish_context", "agent": "atam-context-analyst", "skill": "evaluate-architecture",
     "activity": "establish-context", "reads": [F00], "writes": [F01]},
    {"id": "stage2-build_utility_tree", "agent": "atam-utility-tree-builder", "skill": "evaluate-architecture",
     "activity": "build-utility-tree", "reads": [F00, F01], "writes": [F02]},
    {"id": "stage3-identify_approaches", "agent": "atam-approach-analyst", "skill": "evaluate-architecture",
     "activity": "identify-approaches", "reads": [F00, F01, F02], "writes": [F03]},
    {"id": "stage4-analyze_scenarios", "agent": "atam-scenario-analyst", "skill": "evaluate-architecture",
     "activity": "analyze-scenarios", "reads": [F00, F01, F02, F03], "writes": [F04]},
    {"id": "stage5-synthesize_report", "agent": "atam-report-synthesizer", "skill": "evaluate-architecture",
     "activity": "synthesize-and-review", "reads": [F00, F01, F02, F03, F04], "writes": [F05D]},
    {"id": "stage6-check_evaluation", "agent": "atam-evaluation-checker", "skill": "check-evaluation",
     "activity": "synthesize-and-review", "reads": [F00, F01, F02, F03, F04, F05D], "writes": [F06I]},
    {"id": "stage7-revise_report", "agent": "atam-report-reviser", "skill": "revise-report",
     "activity": "synthesize-and-review", "reads": [F00, F01, F02, F03, F04, F05D, F06I], "writes": [F05, F06]},
]
STAGE_IDS = [s["id"] for s in STAGES]
STAGE_BY_ID = {s["id"]: s for s in STAGES}

GAP_ID_RE = re.compile(r"\bG-\d+(?:-\d+)*\b")
SUFFIX_RE = re.compile(r" \(evidence: ((?:AE|AP|BD)-\d+(?:, (?:AE|AP|BD)-\d+)*); basis: (observed|inferred)\)$")
ANY_SUFFIX_RE = re.compile(r"\s*\(evidence:[^()]*\)\s*$")
CITE_RE = re.compile(r"\(evidence: (AE-\d+(?:, AE-\d+)*)\)")
ID_RE = re.compile(r"\b(?:AE|AP|BD)-\d+\b")
ABSENCE_RE = re.compile(
    r"\b(not (?:described|documented|specified|stated|mentioned|provided|addressed|defined|given|identified)"
    r"|no (?:mention|description|evidence|information|documentation|specification|indication)"
    r"|(?:is|are) (?:absent|missing|undocumented|unspecified)"
    r"|lacks?|lacking|absence of"
    r"|does not (?:describe|specify|mention|document|state|address|define)"
    r"|do not (?:describe|specify|mention|document|state|address|define))\b", re.I)
PERF_QA_RE = re.compile(r"perform|latenc|throughput|response.?time|timeliness|real.?time", re.I)
ATTAIN_RE = re.compile(
    r"\b(meets?|met|satisf(?:y|ies|ied)|achiev(?:e|es|ed)|violat(?:e|es|ed|ion|ions)|exceed(?:s|ed)?"
    r"|breach(?:es|ed)?|miss(?:es|ed)|falls? short|within (?:the )?(?:target|budget|threshold|limit)"
    r"|adequate(?:ly)?|insufficient|sufficient(?:ly)?|will (?:not )?(?:handle|sustain|cope with))\b", re.I)
UNCERTAIN_RE = re.compile(
    r"(cannot|can't|could not|not possible to|unable to|impossible to)\s+(?:be\s+)?"
    r"(?:determine|determined|establish|established|assess|assessed|verify|verified|confirm|confirmed|judge|judged)"
    r"|undetermined|indeterminate|unknown whether|whether|not established|no basis to", re.I)


# ----------------------------------------------------------------------------- utilities

def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ptr(path) -> str:
    return "".join("/" + str(p).replace("~", "~0").replace("/", "~1") for p in path)


def walk_strings(obj, path=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, path + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, path + (i,))
    elif isinstance(obj, str):
        yield path, obj


def walk_keys(obj, path=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path + (k,), k
            yield from walk_keys(v, path + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, path + (i,))


_schema_cache: dict = {}


def schema_errors(instance, schema_path: Path, label: str) -> list[str]:
    if schema_path not in _schema_cache:
        _schema_cache[schema_path] = jsonschema.Draft202012Validator(load_json(schema_path))
    validator = _schema_cache[schema_path]
    errs = sorted(validator.iter_errors(instance), key=lambda e: [str(p) for p in e.absolute_path])
    return [f"{label}: {ptr(e.absolute_path) or '<root>'}: {e.message}" for e in errs]


_TOKEN = re.compile(r"""\.?([^.\[\]]+)|\[(\d+)\]|\["((?:[^"\\]|\\.)*)"\]""")


def resolve_ref(doc, ref: str):
    """Resolve a source_ref such as evaluation_inputs.a.b[0]["k.x"] in 00_evaluation_inputs.json."""
    pos, cur, first = 0, doc, True
    while pos < len(ref):
        m = _TOKEN.match(ref, pos)
        if not m or m.end() == pos or (first and ref[pos] == "."):
            raise KeyError(f"cannot parse at offset {pos}")
        name, index, quoted = m.groups()
        if index is not None:
            if not isinstance(cur, list) or int(index) >= len(cur):
                raise KeyError(f"index [{index}] not found")
            cur = cur[int(index)]
        else:
            key = name if name is not None else json.loads(f'"{quoted}"')
            if not isinstance(cur, dict) or key not in cur:
                raise KeyError(f"key {key!r} not found")
            cur = cur[key]
        pos, first = m.end(), False
    return cur


def ref_errors(doc00, refs, label) -> list[str]:
    out = []
    for r in refs:
        try:
            resolve_ref(doc00, r)
        except KeyError as exc:
            out.append(f"{label}: source_ref {r!r} does not resolve in {F00} ({exc})")
    return out


def gap_id_leaks(obj, label, skip_top=("gaps",)) -> list[str]:
    """G-* identifiers may appear only in gap records."""
    out = []
    for path, s in walk_strings(obj):
        if path and path[0] in skip_top:
            continue
        for m in GAP_ID_RE.finditer(s):
            out.append(f"{label}: {ptr(path)}: gap identifier {m.group(0)} outside a gap record")
    return out


def ws_path(ws) -> Path:
    return Path(ws).resolve() if ws else DEFAULT_WS


# ----------------------------------------------------------------------------- ledger

def ledger_path(ws: Path) -> Path:
    return ws / LEDGER


def load_ledger(ws: Path) -> dict:
    p = ledger_path(ws)
    if not p.exists():
        raise SystemExit(f"no run ledger at {p}; run stage0 intake first (atam.py intake --input ...)")
    return load_json(p)


def save_ledger(ws: Path, ledger: dict) -> None:
    dump_json(ledger_path(ws), ledger)


def event(ledger: dict, stage: str, kind: str, **extra) -> int:
    ledger["seq"] = ledger.get("seq", 0) + 1
    ledger.setdefault("events", []).append({"seq": ledger["seq"], "stage": stage, "event": kind,
                                            "at": now_iso(), **extra})
    return ledger["seq"]


def _excluded(rel: str) -> bool:
    return (rel == LEDGER or rel.startswith(RUNTIME + "/") or "__pycache__" in rel
            or rel.startswith("tests/_tmp") or rel.endswith("settings.local.json"))


def snapshot(ws: Path) -> dict:
    """Hash workspace files and harness files so a stage's write scope can be enforced."""
    files = {}
    for prefix, base in (("ws", ws), ("harness", HARNESS_DIR), ("claude", ROOT / ".claude")):
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file():
                rel = p.relative_to(base).as_posix()
                if not _excluded(rel):
                    files[f"{prefix}:{rel}"] = sha256(p)
    return files


def scope_errors(pre: dict, post: dict, allowed: list[str]) -> list[str]:
    allowed_keys = {f"ws:{a}" for a in allowed}
    out = []
    for key in sorted(set(pre) | set(post)):
        if pre.get(key) != post.get(key) and key not in allowed_keys:
            change = "created" if key not in pre else "deleted" if key not in post else "modified"
            out.append(f"write scope: {key} was {change}; this stage may write only {', '.join(allowed)}")
    return out


def prior_stage_errors(ws: Path, ledger: dict, stage_id: str) -> list[str]:
    out = []
    for sid in STAGE_IDS[:STAGE_IDS.index(stage_id)]:
        rec = ledger["stages"].get(sid)
        if not rec or rec.get("status") != "completed":
            out.append(f"order: {sid} must be completed before {stage_id} (status: "
                       f"{rec.get('status') if rec else 'not started'})")
            continue
        for name, digest in rec.get("outputs", {}).items():
            p = ws / name
            if not p.exists() or sha256(p) != digest:
                out.append(f"integrity: {name} changed after {sid} completed")
    return out


def cmd_stage_begin(ws: Path, stage_id: str, invocation: str, retry=False, rerun=False) -> int:
    ledger = load_ledger(ws)
    if stage_id == STAGE_IDS[0]:
        print("stage0-intake is begun and completed by `atam.py intake`", file=sys.stderr)
        return 1
    rec = ledger["stages"].get(stage_id)
    status = rec.get("status") if rec else None
    if rerun and status:
        # Re-running a stage invalidates it and every later stage; their outputs are moved aside, not deleted.
        idx = STAGE_IDS.index(stage_id)
        seq = event(ledger, stage_id, "rerun-requested")
        dest = ws / RUNTIME / "superseded" / f"seq{seq}"
        for sid in STAGE_IDS[idx:]:
            r = ledger["stages"].get(sid)
            if not r:
                continue
            for name in STAGE_BY_ID[sid]["writes"]:
                if (ws / name).exists():
                    dest.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(ws / name), str(dest / name))
            r["status"] = "invalidated"
        save_ledger(ws, ledger)
        rec, status = ledger["stages"][stage_id], "invalidated"
    errs = prior_stage_errors(ws, ledger, stage_id)
    if status == "completed":
        errs.append(f"{stage_id} is already completed; use --rerun to invalidate it and later stages")
    if status in ("started", "failed") and not retry:
        errs.append(f"{stage_id} is {status}; use --retry to continue it")
    if errs:
        print("\n".join(errs), file=sys.stderr)
        return 1
    if status in ("started", "failed"):
        rec["attempts"] += 1
        rec["status"] = "started"
        rec["begin_seq"] = event(ledger, stage_id, "retry", attempt=rec["attempts"], invocation=invocation)
    else:
        later_running = [s for s in STAGE_IDS[STAGE_IDS.index(stage_id) + 1:]
                         if ledger["stages"].get(s, {}).get("status") in ("started", "completed", "failed")]
        if later_running:
            print(f"later stages {later_running} hold state; use --rerun", file=sys.stderr)
            return 1
        rec = {"status": "started", "attempts": 1, "invocation": invocation,
               "agent": STAGE_BY_ID[stage_id]["agent"], "started_at": now_iso(),
               "pre_snapshot": snapshot(ws), "outputs": {}, "errors": []}
        ledger["stages"][stage_id] = rec
        rec["begin_seq"] = event(ledger, stage_id, "begin", invocation=invocation)
    save_ledger(ws, ledger)
    print(f"{stage_id}: started (attempt {rec['attempts']}); write only: "
          f"{', '.join(STAGE_BY_ID[stage_id]['writes'])}")
    return 0


def cmd_stage_complete(ws: Path, stage_id: str) -> int:
    ledger = load_ledger(ws)
    rec = ledger["stages"].get(stage_id)
    if not rec or rec.get("status") != "started":
        print(f"{stage_id} is not started", file=sys.stderr)
        return 1
    errs = prior_stage_errors(ws, ledger, stage_id)
    if stage_id == "stage7-revise_report" and not errs:
        errs += finalize(ws, ledger)
    errs += validate_stage(ws, stage_id)
    errs += scope_errors(rec["pre_snapshot"], snapshot(ws), STAGE_BY_ID[stage_id]["writes"])
    if errs:
        rec["status"], rec["errors"] = "failed", errs
        event(ledger, stage_id, "gate-failed", errors=len(errs))
        save_ledger(ws, ledger)
        print(f"{stage_id}: gate FAILED\n" + "\n".join(f"  - {e}" for e in errs), file=sys.stderr)
        return 1
    rec["outputs"] = {n: sha256(ws / n) for n in STAGE_BY_ID[stage_id]["writes"]}
    rec["status"], rec["errors"], rec["completed_at"] = "completed", [], now_iso()
    rec["complete_seq"] = event(ledger, stage_id, "complete")
    save_ledger(ws, ledger)
    print(f"{stage_id}: completed")
    if stage_id == "stage7-revise_report":
        final = load_json(ws / F06)
        print(f"ready_for_architect_review = {str(final['ready_for_architect_review']).lower()} "
              f"({final['readiness_basis']['blocking_findings_remaining']} blocking findings remain)")
    return 0


# ----------------------------------------------------------------------------- intake (stage 0)

def cmd_intake(ws: Path, input_path: Path, run_id: str) -> int:
    try:
        raw = load_json(input_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"intake: cannot read {input_path}: {exc}", file=sys.stderr)
        return 1
    leaks = [ptr(p) for p, k in walk_keys(raw) if k == "ground_truth_outputs"]
    if leaks:
        print("intake REFUSED: the input contains evaluation-only reference outputs "
              f"(ground_truth_outputs at {', '.join(leaks)}). Supply an input-only copy.", file=sys.stderr)
        return 2
    body = raw.get("ATAM_Evaluation", raw) if isinstance(raw, dict) else None
    if not isinstance(body, dict) or not isinstance(body.get("evaluation_inputs"), dict):
        print("intake: expected an object with evaluation_inputs (optionally wrapped in ATAM_Evaluation)",
              file=sys.stderr)
        return 1
    extra = sorted(set(body) - {"title", "metadata", "evaluation_inputs"})
    if extra:
        print(f"intake REFUSED: unexpected top-level sections {extra}; only title, metadata and "
              "evaluation_inputs are generation inputs.", file=sys.stderr)
        return 2
    doc = {k: body[k] for k in ("title", "metadata", "evaluation_inputs") if k in body}
    if ws.exists() and any(ws.iterdir()):
        prev = load_json(ledger_path(ws)).get("run_id", "previous") if ledger_path(ws).exists() else "previous"
        archive = ws.parent / f"{ws.name}_archive"
        dest = archive / prev
        n = 1
        while dest.exists():
            n += 1
            dest = archive / f"{prev}-{n}"
        archive.mkdir(parents=True, exist_ok=True)
        shutil.move(str(ws), str(dest))
        print(f"intake: archived previous workspace to {dest}")
    ws.mkdir(parents=True, exist_ok=True)
    ledger = {"run_id": run_id, "input_path": str(input_path), "input_sha256": sha256(input_path),
              "created_at": now_iso(), "seq": 0, "events": [], "stages": {}}
    rec = {"status": "started", "attempts": 1, "invocation": "deterministic", "agent": None,
           "started_at": now_iso(), "pre_snapshot": snapshot(ws), "outputs": {}, "errors": []}
    ledger["stages"]["stage0-intake"] = rec
    rec["begin_seq"] = event(ledger, "stage0-intake", "begin", invocation="deterministic")
    dump_json(ws / F00, doc)
    errs = validate_stage(ws, "stage0-intake")
    if errs:
        rec["status"], rec["errors"] = "failed", errs
        save_ledger(ws, ledger)
        print("\n".join(errs), file=sys.stderr)
        return 1
    rec["outputs"] = {F00: sha256(ws / F00)}
    rec["status"], rec["completed_at"] = "completed", now_iso()
    rec["complete_seq"] = event(ledger, "stage0-intake", "complete")
    save_ledger(ws, ledger)
    print(f"stage0-intake: completed; run_id={run_id}; workspace={ws}")
    return 0


# ----------------------------------------------------------------------------- stage gates

def _load(ws: Path, name: str, errs: list):
    p = ws / name
    if not p.exists():
        errs.append(f"{name}: missing")
        return None
    try:
        return load_json(p)
    except json.JSONDecodeError as exc:
        errs.append(f"{name}: invalid JSON ({exc})")
        return None


def _gap_list_errors(gaps, stage_num: int, label: str) -> list[str]:
    out, seen = [], set()
    for i, g in enumerate(gaps or []):
        gid = g.get("id", "")
        if not re.fullmatch(rf"G-{stage_num}-\d+", gid):
            out.append(f"{label}: /gaps/{i}/id {gid!r} must be G-{stage_num}-n (gap ids carry their stage)")
        if gid in seen:
            out.append(f"{label}: duplicate gap id {gid}")
        seen.add(gid)
    return out


def registries(ws: Path) -> dict:
    """Identifier registries from the validated upstream artifacts."""
    reg = {"AE": set(), "BD": set(), "AP": set(), "scenarios": {}}
    for name, key, field in ((F01, "AE", "architecture_evidence"), (F01, "BD", "business_drivers"),
                             (F03, "AP", "approaches")):
        p = ws / name
        if p.exists():
            try:
                reg[key] |= {x.get("id") for x in load_json(p).get(field, []) if isinstance(x, dict)}
            except (json.JSONDecodeError, AttributeError):
                pass
    p = ws / F02
    if p.exists():
        try:
            for node in load_json(p).get("quality_attribute_nodes", []):
                for ch in node.get("children", []):
                    reg["scenarios"][ch.get("scenario_id")] = {**ch, "attribute_name": node.get("attribute_name")}
        except (json.JSONDecodeError, AttributeError):
            pass
    return reg


def _id_exists_errors(ids, reg, label, allowed=("AE", "AP", "BD")) -> list[str]:
    out = []
    for i in ids:
        ns = i.split("-")[0]
        if ns not in allowed:
            out.append(f"{label}: {i} is not an allowed evidence identifier here ({'/'.join(allowed)} only)")
        elif i not in reg[ns]:
            out.append(f"{label}: {i} is not registered in {F01 if ns != 'AP' else F03}")
    return out


def validate_stage(ws: Path, stage_id: str) -> list[str]:
    errs: list[str] = []
    doc00 = _load(ws, F00, errs)
    if doc00 is None:
        return errs
    if stage_id == "stage0-intake":
        if not isinstance(doc00.get("evaluation_inputs"), dict):
            errs.append(f"{F00}: evaluation_inputs must be an object")
        errs += [f"{F00}: {ptr(p)}: evaluation-only key" for p, k in walk_keys(doc00) if k == "ground_truth_outputs"]
        return errs
    reg = registries(ws)

    if stage_id == "stage1-establish_context":
        d = _load(ws, F01, errs)
        if d is None:
            return errs
        errs += schema_errors(d, SCHEMAS / "01_context.schema.json", F01)
        if errs:
            return errs
        for field in ("business_drivers", "architecture_evidence"):
            ids = [x["id"] for x in d[field]]
            errs += [f"{F01}: duplicate id {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
            for i, x in enumerate(d[field]):
                errs += ref_errors(doc00, x["source_refs"], f"{F01}: /{field}/{i}")
        if d["system_scope"]["basis"] == "observed" and not d["system_scope"]["source_refs"]:
            errs.append(f"{F01}: /system_scope: observed basis requires source_refs")
        errs += ref_errors(doc00, d["system_scope"]["source_refs"], f"{F01}: /system_scope")
        for i, q in enumerate(d["open_questions"]):
            errs += ref_errors(doc00, q["source_refs"], f"{F01}: /open_questions/{i}")
        errs += _gap_list_errors(d["gaps"], 1, F01) + gap_id_leaks(d, F01)

    elif stage_id == "stage2-build_utility_tree":
        d = _load(ws, F02, errs)
        if d is None:
            return errs
        errs += schema_errors(d, SCHEMAS / "02_utility_tree.schema.json", F02)
        if errs:
            return errs
        raw_ids = {r.get("id") for r in (doc00["evaluation_inputs"].get("raw_candidate_scenarios") or [])
                   if isinstance(r, dict)}
        gap_text = " ".join(g["description"] + " " + g["missing_evidence"] for g in d["gaps"])
        seen = set()
        for n, node in enumerate(d["quality_attribute_nodes"]):
            errs += _id_exists_errors(node["driver_ids"], reg, f"{F02}: /quality_attribute_nodes/{n}", ("BD",))
            for c, ch in enumerate(node["children"]):
                loc = f"{F02}: /quality_attribute_nodes/{n}/children/{c}"
                sid = ch["scenario_id"]
                if sid in seen:
                    errs.append(f"{loc}: duplicate scenario_id {sid}")
                seen.add(sid)
                errs += _id_exists_errors(ch["driver_ids"], reg, loc, ("BD",))
                errs += _id_exists_errors(ch["evidence_ids"], reg, loc, ("AE",))
                o = ch["origin"]
                errs += ref_errors(doc00, o["source_refs"], f"{loc}/origin")
                if o["kind"] == "raw_candidate_scenario" and o["source_scenario_id"] not in raw_ids:
                    errs.append(f"{loc}/origin: source_scenario_id {o['source_scenario_id']!r} is not a "
                                "raw_candidate_scenarios id in the inputs")
                rm = ch["response_measure"]
                if rm["value"] is None:
                    if rm["basis"] != "unspecified":
                        errs.append(f"{loc}/response_measure: null value requires basis 'unspecified'")
                    if not re.search(rf"(?<![A-Za-z0-9_.-]){re.escape(sid)}(?![A-Za-z0-9_-])", gap_text):
                        errs.append(f"{loc}/response_measure: unspecified measure needs a G-2-n gap whose "
                                    f"description names scenario {sid}")
                else:
                    if rm["basis"] != "observed" or not rm["source_refs"]:
                        errs.append(f"{loc}/response_measure: a measure must be observed in the inputs "
                                    "(basis observed + source_refs); never fabricate a threshold")
                    errs += ref_errors(doc00, rm["source_refs"], f"{loc}/response_measure")
                if ch["priority_tuple"] is not None:
                    errs += ref_errors(doc00, ch["priority_tuple"]["source_refs"], f"{loc}/priority_tuple")
        if not seen:
            errs.append(f"{F02}: the utility tree has no scenarios")
        errs += _gap_list_errors(d["gaps"], 2, F02) + gap_id_leaks(d, F02)

    elif stage_id == "stage3-identify_approaches":
        d = _load(ws, F03, errs)
        if d is None:
            return errs
        errs += schema_errors(d, SCHEMAS / "03_approaches.schema.json", F03)
        if errs:
            return errs
        ids = [a["id"] for a in d["approaches"]]
        errs += [f"{F03}: duplicate id {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
        for i, a in enumerate(d["approaches"]):
            loc = f"{F03}: /approaches/{i}"
            errs += _id_exists_errors(a["evidence_ids"], reg, loc, ("AE",))
            if a["basis"] == "inferred" and not (a["inference_note"] or "").strip():
                errs.append(f"{loc}: inferred approach requires an inference_note")
            for j, aa in enumerate(a["addressed_attributes"]):
                errs += _id_exists_errors(aa["evidence_ids"], reg, f"{loc}/addressed_attributes/{j}", ("AE",))
        errs += _gap_list_errors(d["gaps"], 3, F03) + gap_id_leaks(d, F03)

    elif stage_id == "stage4-analyze_scenarios":
        d = _load(ws, F04, errs)
        if d is None:
            return errs
        errs += schema_errors(d, CONTRACTS / "analysis.schema.json", F04)
        if errs:
            return errs
        rec_ids, finding_ids, covered = [], [], set()
        for r, rec in enumerate(d["analysis_records"]):
            loc = f"{F04}: /analysis_records/{r}"
            rec_ids.append(rec["record_id"])
            sid = rec["scenario_id"]
            sc = reg["scenarios"].get(sid)
            if sc is None:
                errs.append(f"{loc}: scenario_id {sid!r} is not in {F02}")
            else:
                covered.add(sid)
                sr = rec["scenario_reference"]
                if sr["id"] != sid:
                    errs.append(f"{loc}/scenario_reference/id must equal scenario_id {sid}")
                if sr["text"] != sc["scenario_description"]:
                    errs.append(f"{loc}/scenario_reference/text must be the verbatim scenario_description of {sid}")
                if sr["type"] != sc["scenario_type"]:
                    errs.append(f"{loc}/scenario_reference/type must be {sc['scenario_type']!r}")
                measure = sc["response_measure"]["value"]
                if measure is not None and rec["response_measure"] != measure:
                    errs.append(f"{loc}/response_measure must be copied from {F02}: {measure!r}")
                if measure is None and not rec["response_measure"].lower().startswith("unspecified"):
                    errs.append(f"{loc}/response_measure: scenario {sid} has no supplied measure; write "
                                "'unspecified ...' (without a gap id) and keep the gap in gaps")
            errs += _id_exists_errors(rec["approach_ids"], reg, f"{loc}/approach_ids", ("AP",))
            errs += _id_exists_errors(rec["evidence_ids"], reg, f"{loc}/evidence_ids", ("AE",))
            for k, dec in enumerate(rec["architectural_decisions"]):
                m = CITE_RE.search(dec)
                if not m:
                    errs.append(f"{loc}/architectural_decisions/{k}: cite the decision as '<decision> "
                                "(evidence: AE-n)'")
                else:
                    errs += _id_exists_errors(m.group(1).split(", "), reg,
                                              f"{loc}/architectural_decisions/{k}", ("AE",))
            for kind in ("risks", "non_risks", "sensitivity_points", "tradeoff_points"):
                for f, item in enumerate(rec["findings"][kind]):
                    finding_ids.append(item["id"])
                    allowed = ("AE", "AP", "BD") if kind in ("risks", "non_risks") else ("AE",)
                    errs += _id_exists_errors(item["evidence_ids"], reg, f"{loc}/findings/{kind}/{f}", allowed)
        errs += [f"{F04}: duplicate record_id {i}" for i in sorted({i for i in rec_ids if rec_ids.count(i) > 1})]
        errs += [f"{F04}: duplicate finding id {i}" for i in sorted({i for i in finding_ids if finding_ids.count(i) > 1})]
        un = {u["scenario_id"] for u in d["unanalyzed_scenarios"]}
        errs += [f"{F04}: unanalyzed scenario {u!r} is not in {F02}" for u in sorted(un - set(reg["scenarios"]))]
        missing = sorted(set(reg["scenarios"]) - covered - un)
        errs += [f"{F04}: scenario {s} is neither analyzed nor listed in unanalyzed_scenarios" for s in missing]
        errs += _gap_list_errors(d["gaps"], 4, F04) + gap_id_leaks(d, F04)

    elif stage_id == "stage5-synthesize_report":
        d = _load(ws, F05D, errs)
        if d is None:
            return errs
        errs += schema_errors(d, CONTRACTS / "atam-report.schema.json", F05D)
        try:
            expected = project_report(ws)
        except Exception as exc:  # noqa: BLE001 - surfaced as a gate error
            return errs + [f"projection failed: {exc}"]
        if d != expected:
            diffs = json_diff(expected, d)
            errs.append(f"{F05D}: differs from the deterministic projection of 01-04 at "
                        f"{', '.join(diffs[:8])}{' ...' if len(diffs) > 8 else ''}; stage 5 projects, it "
                        "does not edit (corrections belong to stage7-revise_report)")

    elif stage_id == "stage6-check_evaluation":
        d = _load(ws, F06I, errs)
        report = _load(ws, F05D, errs)
        if d is None or report is None:
            return errs
        errs += schema_errors(d, SCHEMAS / "06_review_findings.schema.json", F06I)
        if errs:
            return errs
        if d["review_stage"] != "initial":
            errs.append(f"{F06I}: review_stage must be 'initial'")
        errs += _review_consistency(ws, d, report, "initial", F06I)

    elif stage_id == "stage7-revise_report":
        draft = _load(ws, F05D, errs)
        final = _load(ws, F05, errs)
        initial = _load(ws, F06I, errs)
        rf = _load(ws, F06, errs)
        if None in (draft, final, initial, rf):
            return errs
        errs += schema_errors(final, CONTRACTS / "atam-report.schema.json", F05)
        errs += schema_errors(rf, SCHEMAS / "06_review_findings.schema.json", F06)
        if errs:
            return errs
        if rf["review_stage"] != "final":
            errs.append(f"{F06}: review_stage must be 'final'")
        errs += _review_consistency(ws, rf, final, "final", F06)
        errs += _revision_scope_errors(draft, final)
        errs += _reviewer_carryover_errors(initial, rf, draft, final)
        expected = compute_final_review(ws, draft, final, initial, rf, load_ledger(ws))
        for key in ("revision", "ready_for_architect_review"):
            if rf.get(key) != expected.get(key):
                errs.append(f"{F06}: {key} does not match the value computed by finalize; run "
                            "`atam.py finalize` and do not edit it by hand")
    else:
        errs.append(f"unknown stage {stage_id}")
    return errs


def _review_consistency(ws, review, report, phase, label) -> list[str]:
    errs = []
    if review["run_id"] != load_ledger(ws)["run_id"]:
        errs.append(f"{label}: run_id must be {load_ledger(ws)['run_id']}")
    auto = {(c["check_id"], c["location"]): c for c in run_checks(ws, report, phase)}
    got_auto = {(c["check_id"], c["location"]): c for c in review["checks"] if c["source"] == "automated"}
    for key, c in auto.items():
        g = got_auto.get(key)
        if g is None:
            errs.append(f"{label}: automated check {key[0]} at {key[1] or '<report>'} is missing; include "
                        "every entry printed by `atam.py check` verbatim")
        elif g["result"] != c["result"]:
            errs.append(f"{label}: automated check {key[0]} at {key[1] or '<report>'} must keep result "
                        f"{c['result']!r} (got {g['result']!r})")
    for key in sorted(set(got_auto) - set(auto)):
        errs.append(f"{label}: automated check {key[0]} at {key[1] or '<report>'} was not produced by "
                    "`atam.py check`; label your own checks source 'reviewer'")
    auto_ids = {k[0] for k in auto}
    for c in review["checks"]:
        if c["category"] != CHECK_PREFIX[c["check_id"].split("-")[0]]:
            errs.append(f"{label}: {c['check_id']} must have category {CHECK_PREFIX[c['check_id'].split('-')[0]]}")
        if c["source"] == "reviewer" and c["check_id"] in auto_ids:
            errs.append(f"{label}: reviewer check id {c['check_id']} collides with an automated check id")
        if c["source"] == "reviewer" and GAP_ID_RE.search(c["location"]):
            errs.append(f"{label}: location must be a JSON pointer, not a gap id")
    keys = [(c["check_id"], c["location"]) for c in review["checks"]]
    errs += [f"{label}: duplicate check {k}" for k in sorted({k for k in keys if keys.count(k) > 1})]
    counts = {r: sum(1 for c in review["checks"] if c["result"] == r) for r in ("pass", "warn", "fail")}
    if review["summary"] != counts:
        errs.append(f"{label}: summary must be {counts}")
    return errs


def _finding_index(report) -> dict:
    out = {}
    for r, rec in enumerate(report["ATAM_Evaluation"]["evaluation_results"]["analysis_records"]):
        for kind in ("risks", "non_risks", "sensitivity_points", "tradeoff_points"):
            for f, item in enumerate(rec["findings"][kind]):
                out[item["id"]] = (r, kind, f, item)
    return out


def _revision_scope_errors(draft, final) -> list[str]:
    """Revision may remove, relabel, relink or rephrase; it may not add findings or touch inputs."""
    errs = []
    d_ev, f_ev = draft["ATAM_Evaluation"], final["ATAM_Evaluation"]
    if f_ev["evaluation_inputs"] != d_ev["evaluation_inputs"]:
        errs.append(f"{F05}: evaluation_inputs must not change during revision")
    d_idx, f_idx = _finding_index(draft), _finding_index(final)
    for fid in sorted(set(f_idx) - set(d_idx)):
        errs.append(f"{F05}: finding {fid} does not exist in the draft; revision cannot add findings")
    for fid in sorted(set(f_idx) & set(d_idx)):
        if f_idx[fid][1] != d_idx[fid][1]:
            errs.append(f"{F05}: finding {fid} changed kind ({d_idx[fid][1]} -> {f_idx[fid][1]})")
    d_sc = {r["scenario_reference"]["id"] for r in d_ev["evaluation_results"]["analysis_records"]}
    f_sc = {r["scenario_reference"]["id"] for r in f_ev["evaluation_results"]["analysis_records"]}
    errs += [f"{F05}: analysis record for {s} is not in the draft" for s in sorted(f_sc - d_sc)]
    d_ap = {a["approach_name"] for a in d_ev["evaluation_results"]["architectural_approaches"]}
    f_ap = {a["approach_name"] for a in f_ev["evaluation_results"]["architectural_approaches"]}
    errs += [f"{F05}: approach {a!r} is not in the draft" for a in sorted(f_ap - d_ap)]
    d_gaps = {g["description"] for g in d_ev["evaluation_results"]["semantic_state"]["gaps"]}
    f_gaps = {g["description"] for g in f_ev["evaluation_results"]["semantic_state"]["gaps"]}
    for g in sorted(d_gaps - f_gaps):
        m = re.match(r"\[(G-\d+-\d+)\]", g)
        if not m or not any(x.startswith(f"[{m.group(1)}]") for x in f_gaps):
            errs.append(f"{F05}: gap {g[:60]!r} was dropped; gaps must stay visible")
    return errs


def _touched(location: str, changed: list[str]) -> bool:
    return any(c == location or c.startswith(location + "/") or location.startswith(c + "/") for c in changed)


def _reviewer_carryover_errors(initial, final_review, draft, final) -> list[str]:
    errs = []
    changed = json_diff(draft, final)
    final_rev = {(c["check_id"], c["location"]): c for c in final_review["checks"] if c["source"] == "reviewer"}
    for c in initial["checks"]:
        if c["source"] != "reviewer":
            continue
        key = (c["check_id"], c["location"])
        g = final_rev.get(key)
        if g is None:
            errs.append(f"{F06}: reviewer check {key[0]} at {key[1] or '<report>'} from the initial review is "
                        "missing; carry every reviewer check forward with an updated result")
            continue
        if c["result"] in ("warn", "fail") and g["result"] == "pass":
            if not (g.get("resolution") or "").strip():
                errs.append(f"{F06}: {key[0]} at {key[1] or '<report>'} is marked pass without a resolution")
            if key[1] and not _touched(key[1], changed):
                errs.append(f"{F06}: {key[0]} at {key[1]} is marked pass but nothing changed at that location")
        if c["result"] in ("warn", "fail") and g["result"] in ("warn", "fail") and not (g.get("resolution") or "").strip():
            errs.append(f"{F06}: {key[0]} at {key[1] or '<report>'} remains {g['result']}; explain what remains "
                        "in resolution")
    return errs


# ----------------------------------------------------------------------------- projection (stage 5)

def _suffix(ids, basis) -> str:
    return f" (evidence: {', '.join(ids)}; basis: {basis})"


def _strip_suffix(text: str) -> str:
    return ANY_SUFFIX_RE.sub("", text).rstrip()


def project_report(ws: Path) -> dict:
    """Project the validated stage 0-4 artifacts into the report contract. Deterministic."""
    ledger = load_ledger(ws)
    d00, d01, d02, d03, d04 = (load_json(ws / n) for n in (F00, F01, F02, F03, F04))
    meta_in = d00.get("metadata") or {}
    metadata = {k: meta_in.get(k) if isinstance(meta_in.get(k), str) else None
                for k in ("system_name", "date", "ref", "evaluator_organization")}
    for k in ("phase_1_attendees", "phase_2_attendees"):
        v = meta_in.get(k)
        metadata[k] = [x for x in v if isinstance(x, str)] if isinstance(v, list) else []
    title = d00.get("title") if isinstance(d00.get("title"), str) and d00.get("title").strip() else None
    title = title or f"ATAM Evaluation — {ledger['run_id']}"

    nodes, scenarios = [], []
    for node in d02["quality_attribute_nodes"]:
        children = []
        for ch in node["children"]:
            pt = ch["priority_tuple"]
            children.append({"refinement": ch["refinement"], "scenario_id": ch["scenario_id"],
                             "scenario_description": ch["scenario_description"],
                             "priority_tuple": {"importance": pt["importance"], "difficulty": pt["difficulty"]}
                             if pt else None})
            scenarios.append({"scenario_text": ch["scenario_description"],
                              "primary_quality_attribute": [node["attribute_name"]]})
        nodes.append({"attribute_name": node["attribute_name"], "children": children})

    approaches = []
    for a in d03["approaches"]:
        desc = _strip_suffix(a["description"])
        if a["basis"] == "inferred":
            desc += f" Inferred approach: {_strip_suffix(a['inference_note'])}"
        approaches.append({
            "approach_name": a["approach_name"],
            "description": desc + _suffix(a["evidence_ids"], a["basis"]),
            "addressed_attributes": [{"quality_attribute": x["quality_attribute"],
                                      "rationale": _strip_suffix(x["rationale"]) + _suffix(x["evidence_ids"], x["basis"])}
                                     for x in a["addressed_attributes"]]})

    records = []
    for rec in d04["analysis_records"]:
        f = rec["findings"]
        records.append({
            "scenario_reference": dict(rec["scenario_reference"]),
            "quality_attribute": rec["quality_attribute"],
            "environment": rec["environment"],
            "stimulus": rec["stimulus"],
            "response_measure": rec["response_measure"],
            "architectural_decisions": list(rec["architectural_decisions"]),
            "reasoning": rec["reasoning"],
            "findings": {
                kind: [{"id": x["id"], "description": x["description"],
                        "rationale": _strip_suffix(x["rationale"]) + _suffix(x["evidence_ids"], x["basis"])}
                       for x in f[kind]] for kind in ("risks", "non_risks")} | {
                "sensitivity_points": [{"id": x["id"],
                                        "parameter": _strip_suffix(x["parameter"]) + f" (evidence: {', '.join(x['evidence_ids'])})",
                                        "correlated_attribute": x["correlated_attribute"]} for x in f["sensitivity_points"]],
                "tradeoff_points": [{"id": x["id"],
                                     "parameter": _strip_suffix(x["parameter"]) + f" (evidence: {', '.join(x['evidence_ids'])})",
                                     "conflicting_attributes": list(x["conflicting_attributes"])} for x in f["tradeoff_points"]]},
        })

    gaps = []
    for doc in (d01, d02, d03, d04):
        for g in doc["gaps"]:
            gaps.append({"description": f"[{g['id']}] ({g['gap_type']}) {g['description']}",
                         "affected_activity": g["affected_activity"],
                         "missing_evidence": g["missing_evidence"],
                         "resolution_question": g["resolution_question"]})

    semantic_state = {
        "context_status": copy.deepcopy(d01["context_status"]),
        "driver_status": copy.deepcopy(d01["driver_status"]),
        "architecture_evidence_status": copy.deepcopy(d01["architecture_evidence_status"]),
        "scenario_analysis_status": copy.deepcopy(d04["scenario_analysis_status"]),
        "report_status": {"value": "draft", "evidence": [
            "No software architect review of this report is recorded in the supplied inputs or workspace artifacts.",
            f"Report content is projected from the validated artifacts {F01}, {F02}, {F03} and {F04}."]},
        "gaps": gaps,
    }
    return {"ATAM_Evaluation": {
        "title": title, "metadata": metadata, "evaluation_inputs": copy.deepcopy(d00["evaluation_inputs"]),
        "evaluation_results": {"utility_tree": {"root": d02["root"], "quality_attribute_nodes": nodes},
                               "architectural_approaches": approaches, "analysis_records": records,
                               "scenarios": scenarios, "semantic_state": semantic_state}}}


def json_diff(a, b, path="") -> list[str]:
    if type(a) is not type(b):
        return [path or "/"]
    if isinstance(a, dict):
        out = []
        for k in list(a) + [k for k in b if k not in a]:
            p = path + ptr([k])
            if k not in a or k not in b:
                out.append(p)
            else:
                out += json_diff(a[k], b[k], p)
        return out
    if isinstance(a, list):
        out = []
        for i in range(max(len(a), len(b))):
            p = f"{path}/{i}"
            out += json_diff(a[i], b[i], p) if i < len(a) and i < len(b) else [p]
        return out
    return [] if a == b else [path or "/"]


# ----------------------------------------------------------------------------- automated checks

def _chk(check_id, result, location, finding, correction=None) -> dict:
    return {"check_id": check_id, "category": CHECK_PREFIX[check_id.split("-")[0]], "source": "automated",
            "result": result, "location": location, "finding": finding, "correction": correction}


def run_checks(ws: Path, report: dict, phase: str) -> list[dict]:
    """Deterministic review checks over a report. phase: 'initial' (draft) or 'final' (revised)."""
    out: list[dict] = []
    viol: dict[str, list] = {}

    def v(cid, result, loc, finding, corr):
        viol.setdefault(cid, []).append(_chk(cid, result, loc, finding, corr))

    errs: list[str] = []
    d00, d01, d02, d03, d04 = (_load(ws, n, errs) for n in (F00, F01, F02, F03, F04))
    ids = [
        "STRUCT-SCHEMA", "STRUCT-SECTIONS", "SEM-REPORT-STATUS", "SEM-ANALYSIS-STATUS", "SEM-STATUS-TRACE",
        "SEM-GAP-ACTIVITY", "SEM-GAPS-PRESERVED", "EVID-RATIONALE-SUFFIX", "EVID-NO-GAP-IDS", "EVID-IDS-EXIST",
        "EVID-FINDING-TRACE", "EVID-SCENARIO-REF", "EVID-DECISION-CITES", "EVID-POINT-CITES",
        "EVID-APPROACH-CITES", "UNC-ABSENCE-BASIS", "UNC-PERF-ATTAINMENT", "UNC-RESPONSE-MEASURE",
        "UNC-PRIORITY", "COV-ACTIVITIES", "COV-SCENARIOS", "REF-NO-REFERENCE-OUTPUTS",
        "REF-INPUTS-PRESERVED", "REF-METADATA"]
    if errs:
        for e in errs:
            v("COV-ACTIVITIES", "fail", "", f"Upstream artifact problem: {e}",
              "Re-run the stage that owns the artifact; revision cannot create upstream evidence.")
    s_errs = schema_errors(report, CONTRACTS / "atam-report.schema.json", "report")
    for e in s_errs:
        loc = e.split(": ")[1] if ": " in e else ""
        v("STRUCT-SCHEMA", "fail", "" if loc == "<root>" else loc, e,
          "Restore the contract shape without adding new content.")
    if s_errs or errs:
        # Content checks cannot be trusted on an invalid report or missing upstream artifacts.
        return _assemble(out, viol, ids, skip=[i for i in ids if i not in viol])

    ev = report["ATAM_Evaluation"]
    res = ev["evaluation_results"]
    base = "/ATAM_Evaluation/evaluation_results"
    reg = registries(ws)

    for sec in ("architectural_approaches", "analysis_records", "scenarios"):
        if not res[sec]:
            v("STRUCT-SECTIONS", "warn", f"{base}/{sec}", f"Section {sec} is empty.",
              "Keep it empty only if the inputs support nothing here, and record the reason as a gap.")
    if not res["utility_tree"]["quality_attribute_nodes"]:
        v("STRUCT-SECTIONS", "warn", f"{base}/utility_tree", "The utility tree has no quality attribute nodes.",
          "Record the missing drivers as a gap.")

    ss = res["semantic_state"]
    if ss["report_status"]["value"] != "draft":
        v("SEM-REPORT-STATUS", "fail", f"{base}/semantic_state/report_status/value",
          "report_status must stay 'draft' until a software architect records a review.", "Set it to 'draft'.")
    if ss["scenario_analysis_status"]["value"] == "reviewed":
        v("SEM-ANALYSIS-STATUS", "fail", f"{base}/semantic_state/scenario_analysis_status/value",
          "scenario_analysis_status 'reviewed' requires a recorded architect review.", "Set it to at most 'partial'.")
    for field, src, srcname in (("context_status", d01, F01), ("driver_status", d01, F01),
                                ("architecture_evidence_status", d01, F01),
                                ("scenario_analysis_status", d04, F04)):
        if ss[field]["value"] != src[field]["value"]:
            v("SEM-STATUS-TRACE", "warn", f"{base}/semantic_state/{field}/value",
              f"{field} is {ss[field]['value']!r} but {srcname} records {src[field]['value']!r}.",
              f"Restore the value recorded in {srcname}.")
    for i, g in enumerate(ss["gaps"]):
        if g["affected_activity"] not in ACTIVITIES:
            v("SEM-GAP-ACTIVITY", "fail", f"{base}/semantic_state/gaps/{i}/affected_activity",
              f"affected_activity {g['affected_activity']!r} is not a methodology activity id.",
              f"Use one of {', '.join(ACTIVITIES)}.")
    report_gap_text = " ".join(g["description"] for g in ss["gaps"])
    for doc in (d01, d02, d03, d04):
        for g in doc["gaps"]:
            if f"[{g['id']}]" not in report_gap_text:
                v("SEM-GAPS-PRESERVED", "warn", f"{base}/semantic_state/gaps",
                  f"Upstream gap {g['id']} is not visible in the report.",
                  f"Restore the gap record for {g['id']} from the upstream artifact.")

    # Evidence traceability.
    for path, s in walk_strings(report):
        if path[:2] == ("ATAM_Evaluation", "evaluation_inputs"):
            continue
        if path[:4] == ("ATAM_Evaluation", "evaluation_results", "semantic_state", "gaps"):
            continue
        for m in GAP_ID_RE.finditer(s):
            v("EVID-NO-GAP-IDS", "fail", ptr(path),
              f"Gap identifier {m.group(0)} appears outside a gap record.",
              "Remove the gap id; refer to the open question in prose and keep the gap only in semantic_state.gaps.")
    f04 = {}
    for rec in d04["analysis_records"]:
        for kind in ("risks", "non_risks", "sensitivity_points", "tradeoff_points"):
            for item in rec["findings"][kind]:
                f04[item["id"]] = (kind, rec["scenario_id"], item)
    for r, rec in enumerate(res["analysis_records"]):
        rloc = f"{base}/analysis_records/{r}"
        sid = rec["scenario_reference"]["id"]
        sc = reg["scenarios"].get(sid)
        if sc is None:
            v("EVID-SCENARIO-REF", "fail", f"{rloc}/scenario_reference/id",
              f"Scenario {sid!r} is not in the utility tree.", "Reference a utility-tree scenario id.")
        elif rec["scenario_reference"]["text"] != sc["scenario_description"]:
            v("EVID-SCENARIO-REF", "fail", f"{rloc}/scenario_reference/text",
              f"Scenario text for {sid} is not verbatim.", "Restore the verbatim scenario_description.")
        for k, dec in enumerate(rec["architectural_decisions"]):
            m = CITE_RE.search(dec)
            if not m:
                v("EVID-DECISION-CITES", "warn", f"{rloc}/architectural_decisions/{k}",
                  "Architectural decision has no (evidence: AE-n) citation.",
                  "Relink it to the AE ids recorded for this analysis record, or remove it.")
            else:
                for i in m.group(1).split(", "):
                    if i not in reg["AE"]:
                        v("EVID-IDS-EXIST", "fail", f"{rloc}/architectural_decisions/{k}",
                          f"{i} is not registered.", "Cite only registered AE ids.")
        perf = bool(PERF_QA_RE.search(rec["quality_attribute"]))
        unmeasured = sc is not None and sc["response_measure"]["value"] is None
        if sc is not None:
            m_val = sc["response_measure"]["value"]
            if (m_val is not None and rec["response_measure"] != m_val) or (
                    m_val is None and not rec["response_measure"].lower().startswith("unspecified")):
                v("UNC-RESPONSE-MEASURE", "warn", f"{rloc}/response_measure",
                  f"Response measure does not match the utility tree ({m_val or 'unspecified'}).",
                  "Use the supplied measure verbatim, or 'unspecified ...' when none was supplied.")
        if perf and unmeasured:
            for path, s in (((f"{rloc}/reasoning"), rec["reasoning"]),) + tuple(
                    (f"{rloc}/findings/{kind}/{f}/{fld}", _strip_suffix(x[fld]))
                    for kind in ("risks", "non_risks") for f, x in enumerate(rec["findings"][kind])
                    for fld in ("description", "rationale")):
                for sent in re.split(r"(?<=[.;!?])\s+", s):
                    m = ATTAIN_RE.search(sent)
                    if m and not UNCERTAIN_RE.search(sent):
                        v("UNC-PERF-ATTAINMENT", "warn", path,
                          f"Performance attainment wording ({m.group(0)!r}) for a scenario with no workload, "
                          f"benchmark or response-time target: {sent.strip()[:160]!r}",
                          "Rephrase as a potential risk and state that attainment cannot be determined "
                          "without a measure.")
        for kind in ("risks", "non_risks"):
            for f, x in enumerate(rec["findings"][kind]):
                floc = f"{rloc}/findings/{kind}/{f}"
                m = SUFFIX_RE.search(x["rationale"])
                if not m or len(re.findall(r"\(evidence:", x["rationale"])) != 1:
                    v("EVID-RATIONALE-SUFFIX", "fail", f"{floc}/rationale",
                      "Rationale does not end with exactly one '(evidence: AE-1, AE-2; basis: observed|inferred)' suffix.",
                      "Restore the suffix from the analysis artifact.")
                    continue
                cited, basis = m.group(1).split(", "), m.group(2)
                for i in cited:
                    ns = i.split("-")[0]
                    if i not in reg[ns]:
                        v("EVID-IDS-EXIST", "fail", f"{floc}/rationale", f"{i} is not registered.",
                          "Cite only registered evidence ids.")
                src = f04.get(x["id"])
                if src is None or src[0] != kind or src[1] != sid:
                    v("EVID-FINDING-TRACE", "fail", f"{floc}/id",
                      f"{x['id']} does not trace to a {kind[:-1]} of scenario {sid} in {F04}.",
                      "Remove the finding or restore its analysis-artifact identity.")
                else:
                    item = src[2]
                    if phase == "initial":
                        ok = set(cited) == set(item["evidence_ids"]) and basis == item["basis"]
                    else:
                        ok = set(cited) <= set(item["evidence_ids"]) and (
                            basis == item["basis"] or (item["basis"] == "observed" and basis == "inferred"))
                    if not ok:
                        v("EVID-FINDING-TRACE", "fail", f"{floc}/rationale",
                          f"Cited evidence/basis ({', '.join(cited)}; {basis}) does not preserve {F04} "
                          f"({', '.join(item['evidence_ids'])}; {item['basis']}).",
                          "Use the analysis artifact's evidence ids; basis may only be downgraded observed->inferred.")
                if basis == "observed":
                    text = x["description"] + " " + _strip_suffix(x["rationale"])
                    m2 = ABSENCE_RE.search(text)
                    if m2:
                        v("UNC-ABSENCE-BASIS", "fail", f"{floc}/rationale",
                          f"Finding labelled observed relies on absent material ({m2.group(0)!r}); a conclusion "
                          "from absence is an inference about uncertainty.",
                          "Relabel basis to inferred and frame the finding as unresolved/potential.")
        for kind in ("sensitivity_points", "tradeoff_points"):
            for f, x in enumerate(rec["findings"][kind]):
                m = CITE_RE.search(x["parameter"])
                if not m:
                    v("EVID-POINT-CITES", "warn", f"{rloc}/findings/{kind}/{f}/parameter",
                      "Sensitivity/tradeoff parameter has lost its (evidence: AE-n) citation.",
                      "Restore the citation from the analysis artifact.")
                if x["id"] not in f04 or f04[x["id"]][0] != kind:
                    v("EVID-FINDING-TRACE", "fail", f"{rloc}/findings/{kind}/{f}/id",
                      f"{x['id']} does not trace to {F04}.", "Remove it or restore its identity.")
    for a, ap in enumerate(res["architectural_approaches"]):
        for j, aa in enumerate(ap["addressed_attributes"]):
            if not SUFFIX_RE.search(aa["rationale"]):
                v("EVID-APPROACH-CITES", "warn",
                  f"{base}/architectural_approaches/{a}/addressed_attributes/{j}/rationale",
                  "Approach rationale has no evidence/basis suffix.", "Restore it from 03_approaches.json.")

    tree02 = reg["scenarios"]
    for n, node in enumerate(res["utility_tree"]["quality_attribute_nodes"]):
        for c, ch in enumerate(node["children"]):
            src = tree02.get(ch["scenario_id"])
            pt = ch["priority_tuple"]
            if pt is not None and (src is None or src["priority_tuple"] is None or
                                   (pt["importance"], pt["difficulty"]) !=
                                   (src["priority_tuple"]["importance"], src["priority_tuple"]["difficulty"])):
                v("UNC-PRIORITY", "fail",
                  f"{base}/utility_tree/quality_attribute_nodes/{n}/children/{c}/priority_tuple",
                  "Priority tuple is not supported by an observed priority in the inputs.",
                  "Set priority_tuple to null and keep the priority question as a gap.")

    acts = [(F01, d01), (F02, d02), (F03, d03), (F04, d04)]
    for name, d in acts:
        if d is None:
            v("COV-ACTIVITIES", "fail", "", f"{name} is missing.", "Run the owning stage.")
    analysed = {r["scenario_reference"]["id"] for r in res["analysis_records"]}
    unanalysed = {u["scenario_id"]: u["reason"] for u in d04["unanalyzed_scenarios"]}
    for sid, sc in tree02.items():
        if sid in analysed:
            continue
        pt = sc["priority_tuple"]
        if sid not in unanalysed:
            v("COV-SCENARIOS", "warn", f"{base}/analysis_records",
              f"Scenario {sid} has no analysis record and no recorded reason.",
              "Restore its analysis record from the analysis artifact.")
        elif pt and pt["importance"] == "High":
            v("COV-SCENARIOS", "warn", f"{base}/analysis_records",
              f"High-importance scenario {sid} was not analyzed ({unanalysed[sid]}).",
              "Keep it visible as a gap; the architect must decide whether the evaluation can proceed.")

    for path, k in walk_keys(report):
        if k == "ground_truth_outputs":
            v("REF-NO-REFERENCE-OUTPUTS", "fail", ptr(path), "Evaluation-only reference outputs present.",
              "Remove them; they must never enter generation.")
    if ev["evaluation_inputs"] != d00["evaluation_inputs"]:
        v("REF-INPUTS-PRESERVED", "fail", "/ATAM_Evaluation/evaluation_inputs",
          f"evaluation_inputs differ from {F00}.", f"Restore them verbatim from {F00}.")
    meta_in = d00.get("metadata") or {}
    for k, val in ev["metadata"].items():
        src = meta_in.get(k)
        if isinstance(val, list):
            if val and val != src:
                v("REF-METADATA", "fail", f"/ATAM_Evaluation/metadata/{k}",
                  f"{k} lists attendees that are not in the supplied metadata.", "Use [] or the supplied list.")
        elif val is not None and val != src:
            v("REF-METADATA", "fail", f"/ATAM_Evaluation/metadata/{k}",
              f"{k} is not supplied by the inputs.", "Use null or the supplied value.")
    return _assemble(out, viol, ids)


def _assemble(out, viol, ids, skip=()):
    for cid in ids:
        if cid in viol:
            seen = set()
            for c in viol[cid]:
                key = (c["check_id"], c["location"])
                if key not in seen:
                    seen.add(key)
                    out.append(c)
        elif cid not in skip:
            out.append(_chk(cid, "pass", "", "No violations found."))
        else:
            out.append(_chk(cid, "fail", "", "Not evaluated because the report or upstream artifacts are invalid.",
                            "Fix the structural failures first."))
    return out


# ----------------------------------------------------------------------------- finalize (stage 7)

def stage_order_status(ledger: dict) -> tuple[bool, str]:
    st = ledger["stages"]
    missing = [s for s in STAGE_IDS[:7] if st.get(s, {}).get("status") != "completed"]
    if missing:
        return False, f"stages not completed before revision: {', '.join(missing)}"
    s7 = st.get("stage7-revise_report", {})
    if s7.get("status") != "started":
        return False, "stage7-revise_report is not the running stage"
    seqs = [st[s]["complete_seq"] for s in STAGE_IDS[:7]]
    if seqs != sorted(seqs) or s7["begin_seq"] <= seqs[-1]:
        return False, "stage completion order in the run ledger is not stage0..stage6 followed by stage7"
    return True, ("run ledger shows stage0..stage6 completed in order and stage7-revise_report begun after "
                  f"stage6-check_evaluation completed (seq {seqs[-1]} < {s7['begin_seq']})")


def compute_final_review(ws, draft, final, initial, agent_review, ledger) -> dict:
    run_id = ledger["run_id"]
    automated = run_checks(ws, final, "final")
    initial_rev = [c for c in initial["checks"] if c["source"] == "reviewer"]
    supplied = {(c["check_id"], c["location"]): c for c in (agent_review or {}).get("checks", [])
                if c.get("source") == "reviewer"}
    reviewer = []
    for c in initial_rev:
        reviewer.append(supplied.pop((c["check_id"], c["location"]), dict(c, resolution=None)))
    reviewer += list(supplied.values())  # reviewer checks newly raised during revision
    initial_auto = {(c["check_id"], c["location"]): c for c in initial["checks"] if c["source"] == "automated"}
    for c in automated:
        prev = initial_auto.get((c["check_id"], c["location"]))
        if prev and prev["result"] != "pass" and c["result"] == "pass":
            c["resolution"] = "Resolved by revision; re-run of the automated check passes."
        elif c["result"] != "pass":
            c["resolution"] = "Remains after revision (automated re-check on the final report)."
        else:
            c["resolution"] = None
    checks = automated + reviewer
    changed = json_diff(draft, final)
    remaining = [{"check_id": c["check_id"], "category": c["category"], "result": c["result"],
                  "location": c["location"]} for c in checks
                 if c["result"] in ("warn", "fail") and c["category"] in BLOCKING_CATEGORIES]
    order_ok, order_detail = stage_order_status(ledger)
    ready = order_ok and not remaining
    return {
        "review_stage": "final", "run_id": run_id, "reviewed_report": F05, "checks": checks,
        "summary": {r: sum(1 for c in checks if c["result"] == r) for r in ("pass", "warn", "fail")},
        "revision": {"applied": bool(changed), "changed_locations": changed, "remaining_failures": remaining},
        "ready_for_architect_review": ready,
        "readiness_basis": {
            "computed_by": "atam_harness/atam.py finalize (stage7-revise_report)",
            "blocking_categories": BLOCKING_CATEGORIES,
            "blocking_findings_remaining": len(remaining),
            "stage_order_verified": order_ok, "stage_order_detail": order_detail,
            "report_status": "draft",
            "note": ("Readiness means the draft may be handed to a software architect for review. The report "
                     "remains a draft and must not inform a decision until that review is recorded."),
        },
    }


def finalize(ws: Path, ledger: dict | None = None) -> list[str]:
    ledger = ledger or load_ledger(ws)
    errs: list[str] = []
    draft, final, initial = _load(ws, F05D, errs), _load(ws, F05, errs), _load(ws, F06I, errs)
    if errs:
        return [f"finalize: {e}" for e in errs]
    agent_review = None
    if (ws / F06).exists():
        try:
            agent_review = load_json(ws / F06)
        except json.JSONDecodeError as exc:
            return [f"finalize: {F06} is not valid JSON ({exc})"]
    dump_json(ws / F06, compute_final_review(ws, draft, final, initial, agent_review, ledger))
    return []


# ----------------------------------------------------------------------------- prompts

def stage_prompt(ws: Path, stage_id: str, gate_errors: list[str] | None = None) -> str:
    s = STAGE_BY_ID[stage_id]
    rel = ws.relative_to(ROOT).as_posix() if ws.is_relative_to(ROOT) else str(ws)
    run_id = load_ledger(ws)["run_id"]
    lines = [
        f"Run {stage_id} of ATAM evaluation run {run_id}.",
        f"Workspace: {rel}/",
        f"Read: {', '.join(f'{rel}/{r}' for r in s['reads'])} (plus the skill references).",
        f"Write ONLY: {', '.join(f'{rel}/{w}' for w in s['writes'])}. Any other change fails the stage gate.",
        f"Follow your agent definition and the `{s['skill']}` skill (methodology activity: {s['activity']}).",
        f"Before finishing, run `python3 atam_harness/atam.py validate {stage_id} --workspace {rel}` and fix "
        "your output until it prints no errors.",
        "Do not run `atam.py stage begin/complete` and do not run any other stage's work.",
        "Finish with a short plain-text summary of what you wrote and which gaps you recorded.",
    ]
    if gate_errors:
        lines += ["", "The previous attempt of this stage FAILED its gate. Fix exactly these problems "
                  "(keep everything else):"] + [f"- {e}" for e in gate_errors]
    return "\n".join(lines)


# ----------------------------------------------------------------------------- CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="atam.py", description=__doc__.splitlines()[0])
    ap.add_argument("--workspace", help="workspace directory (default: <bundle>/_workspace)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("intake", help="stage0: copy the input into the workspace and start a run ledger")
    p.add_argument("--input", required=True)
    p.add_argument("--run-id", required=True)
    p = sub.add_parser("stage", help="begin or complete a stage in the run ledger")
    p.add_argument("action", choices=["begin", "complete"])
    p.add_argument("stage_id", choices=STAGE_IDS[1:])
    p.add_argument("--invocation", default="manual", choices=["claude-p", "agent-tool", "manual"])
    p.add_argument("--retry", action="store_true")
    p.add_argument("--rerun", action="store_true")
    p = sub.add_parser("validate", help="run a stage's gate checks without recording anything")
    p.add_argument("stage_id", choices=STAGE_IDS)
    p = sub.add_parser("check", help="print the automated review checks for a report as JSON")
    p.add_argument("--report", required=True)
    p.add_argument("--phase", choices=["initial", "final"], required=True)
    sub.add_parser("project-draft", help="stage5: write 05_atam_report_draft.json from artifacts 00-04")
    sub.add_parser("start-final", help="stage7: copy the draft to 05_atam_report.json if it does not exist")
    sub.add_parser("finalize", help="stage7: compute 06_review_findings.json and readiness")
    p = sub.add_parser("stage-prompt", help="print the instruction for a stage agent")
    p.add_argument("stage_id", choices=STAGE_IDS[1:])
    sub.add_parser("status", help="print the run ledger summary")
    for name in ("validate", "check", "project-draft", "start-final", "finalize", "stage-prompt", "status", "stage", "intake"):
        sub.choices[name].add_argument("--workspace", dest="workspace_sub")
    a = ap.parse_args(argv)
    ws = ws_path(getattr(a, "workspace_sub", None) or a.workspace)

    if a.cmd == "intake":
        return cmd_intake(ws, Path(a.input).resolve(), a.run_id)
    if a.cmd == "stage":
        if a.action == "begin":
            return cmd_stage_begin(ws, a.stage_id, a.invocation, a.retry, a.rerun)
        return cmd_stage_complete(ws, a.stage_id)
    if a.cmd == "validate":
        errs = validate_stage(ws, a.stage_id)
        print("\n".join(errs) if errs else f"{a.stage_id}: gate checks pass")
        return 1 if errs else 0
    if a.cmd == "check":
        print(json.dumps(run_checks(ws, load_json(Path(a.report)), a.phase), indent=2, ensure_ascii=False))
        return 0
    ledger = load_ledger(ws)
    running = {sid for sid, r in ledger["stages"].items() if r.get("status") == "started"}
    if a.cmd == "project-draft":
        if "stage5-synthesize_report" not in running:
            print("project-draft runs only inside stage5-synthesize_report", file=sys.stderr)
            return 1
        dump_json(ws / F05D, project_report(ws))
        print(f"wrote {F05D}")
        return 0
    if a.cmd == "start-final":
        if "stage7-revise_report" not in running:
            print("start-final runs only inside stage7-revise_report", file=sys.stderr)
            return 1
        if not (ws / F05).exists():
            shutil.copyfile(ws / F05D, ws / F05)
            print(f"copied {F05D} -> {F05}")
        else:
            print(f"{F05} already exists; left unchanged")
        return 0
    if a.cmd == "finalize":
        if "stage7-revise_report" not in running:
            print("finalize runs only inside stage7-revise_report", file=sys.stderr)
            return 1
        errs = finalize(ws, ledger)
        if errs:
            print("\n".join(errs), file=sys.stderr)
            return 1
        r = load_json(ws / F06)
        print(f"wrote {F06}: ready_for_architect_review={str(r['ready_for_architect_review']).lower()}, "
              f"remaining blocking findings={r['readiness_basis']['blocking_findings_remaining']}")
        return 0
    if a.cmd == "stage-prompt":
        print(stage_prompt(ws, a.stage_id))
        return 0
    if a.cmd == "status":
        print(f"run_id: {ledger['run_id']}")
        for sid in STAGE_IDS:
            r = ledger["stages"].get(sid)
            print(f"  {sid:28s} {r['status'] if r else 'not started':12s}"
                  f"{' attempts=' + str(r['attempts']) if r else ''}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
