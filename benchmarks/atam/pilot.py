"""Small, model-free utilities for the ArchEval ATAM pilot protocol."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from harnessweaver._integrity import contains_secret_setting as _contains_secret_setting
from harnessweaver._integrity import sha256_bytes, sha256_file as sha256
from harnessweaver.runtime import AgentInteraction, ExecutionProfile, WorkflowStrategy

CONFIG_PATH = Path(__file__).with_name("pilot.json")
RUNS_DIR = Path(__file__).with_name("runs")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(reference: str) -> Path:
    return (CONFIG_PATH.parent / reference).resolve()


def prepare(run_id: str) -> Path:
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ValueError("run_id must be a single safe path component")
    config = read_json(CONFIG_PATH)
    case_path = resolve(config["source_case"])
    spec_path = resolve(config["harness_spec"])
    harness_assets = config["harness_assets"]
    harness_fingerprints = {asset: sha256(resolve(asset)) for asset in harness_assets}
    harness_digest = sha256_bytes(
        "".join(f"{asset}:{fingerprint}\n" for asset, fingerprint in sorted(harness_fingerprints.items())).encode("utf-8")
    )
    case_bytes = case_path.read_bytes()
    source = json.loads(case_bytes.decode("utf-8"))["ATAM_Evaluation"]
    if "evaluation_inputs" not in source or "ground_truth_outputs" not in source:
        raise ValueError("source case must contain separate evaluation_inputs and ground_truth_outputs")

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    input_path = run_dir / "evaluation_input.json"
    input_bytes = (
        json.dumps({"ATAM_Evaluation": {"evaluation_inputs": source["evaluation_inputs"]}}, indent=2) + "\n"
    ).encode("utf-8")
    input_path.write_bytes(input_bytes)
    manifest = {
        "manifest_version": "0.1",
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_id": config["case_id"],
        "arm": "unassigned",
        "status": "prepared",
        "source_case": config["source_case"],
        "source_case_sha256": sha256_bytes(case_bytes),
        "evaluation_input": "evaluation_input.json",
        "evaluation_input_sha256": sha256_bytes(input_bytes),
        "harness_spec": config["harness_spec"],
        "harness_spec_version": yaml.safe_load(spec_path.read_text(encoding="utf-8"))["spec_version"],
        "harness_spec_sha256": sha256(spec_path),
        "harness_assets_sha256": harness_digest,
        "harness_asset_fingerprints": harness_fingerprints,
        "notes": "See the write-once execution.json for arm/runtime/model/settings and measurements. Never add ground truth to this run directory.",
    }
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
    # Current typed reports place generated sections under evaluation_results; older
    # pilot candidates may put them directly under the ATAM envelope.
    generated = atam.get("evaluation_results", atam.get("generated", atam))
    if not isinstance(generated, dict):
        return ["generated ATAM result must be an object"]
    for section in config["required_sections"]:
        if section not in generated:
            problems.append(f"missing required section: {section}")
    semantic_state = generated.get("semantic_state")
    state_statuses = {
        "context_status": {"missing", "partial", "sufficient"},
        "driver_status": {"missing", "partial", "sufficient"},
        "architecture_evidence_status": {"missing", "partial", "sufficient"},
        "scenario_analysis_status": {"not_started", "partial", "reviewed"},
        "report_status": {"not_started", "draft", "reviewed"},
    }
    if not isinstance(semantic_state, dict):
        problems.append("semantic_state must be an object with evidence-backed methodology status")
    else:
        for field, allowed_statuses in state_statuses.items():
            assessment = semantic_state.get(field)
            if not isinstance(assessment, dict):
                problems.append(f"semantic_state.{field} must be an object")
                continue
            if assessment.get("value") not in allowed_statuses:
                problems.append(f"semantic_state.{field}.value must be one of {sorted(allowed_statuses)}")
            evidence = assessment.get("evidence")
            if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item.strip() for item in evidence):
                problems.append(f"semantic_state.{field}.evidence must contain at least one non-empty evidence item")
        gaps = semantic_state.get("gaps")
        if not isinstance(gaps, list):
            problems.append("semantic_state.gaps must be an array")
        else:
            for index, gap in enumerate(gaps):
                if not isinstance(gap, dict):
                    problems.append(f"semantic_state.gaps[{index}] must be an object")
                    continue
                for field in ("description", "affected_activity", "missing_evidence", "resolution_question"):
                    value = gap.get(field)
                    if not isinstance(value, str) or not value.strip():
                        problems.append(f"semantic_state.gaps[{index}].{field} is required")
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
    # Use the configured source case as the authority for generation inputs.
    # A prediction is untrusted, so its copy of evaluation_inputs cannot validate
    # its own scenario references.
    source_case = read_json(resolve(config["source_case"]))
    source_atam = source_case.get("ATAM_Evaluation", {})
    evaluation_inputs = source_atam.get("evaluation_inputs", {}) if isinstance(source_atam, dict) else {}
    raw_scenarios = evaluation_inputs.get("raw_candidate_scenarios", []) if isinstance(evaluation_inputs, dict) else []
    source_scenario_ids = {item.get("id") for item in raw_scenarios if isinstance(item, dict) and item.get("id")}
    source_scenario_texts = {
        " ".join(item["description"].split())
        for item in raw_scenarios
        if isinstance(item, dict) and isinstance(item.get("description"), str) and item["description"].strip()
    }
    reference_ids = source_scenario_ids
    reference_texts = source_scenario_texts
    if not reference_ids and not reference_texts:
        problems.append("configured ATAM source case has no raw candidate scenarios to validate against")
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
        if not ((scenario_id and scenario_id in reference_ids) or (scenario_text and scenario_text in reference_texts)):
            problems.append(f"analysis_records[{index}].scenario_reference must match a raw source scenario by id or text")
        findings = record.get("findings", {})
        if not isinstance(findings, dict):
            problems.append(f"analysis_records[{index}].findings must be an object")
            continue
        for field in config["required_finding_groups"]:
            group = findings.get(field)
            if not isinstance(group, list):
                problems.append(f"analysis_records[{index}].findings.{field} must be an array")
    return problems


def record_execution(
    run_dir: Path,
    arm: str,
    runtime: str,
    model: str,
    settings: dict[str, Any],
    prediction: Path | None,
    latency: float | None,
    cost: float | None,
    *,
    workflow_strategy: str,
    agent_interaction: str,
    status: str = "succeeded",
) -> Path:
    """Write an immutable execution record for successful, partial, or failed attempts."""
    run_dir = run_dir.resolve()
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"run manifest not found in {run_dir}")
    manifest = read_json(manifest_path)
    if status not in {"succeeded", "partial", "failed"}:
        raise ValueError("status must be succeeded, partial, or failed")
    profile = ExecutionProfile.from_values(workflow_strategy, agent_interaction)
    if _contains_secret_setting(settings):
        raise ValueError("settings must not contain credentials or secrets")
    if prediction is not None:
        prediction = prediction.resolve()
        if not prediction.is_file() or not prediction.is_relative_to(run_dir):
            raise ValueError("prediction must be a file inside the run directory")
    elif status == "succeeded":
        raise ValueError("a successful execution requires a prediction file")
    output = run_dir / "execution.json"
    if output.exists():
        raise FileExistsError(f"execution record already exists: {output}")
    record = {
        "record_version": "0.2",
        "arm": arm,
        "runtime": runtime,
        "model": model,
        "settings": settings,
        "workflow_strategy": profile.workflow_strategy.value,
        "agent_interaction": profile.agent_interaction.value,
        "harness_assets_sha256": manifest.get("harness_assets_sha256"),
        "status": status,
        "prediction": prediction.relative_to(run_dir).as_posix() if prediction else None,
        "prediction_sha256": sha256(prediction) if prediction else None,
        "output_path": prediction.relative_to(run_dir).as_posix() if prediction else None,
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
    record.add_argument("--settings-json", required=True, help="JSON object containing non-secret run settings")
    record.add_argument("--workflow-strategy", choices=tuple(item.value for item in WorkflowStrategy), required=True)
    record.add_argument("--agent-interaction", choices=tuple(item.value for item in AgentInteraction), required=True)
    record.add_argument("--status", choices=("succeeded", "partial", "failed"), default="succeeded")
    record.add_argument("--prediction", type=Path, help="prediction file inside the run directory (required for success)")
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
            print(record_execution(
                args.run_dir, args.arm, args.runtime, args.model, settings, args.prediction,
                args.latency_seconds, args.cost,
                workflow_strategy=args.workflow_strategy,
                agent_interaction=args.agent_interaction,
                status=args.status,
            ))
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
