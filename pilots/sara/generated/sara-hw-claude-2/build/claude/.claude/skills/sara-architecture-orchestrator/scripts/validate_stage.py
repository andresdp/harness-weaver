#!/usr/bin/env python3
"""Deterministic schema gate for the SARA harness.

Parses each artifact as JSON and validates it against its contract in
../references/contracts/. It checks shape only; cross-reference, coverage and
package-fidelity checks remain manual post-run reviews.

Usage:
  validate_stage.py --ports                 # input ports before Stage 1
  validate_stage.py --stage <stage_id>      # all outputs of one stage
  validate_stage.py --artifact <artifact>   # one artifact (producer read-back)
  [--dir _workspace/artifacts]

Exit codes: 0 all valid, 1 missing or invalid artifact, 2 validator unavailable or bad usage.
"""
import argparse
import json
import sys
from pathlib import Path

CONTRACTS = Path(__file__).resolve().parent.parent / "references" / "contracts"

PORTS = {
    "project_description": ("00_project_description.json", "project-description.port.schema.json"),
    "functional_requirements": ("00_functional_requirements.json", "functional-requirements.port.schema.json"),
}

ARTIFACTS = {
    "requirements_analysis": "requirements-analysis.schema.json",
    "quality_attributes": "quality-attributes.schema.json",
    "drivers": "drivers.schema.json",
    "pattern_candidates": "pattern-candidates.schema.json",
    "pattern_compatibility": "pattern-compatibility.schema.json",
    "alternatives": "alternatives.schema.json",
    "alternative_evaluation": "alternative-evaluation.schema.json",
    "trade_off_analysis": "trade-off-analysis.schema.json",
    "alternative_selection": "alternative-selection.schema.json",
    "adr": "adr.schema.json",
    "architecture_decision": "architecture-decision.schema.json",
}

STAGES = {
    "requirements_drivers": ["requirements_analysis", "quality_attributes", "drivers"],
    "solution_design": ["pattern_candidates", "pattern_compatibility", "alternatives"],
    "alternative_evaluation": ["alternative_evaluation", "trade_off_analysis", "alternative_selection"],
    "architecture_decision": ["adr", "architecture_decision"],
}


def check(path: Path, schema_file: str, validator_cls) -> list[str]:
    if not path.is_file():
        return [f"missing: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"not valid JSON: {path}: {exc}"]
    schema = json.loads((CONTRACTS / schema_file).read_text(encoding="utf-8"))
    errors = sorted(validator_cls(schema).iter_errors(data), key=lambda e: list(e.absolute_path))
    return [f"{path.name}: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors]


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ports", action="store_true")
    group.add_argument("--stage", choices=sorted(STAGES))
    group.add_argument("--artifact", choices=sorted(ARTIFACTS))
    parser.add_argument("--dir", default="_workspace/artifacts")
    args = parser.parse_args()

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("VALIDATION UNAVAILABLE: install jsonschema (pip install jsonschema). Do not continue the pipeline.")
        return 2

    root = Path(args.dir)
    if args.ports:
        targets = [(root / f, s) for f, s in PORTS.values()]
    elif args.stage:
        targets = [(root / f"{a}.json", ARTIFACTS[a]) for a in STAGES[args.stage]]
    else:
        targets = [(root / f"{args.artifact}.json", ARTIFACTS[args.artifact])]

    failures = []
    for path, schema_file in targets:
        problems = check(path, schema_file, Draft202012Validator)
        print(f"{'FAIL' if problems else 'PASS'} {path} ({schema_file})")
        failures += problems
    for line in failures:
        print(f"  - {line}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
