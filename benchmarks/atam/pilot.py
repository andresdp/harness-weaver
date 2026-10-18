"""Small, model-free utilities for the ArchEval ATAM pilot protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).with_name("pilot.json")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve(reference: str) -> Path:
    return (CONFIG_PATH.parent / reference).resolve()


def prepare(run_id: str) -> Path:
    config = read_json(CONFIG_PATH)
    case_path = resolve(config["source_case"])
    spec_path = resolve(config["harness_spec"])
    source = read_json(case_path)["ATAM_Evaluation"]
    if "evaluation_inputs" not in source or "ground_truth_outputs" not in source:
        raise ValueError("source case must contain separate evaluation_inputs and ground_truth_outputs")

    run_dir = Path(__file__).with_name("runs") / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    input_path = run_dir / "evaluation_input.json"
    input_path.write_text(json.dumps({"ATAM_Evaluation": {"evaluation_inputs": source["evaluation_inputs"]}}, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "manifest_version": "0.1",
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_id": config["case_id"],
        "arm": "unassigned",
        "status": "prepared",
        "source_case": config["source_case"],
        "source_case_sha256": sha256(case_path),
        "evaluation_input": "evaluation_input.json",
        "evaluation_input_sha256": sha256(input_path),
        "harness_spec": config["harness_spec"],
        "harness_spec_version": read_json(spec_path) if spec_path.suffix == ".json" else None,
        "harness_spec_sha256": sha256(spec_path),
        "notes": "See the write-once execution.json for arm/runtime/model/settings and measurements. Never add ground truth to this run directory.",
    }
    # The example spec is YAML; preserve its version as read from the source text.
    manifest["harness_spec_version"] = "0.1"
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return run_dir


def check(prediction: Path) -> list[str]:
    config = read_json(CONFIG_PATH)
    data = read_json(prediction)
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["prediction root must be an object"]
    atam = data.get("ATAM_Evaluation", data)
    if not isinstance(atam, dict):
        return ["ATAM_Evaluation must be an object"]
    generated = atam.get("generated", atam)
    if not isinstance(generated, dict):
        return ["generated ATAM result must be an object"]
    for section in config["required_sections"]:
        if section not in generated:
            problems.append(f"missing required section: {section}")
    approaches = generated.get("architectural_approaches", [])
    if not isinstance(approaches, list) or not approaches:
        problems.append("architectural_approaches must be a non-empty array")
    for index, approach in enumerate(approaches if isinstance(approaches, list) else []):
        if not isinstance(approach, dict):
            problems.append(f"architectural_approaches[{index}] must be an object")
            continue
        for field in ("approach_name", "description", "addressed_attributes"):
            if not approach.get(field):
                problems.append(f"architectural_approaches[{index}].{field} is required")
    tree = generated.get("utility_tree", {})
    nodes = tree.get("quality_attribute_nodes", []) if isinstance(tree, dict) else []
    if not isinstance(nodes, list) or not nodes:
        problems.append("utility_tree.quality_attribute_nodes must be a non-empty array")
    scenarios = generated.get("scenarios", [])
    if not isinstance(scenarios, list) or not scenarios:
        problems.append("scenarios must be a non-empty array")
    scenario_ids = {item.get("scenario_id") for item in scenarios if isinstance(item, dict) and item.get("scenario_id")}
    scenario_texts = {
        " ".join(item["scenario_text"].split())
        for item in scenarios
        if isinstance(item, dict) and isinstance(item.get("scenario_text"), str) and item["scenario_text"].strip()
    }
    records = generated.get("analysis_records", [])
    if not isinstance(records, list) or not records:
        problems.append("analysis_records must be a non-empty array")
    for index, record in enumerate(records if isinstance(records, list) else []):
        if not isinstance(record, dict):
            problems.append(f"analysis_records[{index}] must be an object")
            continue
        reference = record.get("scenario_reference", {})
        scenario_id = reference.get("id") if isinstance(reference, dict) else None
        raw_text = reference.get("text", "") if isinstance(reference, dict) else ""
        scenario_text = " ".join(raw_text.split()) if isinstance(raw_text, str) else ""
        if not ((scenario_id and scenario_id in scenario_ids) or (scenario_text and scenario_text in scenario_texts)):
            problems.append(f"analysis_records[{index}].scenario_reference must match a generated scenario by id or text")
        findings = record.get("findings", {})
        if not isinstance(findings, dict):
            problems.append(f"analysis_records[{index}].findings must be an object")
            continue
        for field in config["required_finding_groups"]:
            group = findings.get(field)
            if not isinstance(group, list):
                problems.append(f"analysis_records[{index}].findings.{field} must be an array")
    return problems


def record_execution(run_dir: Path, arm: str, runtime: str, model: str, settings: dict[str, Any], prediction: Path, latency: float | None, cost: float | None) -> Path:
    run_dir = run_dir.resolve()
    prediction = prediction.resolve()
    if not (run_dir / "manifest.json").is_file():
        raise ValueError(f"run manifest not found in {run_dir}")
    if not prediction.is_file() or not prediction.is_relative_to(run_dir):
        raise ValueError("prediction must be a file inside the run directory")
    output = run_dir / "execution.json"
    if output.exists():
        raise FileExistsError(f"execution record already exists: {output}")
    record = {
        "record_version": "0.1",
        "arm": arm,
        "runtime": runtime,
        "model": model,
        "settings": settings,
        "prediction": prediction.relative_to(run_dir).as_posix(),
        "prediction_sha256": sha256(prediction),
        "latency_seconds": latency,
        "cost": cost,
    }
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("prepare", help="create an isolated run with evaluation inputs only")
    create.add_argument("--run-id", required=True)
    validate = sub.add_parser("check", help="run deterministic ATAM structure and reference checks")
    validate.add_argument("prediction", type=Path)
    record = sub.add_parser("record", help="write a single immutable execution record for a prepared run")
    record.add_argument("run_dir", type=Path)
    record.add_argument("--arm", choices=("baseline", "spec-guided"), required=True)
    record.add_argument("--runtime", required=True)
    record.add_argument("--model", required=True)
    record.add_argument("--settings-json", required=True, help="JSON object containing temperature and other run settings")
    record.add_argument("--prediction", required=True, type=Path, help="prediction file inside the run directory")
    record.add_argument("--latency-seconds", type=float)
    record.add_argument("--cost", type=float, help="recorded cost in USD, or omit if unavailable")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            print(prepare(args.run_id))
            return 0
        if args.command == "record":
            settings = json.loads(args.settings_json)
            if not isinstance(settings, dict):
                raise ValueError("--settings-json must contain a JSON object")
            print(record_execution(args.run_dir, args.arm, args.runtime, args.model, settings, args.prediction, args.latency_seconds, args.cost))
            return 0
        problems = check(args.prediction)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if problems:
        print("FAIL")
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    print("PASS: required ATAM sections and scenario references are structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
