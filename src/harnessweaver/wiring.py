"""Load and validate the `wiring.yaml` contract between generated DeepAgents stages and a host."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from harnessweaver.spec import ValidationIssue

WIRING_FILENAME = "wiring.yaml"
SUPPORTED_WIRING_VERSIONS = ("0.1",)
ARTIFACTS_ROOT = PurePosixPath("/artifacts")


class WiringError(ValueError):
    """Raised with every problem found, so a generated bundle can be fixed in one pass."""

    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        super().__init__("; ".join(str(issue) for issue in issues))


@dataclass(frozen=True)
class WiringInput:
    port: str
    path: PurePosixPath


@dataclass(frozen=True)
class WiringStage:
    number: int
    dir: str
    handoff_prompt: str
    artifacts: tuple[str, ...]
    schemas: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class HumanGate:
    id: str
    after_stage: int


@dataclass(frozen=True)
class Wiring:
    root: Path
    version: str
    spec: Mapping[str, Any]
    inputs: tuple[WiringInput, ...]
    stages: tuple[WiringStage, ...]
    output_artifact: str
    output_schema: str | None
    human_gates: tuple[HumanGate, ...]


def _is_plain_json_name(value: Any) -> bool:
    return isinstance(value, str) and value.endswith(".json") and PurePosixPath(value).name == value and value != ".json"


def _is_bundle_relative(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def load_wiring(bundle: str | Path) -> Wiring:
    """Read `<bundle>/wiring.yaml` and return it only if the whole contract is consistent."""
    root = Path(bundle)
    source = root / WIRING_FILENAME
    try:
        document = yaml.safe_load(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise WiringError([ValidationIssue(str(source), f"cannot read: {exc.strerror or exc}")]) from exc
    except yaml.YAMLError as exc:
        raise WiringError([ValidationIssue(str(source), f"invalid YAML: {exc}")]) from exc
    if not isinstance(document, Mapping):
        raise WiringError([ValidationIssue(str(source), "document must be a mapping")])

    issues: list[ValidationIssue] = []

    def problem(location: str, message: str) -> None:
        issues.append(ValidationIssue(location, message))

    version = str(document.get("wiring_version", ""))
    if version not in SUPPORTED_WIRING_VERSIONS:
        problem("wiring_version", f"unsupported value {version!r}; supported: {', '.join(SUPPORTED_WIRING_VERSIONS)}")
    spec = document.get("spec") or {}
    if not isinstance(spec, Mapping) or not spec.get("id"):
        problem("spec", "must name the HarnessSpec it was generated from (id, version, path)")

    inputs: list[WiringInput] = []
    for index, entry in enumerate(document.get("inputs") or []):
        location = f"inputs[{index}]"
        port = entry.get("port") if isinstance(entry, Mapping) else None
        raw_path = entry.get("path") if isinstance(entry, Mapping) else None
        if not port:
            problem(location, "port is required")
        path = PurePosixPath(raw_path) if isinstance(raw_path, str) else None
        if path is None or path.parent != ARTIFACTS_ROOT or not _is_plain_json_name(path.name):
            problem(location, f"path must be a JSON file directly under {ARTIFACTS_ROOT}/, got {raw_path!r}")
        elif port:
            inputs.append(WiringInput(str(port), path))

    stages: list[WiringStage] = []
    raw_stages = document.get("stages") or []
    if not raw_stages:
        problem("stages", "at least one stage is required")
    numbers = [entry.get("number") for entry in raw_stages if isinstance(entry, Mapping)]
    if numbers != list(range(1, len(raw_stages) + 1)):
        problem("stages", f"stages must be numbered 1..N in order, got {numbers}")
    seen_artifacts: dict[str, int] = {name: 0 for name in (item.path.name for item in inputs)}
    seen_dirs: set[str] = set()
    for index, entry in enumerate(raw_stages):
        location = f"stages[{index}]"
        if not isinstance(entry, Mapping):
            problem(location, "must be a mapping")
            continue
        number = entry.get("number") if isinstance(entry.get("number"), int) else index + 1
        directory = entry.get("dir")
        if not _is_bundle_relative(directory) or len(PurePosixPath(directory).parts) != 1:
            problem(location, f"dir must be a stage directory name inside the bundle, got {directory!r}")
        elif directory in seen_dirs:
            problem(location, f"duplicate stage dir {directory!r}")
        else:
            seen_dirs.add(directory)
        prompt = entry.get("handoff_prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            problem(location, "handoff_prompt must be a non-empty sentence")
        artifacts = entry.get("artifacts") or []
        if not artifacts:
            problem(location, "artifacts must list at least one file the stage writes")
        for artifact in artifacts:
            if not _is_plain_json_name(artifact):
                problem(location, f"artifact {artifact!r} must be a plain JSON filename under {ARTIFACTS_ROOT}/")
            elif artifact in seen_artifacts:
                problem(location, f"duplicate artifact {artifact!r} (already declared by stage {seen_artifacts[artifact]})")
            else:
                seen_artifacts[artifact] = number
        schemas = entry.get("schemas") or {}
        if not isinstance(schemas, Mapping):
            problem(location, "schemas must map artifact filenames to bundle-relative schema paths")
            schemas = {}
        for artifact, schema_path in schemas.items():
            if artifact not in artifacts:
                problem(location, f"schema key {artifact!r} is not an artifact of stage {number}")
            if not _is_bundle_relative(schema_path):
                problem(location, f"schema path {schema_path!r} must be relative to the bundle")
        stages.append(WiringStage(number, str(directory), str(prompt or ""), tuple(str(a) for a in artifacts), dict(schemas)))

    output = document.get("output") or {}
    output_artifact = output.get("artifact") if isinstance(output, Mapping) else None
    output_schema = output.get("schema") if isinstance(output, Mapping) else None
    if output_artifact not in seen_artifacts or seen_artifacts.get(output_artifact) == 0:
        problem("output.artifact", f"must name an artifact written by a stage, got {output_artifact!r}")
    if output_schema is not None and not _is_bundle_relative(output_schema):
        problem("output.schema", f"must be relative to the bundle, got {output_schema!r}")

    gates: list[HumanGate] = []
    for index, entry in enumerate(document.get("human_gates") or []):
        after = entry.get("after_stage") if isinstance(entry, Mapping) else None
        if not isinstance(entry, Mapping) or not entry.get("id"):
            problem(f"human_gates[{index}]", "id is required")
        elif not isinstance(after, int) or not 1 <= after <= len(raw_stages):
            problem(f"human_gates[{index}]", f"after_stage must be a stage number 1..{len(raw_stages)}, got {after!r}")
        else:
            gates.append(HumanGate(str(entry["id"]), after))

    if issues:
        raise WiringError(issues)
    return Wiring(root, version, dict(spec), tuple(inputs), tuple(stages), str(output_artifact),
                  str(output_schema) if output_schema else None, tuple(gates))
