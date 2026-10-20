"""Model-free utilities for the partial-reference SAAM WRCS pilot."""

from __future__ import annotations

import argparse
import json
import secrets
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harnessweaver._integrity import contains_secret_setting as _contains_secret_setting
from harnessweaver._integrity import sha256_bytes, sha256_file as sha256

CONFIG_PATH = Path(__file__).with_name("pilot.json")
RUNS_DIR = Path(__file__).with_name("runs")
CHECKER_VERSION = "0.5"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def run_artifact(run_dir: Path, reference: str) -> Path:
    """Resolve a recorded artifact only when it stays inside its immutable run directory."""
    run_root = run_dir.resolve()
    artifact = (run_root / reference).resolve()
    if not artifact.is_relative_to(run_root) or not artifact.is_file():
        raise ValueError(f"run artifact must be an existing file inside {run_root}: {reference}")
    return artifact


def resolve(reference: str) -> Path:
    return (CONFIG_PATH.parent / reference).resolve()


def generation_input(source: dict[str, Any]) -> dict[str, Any]:
    """Build the shared generation view without exposing evaluator references."""
    scenarios = source["ground_truth_outputs"].get("scenarios", [])
    return {
        **source["evaluation_inputs"],
        "scenario_inputs": [
            {"scenario_id": item["scenario_id"], "scenario_text": item["scenario_text"]}
            for item in scenarios
        ],
    }


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    """Resolve a non-root RFC 6901 pointer against the generation input."""
    if not pointer.startswith("/"):
        raise ValueError("evidence pointer must start with '/'")
    value = document
    for raw_token in pointer[1:].split("/"):
        token_index = 0
        while token_index < len(raw_token):
            if raw_token[token_index] == "~":
                if token_index + 1 == len(raw_token) or raw_token[token_index + 1] not in "01":
                    raise ValueError(f"evidence pointer has an invalid escape: {pointer}")
                token_index += 2
            else:
                token_index += 1
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and token in value:
            value = value[token]
        elif isinstance(value, list) and token and all("0" <= char <= "9" for char in token):
            if token == "0":
                array_index = 0
            elif token[0] != "0" and len(token) <= len(str(max(len(value) - 1, 0))):
                array_index = int(token)
            else:
                raise ValueError(f"evidence pointer has an invalid array index: {pointer}")
            if array_index >= len(value):
                raise ValueError(f"evidence pointer does not resolve: {pointer}")
            value = value[array_index]
        else:
            raise ValueError(f"evidence pointer does not resolve: {pointer}")
    return value


def prepare(run_id: str, arm: str = "unassigned") -> Path:
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ValueError("run_id must be a single safe path component")
    config = read_json(CONFIG_PATH)
    case_path = resolve(config["source_case"])
    case_bytes = case_path.read_bytes()
    case_data = json.loads(case_bytes)
    if not isinstance(case_data, dict):
        raise ValueError(f"JSON root must be an object: {case_path}")
    source = case_data["SAAM_Evaluation_Extract"]
    if "evaluation_inputs" not in source or "ground_truth_outputs" not in source:
        raise ValueError("source case must separate evaluation_inputs and ground_truth_outputs")
    scenarios = source["ground_truth_outputs"].get("scenarios", [])
    actual_ids = [item.get("scenario_id") for item in scenarios if isinstance(item, dict)]
    expected_ids = config["represented_scenario_ids"]
    if actual_ids != expected_ids:
        raise ValueError(f"partialness contract changed: expected scenarios {expected_ids}, got {actual_ids}")

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    # The case extraction stores its six verbatim source scenarios beside
    # evaluator-only references. Expose only their IDs and source text to the
    # model; classifications and assessment outputs remain evaluator-only.
    evaluation_input = generation_input(source)
    generation_scenarios = evaluation_input["scenario_inputs"]
    input_path = run_dir / "evaluation_input.json"
    input_bytes = (json.dumps({"SAAM_Evaluation_Extract": {"evaluation_inputs": evaluation_input}}, indent=2) + "\n").encode("utf-8")
    input_path.write_bytes(input_bytes)
    spec_path = resolve(config["harness_spec"])
    manifest = {
        "manifest_version": "0.1", "run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(),
        "case_id": config["case_id"], "arm": arm, "status": "prepared",
        "source_case": config["source_case"], "source_case_sha256": sha256_bytes(case_bytes),
        "evaluation_input": "evaluation_input.json", "evaluation_input_sha256": sha256_bytes(input_bytes),
        "harness_spec": config["harness_spec"], "harness_spec_sha256": sha256(spec_path) if spec_path.is_file() else None,
        "scenario_input_provenance": {
            "source_pointer": "SAAM_Evaluation_Extract.ground_truth_outputs.scenarios",
            "fields_exposed": ["scenario_id", "scenario_text"],
            "count": len(generation_scenarios),
            "evaluation_outputs_exposed": False,
        },
        "partial_reference": {"represented_scenarios": 6, "known_total_scenarios": 15, "inferred_fields": ["architecture style", "evaluator roles", "scenario interaction grouping"]},
        "runtime": None, "model": None, "settings": None, "prediction": None,
        "latency_seconds": None, "cost_usd": None,
        "notes": "Write-once run. Six source scenario IDs/texts are exposed as generation inputs; classifications and all evaluator-derived outputs remain evaluator-only. Null cost/time means unavailable, not zero."
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return run_dir


def check(prediction: Path) -> list[str]:
    config = read_json(CONFIG_PATH)
    source_case = read_json(resolve(config["source_case"]))["SAAM_Evaluation_Extract"]
    source = source_case["ground_truth_outputs"]
    allowed_evidence = generation_input(source_case)
    data = read_json(prediction)
    result = data.get("SAAM_Evaluation", data)
    problems: list[str] = []
    if not isinstance(result, dict):
        return ["SAAM_Evaluation must be an object"]
    for section in config["required_sections"]:
        if section not in result:
            problems.append(f"missing required section: {section}")
    represented = set(config["represented_scenario_ids"])
    for section, id_field, allowed in (("scenarios", "scenario_id", represented),
                                        ("scenario_classification", "scenario_id", represented),
                                        # S-02 is represented, but has no extracted evaluation reference.
                                        ("scenario_evaluations", "scenario_id", represented)):
        entries = result.get(section)
        if not isinstance(entries, list):
            problems.append(f"{section} must be an array")
            continue
        seen: set[str] = set()
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                problems.append(f"{section}[{i}] must be an object")
                continue
            ref = entry.get(id_field)
            if ref and ref not in allowed:
                problems.append(f"{section}[{i}] references unavailable scenario {ref}; absent scenario references are unknown")
            if ref and ref in seen:
                problems.append(f"{section} contains duplicate scenario ID {ref}")
            if ref:
                seen.add(ref)

    def check_evidence(section: str, entries: Any, *, required: bool) -> None:
        if not isinstance(entries, list):
            if required:
                problems.append(f"{section} must be an array")
            return
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                problems.append(f"{section}[{index}] must be an object")
                continue
            refs = entry.get("evidence_refs", [])
            if not isinstance(refs, list):
                problems.append(f"{section}[{index}].evidence_refs must be an array")
                continue
            if required and not refs:
                problems.append(f"{section}[{index}] must cite at least one generation-input evidence pointer")
            for ref_index, ref in enumerate(refs):
                pointer = ref.get("source_pointer") if isinstance(ref, dict) else None
                if not isinstance(pointer, str):
                    problems.append(f"{section}[{index}].evidence_refs[{ref_index}].source_pointer must be a string")
                    continue
                try:
                    evidence_value = resolve_json_pointer(allowed_evidence, pointer)
                except ValueError as exc:
                    problems.append(f"{section}[{index}].evidence_refs[{ref_index}]: {exc}")
                    continue
                if evidence_value is None or isinstance(evidence_value, (dict, list)) or (isinstance(evidence_value, str) and not evidence_value.strip()):
                    problems.append(f"{section}[{index}].evidence_refs[{ref_index}] must point to a non-empty scalar source value")

    for section in ("scenario_classification", "scenario_evaluations", "scenario_interactions", "recommendations"):
        entries = result.get(section, [])
        check_evidence(section, entries, required=True)
    overall = result.get("overall_results", {})
    if not isinstance(overall, dict):
        problems.append("overall_results must be an object")
    else:
        for section in ("architectural_strengths", "architectural_weaknesses"):
            check_evidence(f"overall_results.{section}", overall.get(section, []), required=True)
        assessment = overall.get("modifiability_assessment")
        if isinstance(assessment, dict):
            check_evidence("overall_results.modifiability_assessment", [assessment], required=True)
        elif assessment is not None:
            problems.append("overall_results.modifiability_assessment must be an object or null")
    # Ensure every represented input scenario appears, without requiring unsupported scenarios.
    entries = result.get("scenarios", [])
    got = {e.get("scenario_id") for e in entries if isinstance(e, dict)} if isinstance(entries, list) else set()
    missing = set(config["represented_scenario_ids"]) - got
    if missing:
        problems.append(f"missing represented scenario IDs: {', '.join(sorted(missing))}")
    source_scenarios = {item["scenario_id"]: item["scenario_text"] for item in source.get("scenarios", [])}
    if isinstance(entries, list):
        for item in entries:
            if not isinstance(item, dict) or item.get("scenario_id") not in source_scenarios:
                continue
            observed_text = " ".join(str(item.get("scenario_text", "")).split())
            expected_text = " ".join(source_scenarios[item["scenario_id"]].split())
            if observed_text != expected_text:
                problems.append(f"scenarios[{item['scenario_id']}].scenario_text differs from source scenario text")
    # The reference set itself is checked against the immutable source contract.
    # The source case names this section `evaluations`; keep the alias for any
    # normalized source copy that uses `scenario_evaluations`.
    source_evaluations = source.get("scenario_evaluations", source.get("evaluations", []))
    known = {item["scenario_id"] for item in source_evaluations}
    if known != set(config["represented_evaluations"]):
        problems.append("pilot configuration no longer matches represented evaluator references")
    expected_classification = {item["scenario_id"]: item.get("classification") for item in source.get("scenario_classification", [])}
    observed_classification = result.get("scenario_classification", [])
    if isinstance(observed_classification, list):
        observed_ids = {item.get("scenario_id") for item in observed_classification if isinstance(item, dict)}
        missing_classifications = set(expected_classification) - observed_ids
        if missing_classifications:
            problems.append(f"missing represented classifications: {', '.join(sorted(missing_classifications))}")
        for item in observed_classification:
            if isinstance(item, dict) and item.get("scenario_id") in expected_classification:
                expected = expected_classification[item["scenario_id"]]
                if item.get("classification") != expected:
                    problems.append(f"scenario_classification[{item['scenario_id']}] differs from represented reference")
    interactions = result.get("scenario_interactions", [])
    if isinstance(interactions, list):
        for index, interaction in enumerate(interactions):
            if not isinstance(interaction, dict):
                continue
            linked = interaction.get("interacting_scenarios", [])
            if not isinstance(linked, list):
                problems.append(f"scenario_interactions[{index}].interacting_scenarios must be an array")
                continue
            unavailable = sorted(set(linked) - represented)
            if unavailable:
                problems.append(f"scenario_interactions[{index}] references unavailable scenarios: {', '.join(unavailable)}")
    expected_evaluations = {item["scenario_id"]: item for item in source_evaluations}
    observed_evaluations = result.get("scenario_evaluations", [])
    if isinstance(observed_evaluations, list):
        for item in observed_evaluations:
            if not isinstance(item, dict) or item.get("scenario_id") not in expected_evaluations:
                continue  # No evaluator reference exists for this represented scenario (currently S-02).
            expected = expected_evaluations[item["scenario_id"]]
            for field in ("affected_components", "change_extent"):
                if field in item and item[field] != expected.get(field):
                    problems.append(f"scenario_evaluations[{item['scenario_id']}].{field} differs from represented reference")
    return problems


def record_execution(run_dir: Path, *, arm: str, runtime: str, model: str, settings: dict[str, Any], prediction: Path,
                     latency_seconds: float | None = None, cost_usd: float | None = None,
                     status: str = "succeeded", error_type: str | None = None) -> Path:
    run_dir, prediction = run_dir.resolve(), prediction.resolve()
    if not (run_dir / "manifest.json").is_file():
        raise ValueError(f"run manifest not found: {run_dir}")
    if status not in {"succeeded", "partial", "failed"}:
        raise ValueError("status must be succeeded, partial, or failed")
    if _contains_secret_setting(settings):
        raise ValueError("settings must not contain credentials or secrets")
    if prediction.exists() and (not prediction.is_file() or not prediction.is_relative_to(run_dir)):
        raise ValueError("prediction must be a file inside the run directory")
    if status == "succeeded" and not prediction.is_file():
        raise ValueError("a successful execution requires a prediction file")
    target = run_dir / "execution.json"
    record = {"record_version": "0.1", "arm": arm, "runtime": runtime, "model": model, "settings": settings,
              "status": status,
              "prediction": prediction.relative_to(run_dir).as_posix() if prediction.is_file() else None,
              "prediction_sha256": sha256(prediction) if prediction.is_file() else None,
              "latency_seconds": latency_seconds, "cost_usd": cost_usd, "error_type": error_type}
    with target.open("x", encoding="utf-8") as destination:
        destination.write(json.dumps(record, indent=2) + "\n")
    return target


def prepare_blind_review(packet_id: str, baseline_run_id: str, guided_run_id: str) -> Path:
    """Create identical anonymized packets for independent reviewers and keep the arm key private."""
    if not packet_id or Path(packet_id).name != packet_id or packet_id in {".", ".."}:
        raise ValueError("packet_id must be a single safe path component")
    if any(not run_id or Path(run_id).name != run_id or run_id in {".", ".."} for run_id in (baseline_run_id, guided_run_id)):
        raise ValueError("source run IDs must be single safe path components")
    runs = [(RUNS_DIR / run_id).resolve() for run_id in (baseline_run_id, guided_run_id)]
    runs_root = RUNS_DIR.resolve()
    if any(not run.is_relative_to(runs_root) for run in runs):
        raise ValueError("source runs must be inside the configured runs directory")
    manifests = [read_json(run / "manifest.json") for run in runs]
    executions = [read_json(run / "execution.json") for run in runs]
    if [item["arm"] for item in executions] != ["baseline", "spec-guided"]:
        raise ValueError("review packet requires baseline then spec-guided runs")
    if manifests[0]["evaluation_input_sha256"] != manifests[1]["evaluation_input_sha256"]:
        raise ValueError("paired runs must have identical generation inputs")
    input_paths = [run_artifact(run, "evaluation_input.json") for run in runs]
    prediction_paths = [run_artifact(run, execution["prediction"]) for run, execution in zip(runs, executions)]
    for run, manifest, input_path, execution, prediction_path in zip(runs, manifests, input_paths, executions, prediction_paths):
        if sha256(input_path) != manifest["evaluation_input_sha256"]:
            raise ValueError(f"paired run input fingerprint changed: {run.name}")
        if sha256(prediction_path) != execution["prediction_sha256"]:
            raise ValueError(f"paired run prediction fingerprint changed: {run.name}")

    packet = RUNS_DIR / f"review-{packet_id}"
    packet.mkdir(parents=True, exist_ok=False)
    # Use random opaque IDs and ordering so labels reveal no treatment assignment.
    labels = [f"P-{secrets.token_hex(6).upper()}", f"P-{secrets.token_hex(6).upper()}"]
    order = [0, 1]
    secrets.SystemRandom().shuffle(order)
    arm_key: dict[str, str] = {}
    common_input = input_paths[0]
    for reviewer in ("reviewer-1", "reviewer-2"):
        reviewer_dir = packet / reviewer
        reviewer_dir.mkdir()
        shutil.copyfile(common_input, reviewer_dir / "case-input.json")
        for index in order:
            label = labels[index]
            shutil.copyfile(prediction_paths[index], reviewer_dir / f"{label}.json")
            arm_key[label] = executions[index]["arm"]
        (reviewer_dir / "review-form.md").write_text(REVIEW_FORM, encoding="utf-8")

    key_dir = RUNS_DIR / ".review-keys"
    key_dir.mkdir(exist_ok=True)
    with (key_dir / f"{packet_id}.json").open("x", encoding="utf-8") as key_file:
        key_file.write(json.dumps(arm_key, indent=2) + "\n")
    return packet


REVIEW_FORM = """# Independent SAAM report review

Review each anonymized report independently using only the supplied case input and report. Do not seek or use source-paper reference outputs, run prompts, settings, or arm labels. Keep your scores and notes private until both reports are complete. Submit one completed form per report.

Score each dimension from 1 (absent or unsupported) to 5 (complete and well supported). Cite specific report text or scenario IDs for every score.

| Dimension | Score (1–5) | Evidence / rationale |
|---|---:|---|
| SAAM method coverage: classification, impact, interactions, synthesis | | |
| Evidence grounding: supplied architecture facts versus labeled inference | | |
| Uncertainty discipline: partialness and unsupported details remain explicit | | |
| Usefulness and internal consistency of conclusions/recommendations | | |

Critical omissions or unsupported claims:

Reviewer confidence (low / medium / high) and reason:

Review duration, if measured:
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("prepare")
    create.add_argument("--run-id", required=True)
    create.add_argument("--arm", choices=("baseline", "spec-guided", "unassigned"), default="unassigned")
    validate = commands.add_parser("check"); validate.add_argument("prediction", type=Path)
    record = commands.add_parser("record")
    record.add_argument("run_dir", type=Path)
    record.add_argument("--arm", choices=("baseline", "spec-guided"), required=True)
    record.add_argument("--runtime", required=True)
    record.add_argument("--model", required=True)
    record.add_argument("--settings-json", required=True)
    record.add_argument("--prediction", type=Path, required=True)
    record.add_argument("--latency-seconds", type=float)
    record.add_argument("--cost-usd", type=float)
    review = commands.add_parser("prepare-review")
    review.add_argument("--packet-id", required=True)
    review.add_argument("--baseline-run", required=True)
    review.add_argument("--guided-run", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            print(prepare(args.run_id, args.arm)); return 0
        if args.command == "record":
            settings = json.loads(args.settings_json)
            if not isinstance(settings, dict):
                raise ValueError("settings JSON must be an object")
            print(record_execution(args.run_dir, arm=args.arm, runtime=args.runtime, model=args.model, settings=settings, prediction=args.prediction, latency_seconds=args.latency_seconds, cost_usd=args.cost_usd))
            return 0
        if args.command == "prepare-review":
            print(prepare_blind_review(args.packet_id, args.baseline_run, args.guided_run))
            return 0
        problems = check(args.prediction)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr); return 2
    if problems:
        print("FAIL\n" + "\n".join(f"- {problem}" for problem in problems)); return 1
    print("PASS: represented scenario structure and reference bounds are valid; no claims are made about absent scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
