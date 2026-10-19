"""Model-free utilities for the partial-reference SAAM WRCS pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).with_name("pilot.json")
RUNS_DIR = Path(__file__).with_name("runs")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(reference: str) -> Path:
    return (CONFIG_PATH.parent / reference).resolve()


def prepare(run_id: str, arm: str = "unassigned") -> Path:
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ValueError("run_id must be a single safe path component")
    config = read_json(CONFIG_PATH)
    case_path = resolve(config["source_case"])
    source = read_json(case_path)["SAAM_Evaluation_Extract"]
    if "evaluation_inputs" not in source or "ground_truth_outputs" not in source:
        raise ValueError("source case must separate evaluation_inputs and ground_truth_outputs")
    scenarios = source["ground_truth_outputs"].get("scenarios", [])
    actual_ids = [item.get("scenario_id") for item in scenarios if isinstance(item, dict)]
    expected_ids = config["represented_scenario_ids"]
    if actual_ids != expected_ids:
        raise ValueError(f"partialness contract changed: expected scenarios {expected_ids}, got {actual_ids}")

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    input_path = run_dir / "evaluation_input.json"
    input_path.write_text(json.dumps({"SAAM_Evaluation_Extract": {"evaluation_inputs": source["evaluation_inputs"]}}, indent=2) + "\n", encoding="utf-8")
    spec_path = resolve(config["harness_spec"])
    manifest = {
        "manifest_version": "0.1", "run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(),
        "case_id": config["case_id"], "arm": arm, "status": "prepared",
        "source_case": config["source_case"], "source_case_sha256": sha256(case_path),
        "evaluation_input": "evaluation_input.json", "evaluation_input_sha256": sha256(input_path),
        "harness_spec": config["harness_spec"], "harness_spec_sha256": sha256(spec_path) if spec_path.is_file() else None,
        "partial_reference": {"represented_scenarios": 6, "known_total_scenarios": 15, "inferred_fields": ["architecture style", "evaluator roles", "scenario interaction grouping"]},
        "runtime": None, "model": None, "settings": None, "prediction": None,
        "latency_seconds": None, "cost_usd": None,
        "notes": "Write-once run. Ground truth is evaluator-only and must never be copied here. Null cost/time means unavailable, not zero."
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return run_dir


def check(prediction: Path) -> list[str]:
    config = read_json(CONFIG_PATH)
    source = read_json(resolve(config["source_case"]))["SAAM_Evaluation_Extract"]["ground_truth_outputs"]
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
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                problems.append(f"{section}[{i}] must be an object")
                continue
            ref = entry.get(id_field)
            if ref and ref not in allowed:
                problems.append(f"{section}[{i}] references unavailable scenario {ref}; absent scenario references are unknown")
    # Ensure every represented input scenario appears, without requiring unsupported scenarios.
    entries = result.get("scenarios", [])
    got = {e.get("scenario_id") for e in entries if isinstance(e, dict)} if isinstance(entries, list) else set()
    missing = set(config["represented_scenario_ids"]) - got
    if missing:
        problems.append(f"missing represented scenario IDs: {', '.join(sorted(missing))}")
    # The reference set itself is checked against the immutable source contract.
    known = {item["scenario_id"] for item in source.get("scenario_evaluations", [])}
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
    expected_evaluations = {item["scenario_id"]: item for item in source.get("scenario_evaluations", [])}
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
                     latency_seconds: float | None = None, cost_usd: float | None = None) -> Path:
    run_dir, prediction = run_dir.resolve(), prediction.resolve()
    if not (run_dir / "manifest.json").is_file():
        raise ValueError(f"run manifest not found: {run_dir}")
    if not prediction.is_file() or not prediction.is_relative_to(run_dir):
        raise ValueError("prediction must be a file inside the run directory")
    target = run_dir / "execution.json"
    if target.exists():
        raise FileExistsError(target)
    record = {"record_version": "0.1", "arm": arm, "runtime": runtime, "model": model, "settings": settings,
              "prediction": prediction.relative_to(run_dir).as_posix(), "prediction_sha256": sha256(prediction),
              "latency_seconds": latency_seconds, "cost_usd": cost_usd}
    target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("prepare"); create.add_argument("--run-id", required=True); create.add_argument("--arm", choices=("baseline", "spec-guided", "unassigned"), default="unassigned")
    validate = commands.add_parser("check"); validate.add_argument("prediction", type=Path)
    record = commands.add_parser("record"); record.add_argument("run_dir", type=Path); record.add_argument("--arm", choices=("baseline", "spec-guided"), required=True); record.add_argument("--runtime", required=True); record.add_argument("--model", required=True); record.add_argument("--settings-json", required=True); record.add_argument("--prediction", type=Path, required=True); record.add_argument("--latency-seconds", type=float); record.add_argument("--cost-usd", type=float)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            print(prepare(args.run_id, args.arm)); return 0
        if args.command == "record":
            settings = json.loads(args.settings_json)
            if not isinstance(settings, dict): raise ValueError("settings JSON must be an object")
            print(record_execution(args.run_dir, arm=args.arm, runtime=args.runtime, model=args.model, settings=settings, prediction=args.prediction, latency_seconds=args.latency_seconds, cost_usd=args.cost_usd)); return 0
        problems = check(args.prediction)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr); return 2
    if problems:
        print("FAIL\n" + "\n".join(f"- {problem}" for problem in problems)); return 1
    print("PASS: represented scenario structure and reference bounds are valid; no claims are made about absent scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
