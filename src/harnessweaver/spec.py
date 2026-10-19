"""Load and validate versioned HarnessSpec documents without a model runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import jsonschema
import yaml

from harnessweaver.runtime.contracts import SUPPORTED_PROFILES


SCHEMA_DIR = Path(__file__).resolve().parents[2] / "specs" / "harnessspec"
SUPPORTED_VERSIONS = ("0.1", "0.2")
SUPPORTED_ORCHESTRATION_PROFILES = {
    (strategy.value, interaction.value)
    for strategy, interaction in SUPPORTED_PROFILES
}


@dataclass(frozen=True)
class ValidationIssue:
    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}"


class SpecLoadError(ValueError):
    """A parse or spec-version error with a user-facing message."""


def load_spec(path: str | Path) -> dict[str, Any]:
    """Load JSON or YAML, returning the document without modifying its source."""
    source = Path(path)
    try:
        raw = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecLoadError(f"cannot read {source}: {exc.strerror or exc}") from exc
    try:
        document = json.loads(raw) if source.suffix.lower() == ".json" else yaml.safe_load(raw)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f"line {mark.line + 1}, column {mark.column + 1}: " if mark else ""
        raise SpecLoadError(f"{source}: {where}invalid JSON/YAML: {exc}") from exc
    if not isinstance(document, dict):
        raise SpecLoadError(f"{source}: document must be a mapping/object")
    version = document.get("spec_version")
    if version not in SUPPORTED_VERSIONS:
        raise SpecLoadError(
            f"{source}: unsupported spec_version {version!r}; supported versions are {', '.join(SUPPORTED_VERSIONS)}"
        )
    return document


def _schema_errors(document: dict[str, Any]) -> list[ValidationIssue]:
    version = document.get("spec_version")
    if version not in SUPPORTED_VERSIONS:
        return [ValidationIssue("spec_version", f"unsupported spec_version {version!r}; supported versions are {', '.join(SUPPORTED_VERSIONS)}")]
    schema_path = SCHEMA_DIR / f"v{version}.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    issues = []
    for error in validator.iter_errors(document):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        issues.append(ValidationIssue(location, error.message))
    return issues


def _unique_ids(document: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for section in ("sources", "roles", "stages", "artifacts", "verification", "human_gates"):
        seen: set[str] = set()
        for index, item in enumerate(document.get(section, [])):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            value = item["id"]
            if value in seen:
                issues.append(ValidationIssue(f"{section}[{index}].id", f"duplicate id {value!r}"))
            seen.add(value)
    semantic_state = document.get("semantic_state", {})
    if isinstance(semantic_state, dict):
        for section in ("assessments", "gaps"):
            seen: set[str] = set()
            for index, item in enumerate(semantic_state.get(section, [])):
                if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                    continue
                if item["id"] in seen:
                    issues.append(ValidationIssue(f"semantic_state.{section}[{index}].id", f"duplicate id {item['id']!r}"))
                seen.add(item["id"])
    roles = {item.get("id") for item in document.get("roles", []) if isinstance(item, dict)}
    artifacts = {item.get("id") for item in document.get("artifacts", []) if isinstance(item, dict)}
    for index, stage in enumerate(document.get("stages", [])):
        if isinstance(stage, dict) and stage.get("role") not in roles:
            issues.append(ValidationIssue(f"stages[{index}].role", f"unknown role {stage.get('role')!r}; add it to roles"))
    for index, gate in enumerate(document.get("human_gates", [])):
        if isinstance(gate, dict):
            for artifact in gate.get("required_artifacts", []):
                if artifact not in artifacts:
                    issues.append(ValidationIssue(f"human_gates[{index}].required_artifacts", f"unknown artifact {artifact!r}"))
    for index, check in enumerate(document.get("verification", [])):
        if isinstance(check, dict) and check.get("artifact") and check["artifact"] not in artifacts:
            issues.append(ValidationIssue(f"verification[{index}].artifact", f"unknown artifact {check['artifact']!r}"))
    return issues


def _orchestration_issues(document: dict[str, Any]) -> list[ValidationIssue]:
    """Reject declared strategy/interaction pairings the initial adapters cannot map."""
    orchestration = document.get("orchestration")
    if not isinstance(orchestration, dict):
        return []
    profile = (orchestration.get("workflow_strategy"), orchestration.get("agent_interaction"))
    if profile not in SUPPORTED_ORCHESTRATION_PROFILES:
        supported = ", ".join(f"{strategy}+{interaction}" for strategy, interaction in sorted(SUPPORTED_ORCHESTRATION_PROFILES))
        return [ValidationIssue("orchestration", f"unsupported workflow_strategy/agent_interaction combination {profile[0]!r}+{profile[1]!r}; supported combinations: {supported}")]
    return []


def _file_references(document: dict[str, Any], spec_path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    refs: list[tuple[str, str]] = []

    def add(section: str, index: int, key: str, value: Any) -> None:
        if isinstance(value, str):
            refs.append((f"{section}[{index}].{key}", value))

    for section in ("sources", "roles", "stages", "artifacts"):
        for index, item in enumerate(document.get(section, [])):
            if not isinstance(item, dict):
                continue
            keys = {"sources": ("ref",), "roles": ("skill_refs",), "stages": ("inputs",), "artifacts": ("ref", "schema_ref")}[section]
            for key in keys:
                value = item.get(key)
                if isinstance(value, list):
                    for nested_index, nested in enumerate(value):
                        add(section, index, f"{key}[{nested_index}]", nested)
                elif key == "schema_ref":
                    add(section, index, key, value)
                elif section in {"sources", "roles"}:
                    add(section, index, key, value)
                elif key == "ref" and section == "artifacts" and item.get("direction") == "input":
                    add(section, index, key, value)
    methodology = document.get("methodology", {})
    if isinstance(methodology, dict):
        for index, reference in enumerate(methodology.get("source_refs", [])):
            add("methodology", 0, f"source_refs[{index}]", reference)
    semantic_state = document.get("semantic_state", {})
    if isinstance(semantic_state, dict):
        for section in ("assessments", "gaps"):
            for index, item in enumerate(semantic_state.get(section, [])):
                if isinstance(item, dict):
                    for nested_index, reference in enumerate(item.get("evidence_refs", [])):
                        add(f"semantic_state.{section}", index, f"evidence_refs[{nested_index}]", reference)
    for location, reference in refs:
        parsed = urlparse(reference)
        if parsed.scheme:
            continue
        path_part = reference.split("#", 1)[0]
        candidate = (spec_path.parent / path_part).resolve()
        if not candidate.exists():
            issues.append(ValidationIssue(location, f"referenced file {path_part!r} does not exist (relative to {spec_path.parent})"))
    return issues


def validate_spec(document: dict[str, Any], spec_path: str | Path | None = None) -> list[ValidationIssue]:
    """Return actionable contract, cross-reference, and optional file-reference errors."""
    issues = _schema_errors(document)
    if any(issue.location == "spec_version" or issue.location.startswith("spec_version.") for issue in issues):
        return issues
    issues.extend(_unique_ids(document))
    issues.extend(_orchestration_issues(document))
    if spec_path is not None:
        issues.extend(_file_references(document, Path(spec_path).resolve()))
    return sorted(issues, key=lambda issue: (issue.location, issue.message))
