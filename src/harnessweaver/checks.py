"""Check an execution sandbox's outputs from outside the sandbox (`hw check`)."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from harnessweaver._integrity import sha256_file
from harnessweaver.hosts.deepagents import RECORD_FILENAME
from harnessweaver.sandbox import CLAUDE_REPORT_FILENAME, Pilot, SandboxError, load_sandbox, select

CHECK_FILE = "check.json"
LEAKAGE_MIN_LENGTH = 60
LEAKAGE_SCANNED = ("input", "bundle", "workspace", "output")
MAX_SCHEMA_ERRORS = 20
LEAKAGE_CHECK = "no-reference-leakage"
SCHEMA_CHECK = "schema"


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in _strings(nested)]
    if isinstance(value, list):
        return [item for nested in value for item in _strings(nested)]
    return []


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _selected_strings(case_path: Path, items: list[dict[str, Any]]) -> list[str]:
    result = []
    for item in items:
        if "value" in item:
            value = item["value"]
        else:
            value = select(json.loads((case_path.parent / item["from"]).read_text(encoding="utf-8")), item["select"])
        result.extend(_strings(value))
    return result


def find_report(sandbox: Path) -> Path | None:
    """The host record names the output; Claude runs are asked to write output/report.json."""
    record = sandbox / "output" / RECORD_FILENAME
    if record.is_file():
        output = json.loads(record.read_text(encoding="utf-8")).get("output")
        if output and Path(output).is_file():
            return Path(output)
    report = sandbox / "output" / CLAUDE_REPORT_FILENAME
    return report if report.is_file() else None


def check_leakage(sandbox: Path, case_path: Path, binding: dict[str, Any]) -> list[str]:
    """Distinctive evaluator-only strings must not appear anywhere inside the sandbox."""
    generation_text = {_normalize(text) for text in _selected_strings(case_path, binding.get("generation_inputs") or [])}
    distinctive: set[str] = set()
    for text in _selected_strings(case_path, binding.get("evaluator_only") or []):
        normalized = _normalize(text)
        # Strings that also appear in generation inputs are allowed to show up in outputs.
        if len(normalized) >= LEAKAGE_MIN_LENGTH and not any(normalized in generated for generated in generation_text):
            distinctive.add(normalized)
    problems = []
    for subdir in LEAKAGE_SCANNED:
        base = sandbox / subdir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            try:
                text = _normalize(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue
            hits = [snippet for snippet in distinctive if snippet in text]
            if hits:
                problems.append(f"{path.relative_to(sandbox)} contains {len(hits)} evaluator-only passage(s), e.g. {hits[0][:80]!r}")
    return problems


def check_schema(report: Path, schema_path: Path) -> list[str]:
    try:
        value = json.loads(report.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{report.name} is not valid JSON: {exc}"]
    validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    return [f"{'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}" for error in errors[:MAX_SCHEMA_ERRORS]] + (
        [f"... {len(errors) - MAX_SCHEMA_ERRORS} more"] if len(errors) > MAX_SCHEMA_ERRORS else [])


def _load_checker(pilot: Pilot, name: str):
    spec = pilot.config.get("checkers", {}).get(name)
    if not spec:
        raise SandboxError(f"pilot {pilot.name!r} defines no checker {name!r}")
    script = (pilot.root / spec["script"]).resolve()
    module_spec = importlib.util.spec_from_file_location(f"hw_checker_{name.replace('-', '_')}", script)
    if module_spec is None or module_spec.loader is None:
        raise SandboxError(f"checker {name!r}: cannot load {script}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return getattr(module, spec.get("function", "check"))


def run_checks(sandbox: str | Path) -> dict[str, Any]:
    """Run the case binding's checks plus the leakage check, and write check.json next to the sandbox record."""
    path, meta = load_sandbox(sandbox)
    if meta.get("kind") != "execution":
        raise SandboxError(f"{path} is not an execution sandbox")
    pilot = Pilot.load(meta["pilot_dir"])
    case_path, binding = pilot.case(meta["case"])
    report = find_report(path)
    results: dict[str, Any] = {LEAKAGE_CHECK: check_leakage(path, case_path, binding)}
    for name in binding.get("checks") or []:
        if report is None:
            results[name] = [f"no report found (expected output/{CLAUDE_REPORT_FILENAME} or the host record's output)"]
        elif name == SCHEMA_CHECK:
            results[name] = check_schema(report, pilot.path("report_schema"))
        else:
            results[name] = list(_load_checker(pilot, name)(report))
    summary = {
        "sandbox": meta["name"],
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "report": str(report.relative_to(path)) if report else None,
        "report_sha256": sha256_file(report) if report else None,
        "passed": all(not problems for problems in results.values()),
        "checks": {name: {"passed": not problems, "problems": problems} for name, problems in results.items()},
    }
    (path / CHECK_FILE).write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary
