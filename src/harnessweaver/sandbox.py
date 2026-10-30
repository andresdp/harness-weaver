"""Create, collect and record generation and execution sandboxes (`hw sandbox ...`).

A sandbox is one directory per (pilot, arm or target, case, run). It holds only what the step
may use: read-only sources and skills for generation; a read-only bundle and generation-only
inputs for execution. Evaluator-only data is never copied in, and checks run from outside.
Sandboxes default to a sibling of the repository so a coding agent inside one cannot read
the repository (which holds reference outputs).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import yaml

from harnessweaver._integrity import sha256_file
from harnessweaver.bundles import TARGETS
from harnessweaver.wiring import WiringError, load_wiring

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPOSITORY_ROOT / "src/harnessweaver/skills"
BASELINE_DIR = REPOSITORY_ROOT / "baselines/revfactory-harness-v2.1.0-en"
LANGCHAIN_SKILLS_DIR = REPOSITORY_ROOT / ".agents/skills"
LANGCHAIN_SKILLS = ("deep-agents-core", "deep-agents-orchestration", "deep-agents-memory", "langgraph-human-in-the-loop")
EVIDENCE_DIR = REPOSITORY_ROOT / "docs/cain-2027/evidence"
ARMS = ("harnessweaver", "revfactory-en")
SANDBOX_FILE = "sandbox.yaml"
MANIFEST_FILE = "manifest.json"
CLAUDE_REPORT_FILENAME = "report.json"   # where Claude execution runs are asked to write the report
SPEC_PACKAGE_FILENAME = "spec-package.zip"
SPEC_PACKAGE_VERSION = "0.1"
MAX_SPEC_PACKAGE_BYTES = 128 * 1024 * 1024


class SandboxError(ValueError):
    """A sandbox cannot be created, collected or recorded as requested."""


def _new_sandbox_dir(root: Path | None, name: str) -> Path:
    """Create the sandbox directory, refusing locations inside the repository."""
    sandbox = ((root or default_root()) / name).resolve()
    if sandbox == REPOSITORY_ROOT or REPOSITORY_ROOT in sandbox.parents:
        # Its settings deny reads of the repository, which would also hide the sandbox itself.
        raise SandboxError(f"sandboxes must live outside the repository ({REPOSITORY_ROOT}); got {sandbox}")
    if sandbox.exists():
        raise SandboxError(f"sandbox already exists: {sandbox}")
    sandbox.mkdir(parents=True)
    return sandbox


def default_root() -> Path:
    """Sandboxes live outside the repository unless HW_SANDBOX_ROOT says otherwise."""
    configured = os.environ.get("HW_SANDBOX_ROOT")
    return Path(configured) if configured else REPOSITORY_ROOT.parent / f"{REPOSITORY_ROOT.name}-sandboxes"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y%m%dT%H%M%S")


def _git_commit() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(REPOSITORY_ROOT), "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _git_dirty(paths: list[Path]) -> bool | None:
    try:
        relative = [str(path.relative_to(REPOSITORY_ROOT)) for path in paths]
        output = subprocess.run(["git", "-C", str(REPOSITORY_ROOT), "status", "--porcelain", "--", *relative],
                                check=True, capture_output=True, text=True).stdout
        return bool(output.strip())
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def _digests(root: Path, subdirs: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for subdir in subdirs:
        base = root / subdir
        if base.is_file():
            result[subdir] = sha256_file(base)
            continue
        for path in sorted(base.rglob("*")) if base.is_dir() else []:
            if path.is_file():
                result[str(path.relative_to(root))] = sha256_file(path)
    return result


def _make_read_only(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def _write(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_yaml(path: Path, document: dict[str, Any]) -> None:
    _write(path, yaml.safe_dump(document, sort_keys=False, allow_unicode=True))


def _bundle_zip(bundle: Path, archive: Path) -> None:
    """Write a portable archive of a bundle, excluding caches and the archive itself."""
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(p for p in bundle.rglob("*") if p.is_file()):
            relative = path.relative_to(bundle)
            if any(part in {"__pycache__", ".DS_Store"} for part in relative.parts):
                continue
            info = zipfile.ZipInfo(f"{bundle.name}/{relative.as_posix()}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (path.stat().st_mode & 0xFFFF) << 16
            output.writestr(info, path.read_bytes())


def _write_spec_package(sources: Path, generated: Path, archive: Path, *, pilot: str,
                        answers: Path | None = None) -> dict[str, Any]:
    """Create a portable, hash-indexed package for later target materialization."""
    from harnessweaver.spec import load_spec, validate_spec

    specs = sorted(generated.glob("**/harnessspec*.yaml")) + sorted(generated.glob("**/harnessspec*.yml"))
    specs += sorted(generated.glob("**/harnessspec*.json"))
    specs = [p for p in specs if "build" not in p.relative_to(generated).parts and "record" not in p.relative_to(generated).parts]
    if len(specs) != 1:
        raise SandboxError(f"a reusable spec package needs exactly one HarnessSpec; found {len(specs)}")
    spec_path = specs[0]

    payload: dict[str, bytes] = {}
    for path in sorted(p for p in sources.rglob("*") if p.is_file()):
        if path.is_symlink():
            raise SandboxError(f"cannot package a symlinked source input: {path}")
        relative = path.relative_to(sources)
        if any(part in {"__pycache__", ".DS_Store"} for part in relative.parts):
            continue
        payload[f"inputs/sources/{relative.as_posix()}"] = path.read_bytes()
    for path in sorted(p for p in generated.rglob("*") if p.is_file()):
        if path.is_symlink():
            raise SandboxError(f"cannot package a symlinked generated source: {path}")
        relative = path.relative_to(generated)
        if relative.parts[0] in {"build", "record"} or path.name == "generation-record.json" or path.suffix == ".zip":
            continue
        if any(part in {"__pycache__", ".DS_Store"} for part in relative.parts):
            continue
        payload[f"generated/{relative.as_posix()}"] = path.read_bytes()
    if answers is not None and answers.is_file():
        payload["inputs/harness-answers.yaml"] = answers.read_bytes()

    spec_member = f"generated/{spec_path.relative_to(generated).as_posix()}"
    # Validate in the same layout used when the package is reopened: `generated/` and
    # `sources/` are siblings, so refs such as `../sources/host-adaptation.md` resolve.
    with tempfile.TemporaryDirectory(prefix="hw-spec-package-") as temporary:
        staging = Path(temporary)
        for name, data in payload.items():
            relative = PurePosixPath(name)
            if name.startswith("inputs/sources/"):
                staged_path = staging / "sources" / Path(*relative.parts[2:])
            elif name.startswith("generated/"):
                staged_path = staging / "generated" / Path(*relative.parts[1:])
            else:
                continue
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            staged_path.write_bytes(data)
        staged_spec = staging / spec_member
        try:
            issues = validate_spec(load_spec(staged_spec), staged_spec)
        except ValueError as exc:
            raise SandboxError(f"cannot package an unreadable HarnessSpec: {exc}") from exc
        if issues:
            raise SandboxError("cannot package an invalid HarnessSpec: " + "; ".join(map(str, issues)))
    manifest = {
        "package_version": SPEC_PACKAGE_VERSION,
        "pilot": pilot,
        "spec_path": spec_member,
        "spec_sha256": hashlib.sha256(payload[spec_member]).hexdigest(),
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payload.items())},
    }
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, data)
        info = zipfile.ZipInfo("manifest.json", date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        output.writestr(info, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def _read_spec_package(archive: Path) -> tuple[dict[str, Any], zipfile.ZipFile]:
    """Open and verify a spec package before extracting any of its paths."""
    try:
        package = zipfile.ZipFile(archive)
    except (OSError, zipfile.BadZipFile) as exc:
        raise SandboxError(f"cannot read spec package {archive}: {exc}") from exc
    names = package.namelist()
    if len(names) != len(set(names)):
        package.close()
        raise SandboxError("spec package contains duplicate paths")
    if "manifest.json" not in names:
        package.close()
        raise SandboxError("spec package is missing manifest.json")
    try:
        manifest = json.loads(package.read("manifest.json"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        package.close()
        raise SandboxError(f"invalid spec package manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("package_version") != SPEC_PACKAGE_VERSION:
        package.close()
        version = manifest.get("package_version") if isinstance(manifest, dict) else None
        raise SandboxError(f"unsupported spec package version: {version!r}")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(names) != set(files) | {"manifest.json"}:
        package.close()
        raise SandboxError("spec package file list does not match its manifest")
    if len(files) > 20000 or sum(package.getinfo(name).file_size for name in files) > MAX_SPEC_PACKAGE_BYTES:
        package.close()
        raise SandboxError("spec package exceeds the 20,000-file or 128 MiB expanded-size limit")
    for name, digest in files.items():
        if not isinstance(name, str) or not isinstance(digest, str):
            package.close()
            raise SandboxError("spec package manifest file entries must map string paths to SHA-256 strings")
        member = PurePosixPath(name)
        if member.is_absolute() or ".." in member.parts or "\\" in name or name.endswith("/"):
            package.close()
            raise SandboxError(f"unsafe path in spec package: {name!r}")
        if not (name.startswith("inputs/sources/") or name == "inputs/harness-answers.yaml" or name.startswith("generated/")):
            package.close()
            raise SandboxError(f"unsupported path in spec package: {name!r}")
        if (name.startswith("inputs/sources/") and len(member.parts) < 3) or (name.startswith("generated/") and len(member.parts) < 2):
            package.close()
            raise SandboxError(f"empty path in spec package: {name!r}")
        data = package.read(name)
        if hashlib.sha256(data).hexdigest() != digest:
            package.close()
            raise SandboxError(f"spec package integrity check failed for {name}")
    spec_name = manifest.get("spec_path")
    if not isinstance(spec_name, str) or not spec_name.startswith("generated/") or spec_name not in files:
        package.close()
        raise SandboxError("spec package manifest has an invalid spec_path")
    if hashlib.sha256(package.read(spec_name)).hexdigest() != manifest.get("spec_sha256"):
        package.close()
        raise SandboxError("spec package HarnessSpec digest does not match its manifest")
    return manifest, package


def _stage_spec_package(archive: Path, sandbox: Path, targets: list[str]) -> dict[str, Any]:
    from harnessweaver.spec import load_spec, validate_spec

    manifest, package = _read_spec_package(archive)
    try:
        for name in manifest["files"]:
            relative = PurePosixPath(name)
            if name.startswith("inputs/sources/"):
                destination = sandbox / "sources" / Path(*relative.parts[2:])
            elif name == "inputs/harness-answers.yaml":
                destination = sandbox / "harness-answers.yaml"
            elif name.startswith("generated/"):
                destination = sandbox / "generated" / Path(*relative.parts[1:])
            else:
                raise SandboxError(f"unsupported spec package member: {name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(package.read(name))
    finally:
        package.close()

    spec_path = sandbox / manifest["spec_path"]
    spec = load_spec(spec_path)
    issues = validate_spec(spec, spec_path)
    if issues:
        raise SandboxError("packaged HarnessSpec is invalid: " + "; ".join(map(str, issues)))
    references: list[str] = []
    for source in spec.get("sources", []):
        if isinstance(source, dict) and isinstance(source.get("ref"), str):
            references.append(source["ref"])
    methodology = spec.get("methodology")
    if isinstance(methodology, dict):
        references.extend(ref for ref in methodology.get("source_refs", []) if isinstance(ref, str))
    for role in spec.get("roles", []):
        if isinstance(role, dict):
            references.extend(ref for ref in role.get("skill_refs", []) if isinstance(ref, str))
    for artifact in spec.get("artifacts", []):
        if isinstance(artifact, dict) and isinstance(artifact.get("schema_ref"), str):
            references.append(artifact["schema_ref"])
    missing = []
    for reference in references:
        parsed = urlparse(reference)
        if parsed.scheme or reference.startswith("port:"):
            continue
        reference_path = Path(reference)
        resolved = (spec_path.parent / reference_path).resolve()
        if reference_path.is_absolute() or not resolved.is_relative_to(sandbox.resolve()) or not resolved.is_file():
            missing.append(reference)
    if missing:
        raise SandboxError("spec package is missing referenced source/contract files: " + ", ".join(sorted(set(missing))))
    answers_path = sandbox / "harness-answers.yaml"
    answers = yaml.safe_load(answers_path.read_text(encoding="utf-8")) if answers_path.is_file() else {"answers_version": "0.1"}
    if not isinstance(answers, dict):
        raise SandboxError("packaged harness-answers.yaml must contain a YAML mapping")
    g0 = answers.setdefault("G0", {})
    if not isinstance(g0, dict):
        raise SandboxError("packaged harness-answers.yaml G0 must be a mapping")
    g0.update({"sources": "sources/", "start_from": f"spec:{manifest['spec_path']}",
               "saved_spec": True, "output_root": "generated/"})
    prior_g4 = answers.get("G4") if isinstance(answers.get("G4"), dict) else {}
    answers["G4"] = {**prior_g4, "targets": targets}
    _write_yaml(answers_path, answers)
    return manifest


def _verify_staged_spec_package(sandbox: Path) -> None:
    package_copy = sandbox / "record/source-spec-package.zip"
    manifest, package = _read_spec_package(package_copy)
    try:
        expected_generated = {PurePosixPath(name).relative_to("generated").as_posix()
                              for name in manifest["files"] if name.startswith("generated/")}
        for name, expected in manifest["files"].items():
            if name == "inputs/harness-answers.yaml":
                continue  # G0 and G4 are deliberately specialized for this materialization.
            relative = PurePosixPath(name)
            if name.startswith("inputs/sources/"):
                actual_path = sandbox / "sources" / Path(*relative.parts[2:])
            elif name.startswith("generated/"):
                actual_path = sandbox / "generated" / Path(*relative.parts[1:])
            else:
                raise SandboxError(f"unsupported spec package member: {name}")
            if not actual_path.is_file() or sha256_file(actual_path) != expected:
                raise SandboxError(f"shared spec package file was changed during materialization: {actual_path}")
        generated_root = sandbox / "generated"
        actual_generated = {path.relative_to(generated_root).as_posix() for path in generated_root.rglob("*")
                            if path.is_file() and path.relative_to(generated_root).parts[0] not in {"build", "record"}
                            and path.name != "generation-record.json" and path.suffix != ".zip"
                            and not any(part in {"__pycache__", ".DS_Store"} for part in path.relative_to(generated_root).parts)}
        if actual_generated != expected_generated:
            raise SandboxError("materialization added or removed files outside generated/build/; review the shared spec package files")
    finally:
        package.close()


def _bundle_guide(target: str, bundle: Path, *, pilot: str, arm: str | None = None) -> str:
    if target == "generation-skills":
        contents = "HarnessWeaver's `harness` and `evolve` skills, their reference guides and templates, and any selected supporting LangChain skills."
        structure = "`.claude-plugin/` identifies the Claude Code plugin; `skills/` contains each skill and its references."
        run = ("From the generation sandbox, run `ISOLATION=settings ./run.sh` to start the configured Claude Code session. "
               "The sandbox launcher loads this plugin and the pilot prompt; use that launcher so outputs stay in `generated/`.")
        label = f"{arm or 'HarnessWeaver'} generation skills for {pilot}"
    elif target == "revfactory-skills":
        contents = "The English-translated RevFactory/Harness baseline plugin and its skills, included as the comparison generation arm."
        structure = "`.claude-plugin/` identifies the plugin; `skills/` contains the translated baseline skill files."
        run = "Run the generation sandbox's `ISOLATION=settings ./run.sh` launcher. It starts Claude Code with this plugin and the sandbox prompt."
        label = f"RevFactory English baseline skills for {pilot}"
    elif target == "claude":
        contents = "A generated Claude Code implementation of the domain workflow, including its orchestrator instructions, domain skills and agents, validation helpers, and materialization report when present."
        structure = "`CLAUDE.md` is the entry point; `.claude/agents/` and `.claude/skills/` hold runtime instructions; supporting contracts and scripts remain beside them."
        run = ("From the HarnessWeaver repository root, create an isolated execution sandbox, replacing the bundle path and case name:\n\n"
               f"```shell\nhw sandbox create-execution {pilot} --target claude --bundle <path-to-this-bundle> --case <case>\n```\n\n"
               "Then follow the printed runbook; "
               "for Claude OAuth, run `ISOLATION=settings ./run.sh` inside that execution sandbox.")
        label = f"{pilot} Claude Code runtime bundle"
    elif target == "deepagents":
        contents = "A generated DeepAgents runtime implementation with stage instructions, orchestration wiring, artifact contracts, and a materialization report."
        structure = "`wiring.yaml` maps the pipeline; `stage*/` contains each stage's agent instructions and skills; `contracts/` contains artifact schemas; `README.md` has domain details."
        run = ("From the HarnessWeaver repository root, create an isolated execution sandbox, replacing the bundle path, case name, and model:\n\n"
               f"```shell\nhw sandbox create-execution {pilot} --target deepagents --bundle <path-to-this-bundle> --case <case> --model <provider:model>\n```\n\n"
               "Configure the provider credentials in the environment or sandbox `.env`, then run `./run.sh` there. "
               "The execution runbook lists checks and recording steps.")
        label = f"{pilot} DeepAgents runtime bundle"
    else:
        raise SandboxError(f"unknown bundle guide target: {target}")
    return (f"# {label}\n\n"
            f"This folder is a portable **{target}** bundle generated for the `{pilot}` pilot.\n\n"
            f"## What it contains\n\n{contents}\n\n"
            f"## Structure\n\n{structure}\n\n"
            f"## How to run it\n\n{run}\n\n"
            "The ZIP next to this bundle folder contains this guide and the complete bundle tree. Keep the guide with the files when moving or sharing the bundle.\n")


@dataclass(frozen=True)
class Pilot:
    """A pilot directory and its `pilot.yaml` sandbox configuration."""

    root: Path
    config: dict[str, Any]

    @classmethod
    def load(cls, pilot: str | Path) -> "Pilot":
        root = Path(pilot)
        if not (root / "pilot.yaml").is_file():
            candidate = REPOSITORY_ROOT / "pilots" / str(pilot)
            root = candidate if (candidate / "pilot.yaml").is_file() else root
        config_path = root / "pilot.yaml"
        if not config_path.is_file():
            raise SandboxError(f"no pilot.yaml found for pilot {pilot!r}")
        return cls(root.resolve(), yaml.safe_load(config_path.read_text(encoding="utf-8")))

    @property
    def name(self) -> str:
        return str(self.config["pilot"])

    def path(self, key: str) -> Path:
        return (self.root / self.config[key]).resolve()

    def prompt(self, *keys: str) -> str:
        node: Any = self.config.get("prompts", {})
        traversed: list[str] = []
        for key in keys:
            traversed.append(key)
            if not isinstance(node, dict) or key not in node:
                prompt_key = ".".join(traversed)
                raise SandboxError(
                    f"pilot {self.name!r} does not configure prompts.{prompt_key} in "
                    f"{self.root / 'pilot.yaml'}; add a prompt file and reference it under "
                    f"prompts.{prompt_key}"
                )
            node = node[key]
        if not isinstance(node, str) or not node.strip():
            prompt_key = ".".join(keys)
            raise SandboxError(
                f"pilot {self.name!r} has an invalid prompts.{prompt_key} entry in "
                f"{self.root / 'pilot.yaml'}; expected a path to a prompt file"
            )
        prompt_path = (self.root / node).resolve()
        if not prompt_path.is_file():
            prompt_key = ".".join(keys)
            raise SandboxError(
                f"pilot {self.name!r} configures prompts.{prompt_key} as {node!r}, "
                f"but the prompt file does not exist: {prompt_path}"
            )
        return prompt_path.read_text(encoding="utf-8")

    def claude_allowed_bash(self) -> list[str]:
        """Return the Claude Bash allowlist explicitly configured for this pilot."""
        execution = self.config.get("execution", {})
        claude = execution.get("claude", {}) if isinstance(execution, dict) else None
        if not isinstance(claude, dict):
            raise SandboxError(
                f"pilot {self.name!r} has invalid execution.claude settings in "
                f"{self.root / 'pilot.yaml'}; expected a mapping"
            )
        commands = claude.get("allow_bash", [])
        if (not isinstance(commands, list)
                or any(not isinstance(command, str) or not command.strip() for command in commands)):
            raise SandboxError(
                f"pilot {self.name!r} has invalid execution.claude.allow_bash in "
                f"{self.root / 'pilot.yaml'}; expected a list of non-empty command patterns"
            )
        return commands

    def case(self, name: str) -> tuple[Path, dict[str, Any]]:
        path = self.path("cases") / f"{name}.yaml"
        if not path.is_file():
            raise SandboxError(f"case binding not found: {path}")
        return path, yaml.safe_load(path.read_text(encoding="utf-8"))


def select(document: Any, pointer: str) -> Any:
    """Follow a dotted selector such as `ATAM_Evaluation.evaluation_inputs`."""
    node = document
    for part in pointer.split("."):
        if not isinstance(node, dict) or part not in node:
            raise SandboxError(f"selector {pointer!r} does not resolve (missing {part!r})")
        node = node[part]
    return node


def _envelope(pointer: str, value: Any) -> Any:
    """Re-wrap a selected value in its original key path so consumers see the familiar shape."""
    for part in reversed(pointer.split(".")):
        value = {part: value}
    return value


def _deepagents_input_map(bundle: Path, generation_inputs: list[tuple[dict[str, Any], Any]]) -> list[tuple[str, Any]]:
    """Map case generation inputs to the input port filenames required by a DeepAgents bundle."""
    try:
        ports = load_wiring(bundle).inputs
    except WiringError as exc:
        raise SandboxError(f"cannot map case inputs to DeepAgents ports: {exc}") from exc

    if len(ports) != len(generation_inputs):
        raise SandboxError(
            f"DeepAgents bundle declares {len(ports)} input port(s), but the case provides "
            f"{len(generation_inputs)} generation input(s); add explicit port mappings to the case or align the bundle."
        )

    assignments: dict[str, int] = {}
    used: set[int] = set()
    for port in ports:
        matches = []
        for index, (item, _) in enumerate(generation_inputs):
            selectors = [item.get("envelope"), item.get("select")]
            selector_names = {str(selector).rsplit(".", 1)[-1] for selector in selectors if selector}
            aliases = {str(item.get("id", "")), str(item.get("port", "")), *selector_names}
            if port.port in aliases:
                matches.append(index)
        if len(matches) > 1:
            raise SandboxError(f"DeepAgents input port {port.port!r} matches multiple case generation inputs; specify a unique port mapping.")
        if matches:
            index = matches[0]
            if index in used:
                raise SandboxError(f"case generation input {generation_inputs[index][0].get('id')!r} maps to multiple DeepAgents ports.")
            assignments[port.port] = index
            used.add(index)

    unmatched_ports = [port.port for port in ports if port.port not in assignments]
    unmatched_inputs = [index for index in range(len(generation_inputs)) if index not in used]
    if len(unmatched_ports) == 1 and len(unmatched_inputs) == 1:
        assignments[unmatched_ports[0]] = unmatched_inputs[0]
    elif unmatched_ports or unmatched_inputs:
        raise SandboxError(
            "could not map every case generation input to a DeepAgents input port; "
            f"unmatched ports: {unmatched_ports}, unmatched case input ids: "
            f"{[generation_inputs[index][0].get('id') for index in unmatched_inputs]}. "
            "Set a matching `port` on each case generation input or align its id/envelope with the bundle port."
        )

    return [(port.port, generation_inputs[assignments[port.port]][1]) for port in ports]


def _claude_settings(writable: list[Path], readable: list[Path], denied_reads: list[Path], allow_bash: list[str]) -> str:
    """Permission rules for a sandboxed Claude Code session (absolute `//` paths)."""
    def rule(tool: str, path: Path) -> str:
        return f"{tool}(/{path.as_posix()}/**)"

    settings = {
        "permissions": {
            "allow": [*(rule("Read", path) for path in readable), *(rule(tool, path) for path in writable for tool in ("Edit", "Write")),
                      *(f"Bash({command})" for command in allow_bash)],
            "deny": [*(rule("Read", path) for path in denied_reads), "WebFetch", "WebSearch"],
        }
    }
    return json.dumps(settings, indent=2) + "\n"


def _build_skills_plugin(arm: str, destination: Path, include_langchain: bool) -> dict[str, Any]:
    """Wrap an arm's skills as a Claude Code plugin so every arm is installed the same way."""
    notes: dict[str, Any] = {"arm": arm, "langchain_skills": []}
    if arm == "harnessweaver":
        _write(destination / ".claude-plugin/plugin.json", json.dumps({
            "name": "harnessweaver",
            "version": "0.1.0-dev",
            "description": "HarnessWeaver generation skills: harness (design and materialize) and evolve (revise).",
            "license": "Apache-2.0",
        }, indent=2) + "\n")
        for skill in ("harness", "evolve"):
            shutil.copytree(SKILLS_DIR / skill, destination / "skills" / skill)
        if include_langchain:
            for skill in LANGCHAIN_SKILLS:
                source = LANGCHAIN_SKILLS_DIR / skill
                if source.is_dir():
                    shutil.copytree(source, destination / "skills" / skill)
                    notes["langchain_skills"].append(skill)
            notes["langchain_skills_missing"] = sorted(set(LANGCHAIN_SKILLS) - set(notes["langchain_skills"]))
        notes["source"] = str(SKILLS_DIR.relative_to(REPOSITORY_ROOT))
        notes["source_dirty"] = _git_dirty([SKILLS_DIR])
    elif arm == "revfactory-en":
        _verify_baseline()
        shutil.copytree(BASELINE_DIR / ".claude-plugin", destination / ".claude-plugin")
        shutil.copytree(BASELINE_DIR / "skills", destination / "skills")
        notes["source"] = str(BASELINE_DIR.relative_to(REPOSITORY_ROOT))
    else:
        raise SandboxError(f"unknown arm {arm!r}; expected one of {', '.join(ARMS)}")
    return notes


def _verify_baseline() -> None:
    """The baseline must match its recorded digests; an edited baseline invalidates comparisons."""
    for line in (BASELINE_DIR / "TRANSLATION.sha256").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split(maxsplit=1)
        if sha256_file(BASELINE_DIR / relative) != expected:
            raise SandboxError(f"baseline file changed since translation was recorded: {relative}")


GENERATION_RUN_SH = """#!/usr/bin/env bash
# Launch the generation session for this sandbox. See RUNBOOK.md.
set -euo pipefail
cd "$(dirname "$0")"
SESSION_ID="{session_id}"
MODEL="${{MODEL:-{model}}}"
ISOLATION="${{ISOLATION:-bare}}"   # bare: skip user hooks/settings/CLAUDE.md (needs ANTHROPIC_API_KEY); settings: project settings only
args=(--plugin-dir ./skills-plugin --settings ./claude-settings.json --session-id "$SESSION_ID")
if [ -n "$MODEL" ]; then args+=(--model "$MODEL"); fi
if [ "$ISOLATION" = "bare" ]; then args=(--bare "${{args[@]}}"); else args+=(--setting-sources project); fi
mkdir -p record
claude --version > record/claude-version.txt 2>&1 || true
printf '%s\\n' "$ISOLATION" > record/isolation.txt
printf '%s\\n' "${{MODEL:-<claude default>}}" > record/model-requested.txt
date -u +%Y-%m-%dT%H:%M:%SZ > record/started-at.txt
echo "Starting Claude Code generation. Generated files belong under: $PWD/generated"
echo "Session ID: $SESSION_ID"
if claude "${{args[@]}}" "$(cat prompt.md)"; then
  status=0
else
  status=$?
fi
date -u +%Y-%m-%dT%H:%M:%SZ > record/finished-at.txt
printf '%s\\n' "$status" > record/exit-code.txt
if [ "$status" -eq 0 ]; then
  printf '%s\\n' completed > record/status.txt
  echo "Generation session finished. Review generated/ and this sandbox's RUNBOOK.md."
  printf '\\033[32mNext: from the repository root, run hw sandbox collect "%s" --label <unique-label>\\033[0m\\n' "$PWD"
else
  printf '%s\\n' failed > record/status.txt
  echo "Claude exited with status $status. Check authentication/usage limits and resume the recorded session if needed."
  echo "Session ID: $SESSION_ID; sandbox: $PWD; started/finished and exit status are in record/."
fi
exit "$status"
"""

GENERATION_RUNBOOK = """# Generation sandbox: {name}

Arm: **{arm}**. Pilot: **{pilot}**. Created {created} from repository commit `{commit}`.
Runtime target(s): **{targets_label}**.

You run this session; Claude Code with the arm's skills generates the harness. Everything runs in English.

## Before you start

- `cd {root}`
- Activate the Python environment where HarnessWeaver is installed before running collection commands.
- With the default `ISOLATION=bare`, export `ANTHROPIC_API_KEY` (bare mode ignores OAuth login). It keeps your global hooks, plugins and `CLAUDE.md` out of the session. Use `ISOLATION=settings` to keep OAuth; it loads only this sandbox's settings, but your user-level `CLAUDE.md` may still load. Note which you used.
- Optionally set `MODEL` (default: {model_label}). Use the same model for every arm you compare.

## Run

```shell
ISOLATION=settings ./run.sh    # subscription OAuth; use bare only with ANTHROPIC_API_KEY
```

The session starts with the request in `prompt.md`{answers_note}. {spec_mode_note} Answer any remaining target-specific questions. Writes are allowed only under `generated/`. Reads of the repository are denied.

When the skill has finished, ask it to confirm where it wrote each file, then exit the session.

The launcher prints the session ID and records `record/started-at.txt`, `record/finished-at.txt`, `record/exit-code.txt`, and `record/status.txt`, including when Claude exits with an error.

## Afterwards

From the repository root (with your HarnessWeaver Python environment active):

```shell
hw sandbox collect {root} --label <label>
```

`collect` copies `generated/` into `pilots/{pilot}/generated/<label>/`, copies the session transcript (`~/.claude/projects/*/{session_id}.jsonl`) into the sandbox `record/`, writes `generation-record.json`, checks any runtime bundles, and creates `spec-package.zip` when one valid HarnessSpec is present. That package can be used to materialize another runtime later without harvesting the workflow again.
"""


def _write_target_answers(path: Path, targets: list[str], *, spec_path: str | None = None) -> None:
    if path.is_file():
        answers = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(answers, dict):
            raise SandboxError("harness-answers.yaml must contain a YAML mapping")
    else:
        answers = {"answers_version": "0.1"}
    answers["G4"] = {**(answers.get("G4") if isinstance(answers.get("G4"), dict) else {}), "targets": targets}
    if spec_path:
        g0 = answers.setdefault("G0", {})
        if not isinstance(g0, dict):
            raise SandboxError("harness-answers.yaml G0 must be a mapping")
        g0.update({"sources": "sources/", "start_from": f"spec:{spec_path}",
                   "saved_spec": True, "output_root": "generated/"})
    _write_yaml(path, answers)


def create_generation_sandbox(pilot_name: str | Path, arm: str, *, root: Path | None = None, model: str = "",
                              answers: Path | None = None, include_langchain_skills: bool = True,
                              targets: list[str] | None = None, from_package: Path | None = None) -> Path:
    """Create a sandbox in which the user runs a Claude Code generation session for one arm."""
    if arm not in ARMS:
        raise SandboxError(f"unknown arm {arm!r}; expected one of {', '.join(ARMS)}")
    if answers is not None and arm != "harnessweaver":
        raise SandboxError("harness-answers.yaml is a HarnessWeaver-skill feature; the baseline arm must be answered live")
    if targets is not None:
        if arm != "harnessweaver":
            raise SandboxError("runtime target selection applies only to the HarnessWeaver generation arm")
        if not targets or len(targets) != len(set(targets)) or set(targets) - set(TARGETS):
            raise SandboxError(f"select one or more unique targets from: {', '.join(TARGETS)}")
    if from_package is not None and (arm != "harnessweaver" or not targets):
        raise SandboxError("spec-package materialization requires the HarnessWeaver arm and at least one --target")
    pilot = Pilot.load(pilot_name)
    baseline_generation_prompt = pilot.prompt("baseline_generation") if arm == "revfactory-en" and from_package is None else None
    created = _now()
    name = f"gen-{pilot.name}-{arm}-{_stamp(created)}"
    sandbox = _new_sandbox_dir(root, name)

    package_manifest = None
    if from_package is None:
        shutil.copytree(pilot.path("sources"), sandbox / "sources")
    else:
        package_manifest = _stage_spec_package(Path(from_package), sandbox, targets or [])
    plugin_notes = _build_skills_plugin(arm, sandbox / "skills-plugin", include_langchain_skills)
    guide_target = "generation-skills" if arm == "harnessweaver" else "revfactory-skills"
    _write(sandbox / "skills-plugin/BUNDLE-GUIDE.md",
           _bundle_guide(guide_target, sandbox / "skills-plugin", pilot=pilot.name, arm=arm))
    _bundle_zip(sandbox / "skills-plugin", sandbox / "skills-plugin.zip")
    plugin_notes["guide"] = "BUNDLE-GUIDE.md"
    plugin_notes["archive"] = "skills-plugin.zip"
    (sandbox / "generated").mkdir(exist_ok=True)
    (sandbox / "record").mkdir()
    if from_package is not None:
        shutil.copyfile(from_package, sandbox / "record/source-spec-package.zip")
    if from_package is None and arm == "revfactory-en":
        generation_prompt = baseline_generation_prompt
    elif from_package is None:
        generation_prompt = pilot.prompt("generation")
    else:
        generation_prompt = (SKILLS_DIR / "harness/references/spec-package-materialization.md").read_text(encoding="utf-8")
        generation_prompt += f"\n\nProject: {pilot.name}. Spec package: {from_package}. Selected target(s): {', '.join(targets or [])}.\n"
    if targets:
        generation_prompt += (
            "\n\nAuthoritative runtime selection for this sandbox: " + ", ".join(targets) + ".\n"
            "Materialize exactly these selected target(s). If the pilot prompt or an imported answer file names a different target list, "
            "the selection printed here is authoritative; preserve the pilot's domain and methodology requirements.\n"
        )
    if arm == "revfactory-en":
        generation_prompt += (
            "\n\nBaseline comparison scope and implementation boundary:\n"
            "- Generate only a Claude Code-native harness using this arm's documented forms: agents, skills, "
            "CLAUDE.md, and its orchestrator skill. For fixed sequences, use the documented Claude Code Workflow "
            "pattern in the orchestrator skill when supported.\n"
            "- Do not create standalone application/runtime code or executable scripts, such as a project-specific "
            "Python runner, ledger/gate engine, artifact projection framework, or validator framework. Keep the "
            "harness behavior in the baseline's agents, skills, and orchestrator. Declarative artifacts such as "
            "JSON Schemas and static references may accompany them. If a requirement appears to need external "
            "runtime enforcement, explain the limitation and record the requirement as unsupported or approximated "
            "instead of adding custom code.\n"
            "- If the supplied intent or other source mentions DeepAgents or another runtime, treat that as "
            "context for the overall project and do not generate, plan, or ask whether to generate it in this "
            "baseline session. The DeepAgents target is handled separately by HarnessWeaver.\n"
        )
    _write(sandbox / "prompt.md", generation_prompt)
    if answers is not None:
        shutil.copyfile(answers, sandbox / "harness-answers.yaml")
    if targets:
        _write_target_answers(sandbox / "harness-answers.yaml", targets,
                              spec_path=package_manifest["spec_path"] if package_manifest else None)
    _make_read_only(sandbox / "sources")
    _make_read_only(sandbox / "skills-plugin")

    session_id = str(uuid4())
    commit = _git_commit()
    _write(sandbox / "claude-settings.json", _claude_settings(
        writable=[sandbox / "generated"],
        readable=[sandbox],
        denied_reads=[REPOSITORY_ROOT],
        allow_bash=["hw validate:*", "conda run -n harness hw validate:*", "hw check-bundle:*",
                    "conda run -n harness hw check-bundle:*", "mkdir -p generated/*", "ls:*"],
    ))
    _write(sandbox / "run.sh", GENERATION_RUN_SH.format(session_id=session_id, model=model), executable=True)
    _write(sandbox / "RUNBOOK.md", GENERATION_RUNBOOK.format(
        name=name, arm=arm, pilot=pilot.name, created=created.isoformat(timespec="seconds"),
        commit=commit or "unknown", root=sandbox, model_label=model or "the Claude Code default",
        session_id=session_id,
        targets_label=", ".join(targets) if targets else "selected interactively at G4",
        spec_mode_note=("This is a target-only regeneration from the saved, hash-checked spec package; the shared design files are verified unchanged at collection."
                        if package_manifest else "The source-generation request and any answered design gates define the shared HarnessSpec."),
        answers_note=" and `harness-answers.yaml` (pre-recorded gate answers; the skill asks only what it leaves open)"
        if answers is not None or targets else "",
    ))
    _write_yaml(sandbox / SANDBOX_FILE, {
        "kind": "generation",
        "name": name,
        "pilot": pilot.name,
        "pilot_dir": str(pilot.root),
        "arm": arm,
        "created_at": created.isoformat(timespec="seconds"),
        "repository_commit": commit,
        "sources_dirty": _git_dirty([pilot.path("sources")]),
        "session_id": session_id,
        "model_requested": model or None,
        "skills": plugin_notes,
        "answers_file": (sandbox / "harness-answers.yaml").is_file(),
        "targets": targets,
        "spec_package": {"path": str(from_package.resolve()), "spec_path": package_manifest["spec_path"],
                         "spec_sha256": package_manifest["spec_sha256"],
                         "package_sha256": sha256_file(from_package)} if package_manifest else None,
    })
    _write(sandbox / MANIFEST_FILE, json.dumps(
        {"inputs": _digests(sandbox, ["sources", "generated", "skills-plugin", "prompt.md", "harness-answers.yaml", "claude-settings.json"])},
        indent=2) + "\n")
    return sandbox


EXECUTION_RUN_SH = {
    "claude": """#!/usr/bin/env bash
# Run the generated Claude Code harness headlessly on this sandbox's case. See RUNBOOK.md.
set -euo pipefail
cd "$(dirname "$0")"
SESSION_ID="{session_id}"
MODEL="${{MODEL:-{model}}}"
ISOLATION="${{ISOLATION:-bare}}"
HW_PYTHON="${{HW_PYTHON:-python}}"
read -r -a python_cmd <<< "$HW_PYTHON"
if [ -f record/started-at.txt ]; then
  echo "This execution sandbox already has a run attempt. Create a new execution sandbox for a clean run; reusing this one can mix stale artifacts." >&2
  exit 10
fi
args=(-p --session-id "$SESSION_ID" --settings ../claude-settings.json --add-dir ../input --add-dir ../output
      --output-format stream-json --verbose)
if [ -n "$MODEL" ]; then args+=(--model "$MODEL"); fi
if [ "$ISOLATION" = "bare" ]; then
  args=(--bare "${{args[@]}}")
  # Bare mode skips CLAUDE.md discovery; pass the harness pointer explicitly.
  if [ -f workspace/CLAUDE.md ]; then args+=(--append-system-prompt-file CLAUDE.md); fi
else
  args+=(--setting-sources project)
fi
repair_args=(-p --resume "$SESSION_ID" --settings ../claude-settings.json --add-dir ../input --add-dir ../output
             --output-format stream-json --verbose)
if [ -n "$MODEL" ]; then repair_args+=(--model "$MODEL"); fi
if [ "$ISOLATION" = "bare" ]; then
  repair_args=(--bare "${{repair_args[@]}}")
  if [ -f workspace/CLAUDE.md ]; then repair_args+=(--append-system-prompt-file CLAUDE.md); fi
else
  repair_args+=(--setting-sources project)
fi
mkdir -p record output
claude --version > record/claude-version.txt 2>&1 || true
printf '%s\\n' "$ISOLATION" > record/isolation.txt
date -u +%Y-%m-%dT%H:%M:%SZ > record/started-at.txt
echo "Starting Claude Code execution on case {case}; workspace: $PWD/workspace"
echo "Claude progress will appear here; raw stream: $PWD/output/transcript.jsonl"
if (cd workspace && claude "${{args[@]}}" "$(cat ../prompt.md)") | "${{python_cmd[@]}}" stream_claude.py --transcript output/transcript.jsonl; then
  status=0
else
  status=$?
fi
if [ "$status" -eq 0 ] && [ -f output/{report_filename} ]; then
  echo "Checking report JSON/schema from outside the Claude sandbox…"
  if "${{python_cmd[@]}}" -m harnessweaver.cli check "$PWD" --repair-prompt output/repair-prompt.md; then
    check_status=0
  else
    check_status=$?
  fi
  if [ "$check_status" -gt 1 ]; then
    status=$check_status
  fi
  if [ "$status" -eq 0 ] && [ -f output/repair-prompt.md ]; then
    cp check.json record/check-before-repair.json
    echo "The report has a structural JSON/schema issue. Asking Claude for one bounded repair; evaluator findings are not sent to the model."
    if (cd workspace && claude "${{repair_args[@]}}" "$(cat ../output/repair-prompt.md)") | "${{python_cmd[@]}}" stream_claude.py --transcript output/transcript.jsonl --append; then
      repair_status=0
    else
      repair_status=$?
    fi
    if [ "$repair_status" -eq 0 ]; then
      if "${{python_cmd[@]}}" -m harnessweaver.cli check "$PWD"; then
        :
      else
        final_check_status=$?
        if [ "$final_check_status" -gt 1 ]; then status=$final_check_status; fi
      fi
    else
      status=$repair_status
    fi
  fi
fi
date -u +%Y-%m-%dT%H:%M:%SZ > record/finished-at.txt
printf '%s\\n' "$status" > record/exit-code.txt
if [ "$status" -eq 0 ] && [ -f output/{report_filename} ]; then
  printf '%s\\n' completed > record/status.txt
  echo "Execution finished. Report: $PWD/output/{report_filename}"
  printf '\\033[32mNext: hw check "%s"\\033[0m\\n' "$PWD"
else
  if [ "$status" -eq 0 ]; then status=4; printf '%s\\n' "$status" > record/exit-code.txt; fi
  printf '%s\\n' failed > record/status.txt
  echo "Execution stopped with status $status. Review output/transcript.jsonl and record/."
  echo "Run hw check '$PWD' to see which outputs are present."
fi
exit "$status"
""",
    "deepagents": """#!/usr/bin/env bash
# Run the generated DeepAgents stages with the HarnessWeaver stage host. See RUNBOOK.md.
set -euo pipefail
cd "$(dirname "$0")"
clean=0
if [ "${{1:-}}" = "--clean" ]; then
  clean=1
  shift
fi
if [ -f record/started-at.txt ] && [ "$clean" -ne 1 ]; then
  echo "This execution sandbox already has a run attempt. Use ./run.sh --clean to rerun the full pipeline here, or create a fresh sandbox." >&2
  exit 10
fi
if [ "$clean" -eq 1 ]; then
  echo "Cleaning prior workspace, outputs, and run records; restarting all stages from stage 1."
  rm -rf workspace output record check.json
fi
MODEL="${{MODEL:-{model}}}"
TIMEOUT="${{TIMEOUT:-180}}"
HW_PYTHON="${{HW_PYTHON:-python}}"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
mkdir -p record output
date -u +%Y-%m-%dT%H:%M:%SZ > record/started-at.txt
echo "Starting DeepAgents execution on model $MODEL; workspace: $PWD/workspace"
read -r -a python_cmd <<< "$HW_PYTHON"
if "${{python_cmd[@]}}" -m harnessweaver.hosts.deepagents --bundle bundle --input input --workspace workspace --out output \\
  --model "$MODEL" --timeout "$TIMEOUT" "$@"
then status=0; else status=$?; fi
date -u +%Y-%m-%dT%H:%M:%SZ > record/finished-at.txt
printf '%s\\n' "$status" > record/exit-code.txt
if [ "$status" -eq 0 ]; then
  printf '%s\\n' completed > record/status.txt
  echo "Execution finished. Review output/ and record/host-record.json."
  printf '\\033[32mNext: hw check "%s"\\033[0m\\n' "$PWD"
else
  printf '%s\\n' failed > record/status.txt
  echo "DeepAgents exited with status $status. Review record/host-record.json and output/; sandbox: $PWD"
fi
exit "$status"
""",
}

EXECUTION_RUNBOOK = """# Execution sandbox: {name}

Target: **{target}**. Pilot: **{pilot}**. Case: **{case}**. Bundle: `{bundle}`.

`input/` holds only the case's generation inputs ({inputs}). Evaluator-only data was not copied.

## Run

```shell
cd {root}
{run_hint}
```

The launcher prints live progress and records its exit status and finish time under `record/`. Each DeepAgents stage or final Claude report receives at most one repair attempt for JSON/schema errors, based only on deterministic structural validation. Pilot-specific evaluation and reference-leakage findings are never sent back to the model. Claude execution sandboxes are single-use because the Claude session ID is fixed. For DeepAgents, `./run.sh --clean` clears the prior workspace, outputs and run records, then reruns the full pipeline from stage 1 in the same sandbox; it does not resume the failed model conversation or skip completed stages. Use `--clean` before rerunning in place so old artifacts cannot be mistaken for new results. Claude runs also save the complete JSONL event stream in `output/transcript.jsonl`.

## Afterwards

From the repository root with your HarnessWeaver Python environment active (or prefix `hw` with `conda run -n <environment> --no-capture-output`):

```shell
hw check {root}
hw sandbox record {root}
```

`check` writes `check.json` next to this file; `record` copies the sandbox record, outputs and check result into `docs/cain-2027/evidence/{name}/`. A report schema failure may trigger one automatic Claude repair in the launcher; review `record/check-before-repair.json` and final `check.json`. DeepAgents applies the same one-retry limit to each stage artifact it validates.
"""

RUN_HINTS = {
    "claude": "ISOLATION=settings ./run.sh    # Claude subscription OAuth; raw transcript is saved in output/",
    "deepagents": "./run.sh    # provider keys come from the environment or a .env file; retry from scratch here with ./run.sh --clean",
}


def create_execution_sandbox(pilot_name: str | Path, target: str, bundle: Path, case: str, *,
                             root: Path | None = None, model: str = "") -> Path:
    """Create a sandbox that runs one generated bundle on one case with generation inputs only."""
    if target not in TARGETS:
        raise SandboxError(f"unknown target {target!r}; expected one of {', '.join(TARGETS)}")
    if target == "deepagents" and not model:
        raise SandboxError("a DeepAgents execution needs --model (for example openai:gpt-5.4-mini)")
    pilot = Pilot.load(pilot_name)
    bundle = Path(bundle).resolve()
    if not bundle.is_dir():
        raise SandboxError(f"bundle not found: {bundle}")
    case_path, binding = pilot.case(case)

    generation_inputs = []
    for item in binding.get("generation_inputs") or []:
        if "value" in item:
            value = item["value"]
            document = _envelope(item["envelope"], value) if item.get("envelope") else value
        else:
            source = (case_path.parent / item["from"]).resolve()
            value = select(json.loads(source.read_text(encoding="utf-8")), item["select"])
            document = _envelope(item["select"], value)
        generation_inputs.append((item, document))
    if target == "deepagents":
        named_inputs = _deepagents_input_map(bundle, generation_inputs)
    else:
        named_inputs = [(str(item["id"]), document) for item, document in generation_inputs]

    # Resolve required Claude configuration before creating any sandbox files. A missing
    # prompt should be an actionable pilot-configuration error, not a partial sandbox.
    claude_prompt_template = pilot.prompt("execution", "claude") if target == "claude" else None
    claude_allow_bash = pilot.claude_allowed_bash() if target == "claude" else []
    input_paths = [f"../input/{input_name}.json" for input_name, _ in named_inputs]
    input_listing = "\n".join(
        f"- `{input_name}` ({item.get('port', 'input')}): `../input/{input_name}.json`"
        for (input_name, _), (item, _) in zip(named_inputs, generation_inputs)
    ) or "- No input files were configured."

    created = _now()
    name = f"run-{pilot.name}-{target}-{case}-{_stamp(created)}"
    sandbox = _new_sandbox_dir(root, name)

    shutil.copytree(bundle, sandbox / "bundle")
    _make_read_only(sandbox / "bundle")
    input_dir = sandbox / "input"
    input_dir.mkdir()
    input_ids = []
    for input_name, document in named_inputs:
        _write(input_dir / f"{input_name}.json", json.dumps(document, indent=2, ensure_ascii=False) + "\n")
        input_ids.append(input_name)
    _make_read_only(input_dir)
    (sandbox / "output").mkdir()
    (sandbox / "record").mkdir()
    if target == "claude":
        # The generated project is the working directory; it may write its own _workspace/.
        shutil.copytree(bundle, sandbox / "workspace")
        first_input = input_paths[0] if input_paths else "../input/"
        prompt = (claude_prompt_template
                  .replace("{input}", first_input)
                  .replace("{inputs}", input_listing)
                  .replace("{output}", f"../output/{CLAUDE_REPORT_FILENAME}"))
        _write(sandbox / "prompt.md", prompt)
        # The generated ATAM Claude harness runs this local deterministic validator between stages.
        # Keep Bash narrowly scoped to commands explicitly configured by the pilot.
        _write(sandbox / "claude-settings.json", _claude_settings(
            writable=[sandbox / "workspace", sandbox / "output"],
            readable=[sandbox / "workspace", sandbox / "input"],
            denied_reads=[REPOSITORY_ROOT],
            allow_bash=claude_allow_bash,
        ))
        shutil.copyfile(Path(__file__).with_name("stream.py"), sandbox / "stream_claude.py")
    else:
        (sandbox / "workspace").mkdir()

    session_id = str(uuid4()) if target == "claude" else None
    _write(sandbox / "run.sh", EXECUTION_RUN_SH[target].format(
        session_id=session_id, model=model, case=case, report_filename=CLAUDE_REPORT_FILENAME), executable=True)
    _write(sandbox / "RUNBOOK.md", EXECUTION_RUNBOOK.format(
        name=name, target=target, pilot=pilot.name, case=case, bundle=bundle, inputs=", ".join(input_ids) or "none",
        root=sandbox, run_hint=RUN_HINTS[target]))
    _write_yaml(sandbox / SANDBOX_FILE, {
        "kind": "execution",
        "name": name,
        "pilot": pilot.name,
        "pilot_dir": str(pilot.root),
        "target": target,
        "case": case,
        "case_binding": str(case_path),
        "bundle_source": str(bundle),
        "created_at": created.isoformat(timespec="seconds"),
        "repository_commit": _git_commit(),
        "session_id": session_id,
        "model_requested": model or None,
    })
    input_paths = ["bundle", "input", "prompt.md"]
    if target == "claude":
        input_paths.append("stream_claude.py")
    _write(sandbox / MANIFEST_FILE, json.dumps({"inputs": _digests(sandbox, input_paths)}, indent=2) + "\n")
    return sandbox


def load_sandbox(sandbox: str | Path) -> tuple[Path, dict[str, Any]]:
    path = Path(sandbox).resolve()
    meta_path = path / SANDBOX_FILE
    if not meta_path.is_file():
        raise SandboxError(f"not a sandbox (no {SANDBOX_FILE}): {path}")
    return path, yaml.safe_load(meta_path.read_text(encoding="utf-8"))


def _find_transcript(session_id: str, projects_dir: Path | None = None) -> Path | None:
    base = projects_dir or Path.home() / ".claude/projects"
    matches = sorted(base.glob(f"*/{session_id}.jsonl")) if base.is_dir() else []
    return matches[0] if matches else None


def collect_generation(sandbox: str | Path, label: str, *, projects_dir: Path | None = None,
                       destination_root: Path | None = None) -> Path:
    """Copy a finished generation into the pilot and record how it was produced."""
    from harnessweaver.bundles import check_bundle

    path, meta = load_sandbox(sandbox)
    if meta.get("kind") != "generation":
        raise SandboxError(f"{path} is not a generation sandbox")
    if meta.get("spec_package"):
        _verify_staged_spec_package(path)
    generated = path / "generated"
    if not generated.is_dir() or not any(generated.iterdir()):
        raise SandboxError(f"nothing was generated in {generated}")
    destination = (destination_root or Path(meta["pilot_dir"]) / "generated") / label
    if destination.exists():
        raise SandboxError(f"label already used: {destination}")

    transcript = path / "record/transcript.jsonl"
    if not transcript.is_file():
        found = _find_transcript(meta["session_id"], projects_dir)
        if found:
            shutil.copyfile(found, transcript)
    shutil.copytree(generated, destination)
    if transcript.is_file():
        (destination / "record").mkdir(exist_ok=True)
        shutil.copyfile(transcript, destination / "record/transcript.jsonl")

    spec_candidates = sorted(destination.glob("**/harnessspec*.yaml"))
    bundle_checks: dict[str, Any] = {}
    packaged_bundles: dict[str, dict[str, str]] = {}
    for target in TARGETS:
        for bundle in sorted(destination.glob(f"**/build/{target}")):
            _write(bundle / "BUNDLE-GUIDE.md",
                   _bundle_guide(target, bundle, pilot=str(meta["pilot"])))
            archive = bundle.parent / f"{target}.zip"
            _bundle_zip(bundle, archive)
            packaged_bundles[str(bundle.relative_to(destination))] = {
                "guide": str((bundle / "BUNDLE-GUIDE.md").relative_to(destination)),
                "archive": str(archive.relative_to(destination)),
            }
            spec = spec_candidates[0] if spec_candidates else None
            issues = check_bundle(target, bundle, spec)
            bundle_checks[str(bundle.relative_to(destination))] = {
                "target": target, "spec": str(spec.relative_to(destination)) if spec else None,
                "passed": not issues, "issues": [str(issue) for issue in issues]}
    spec_package = None
    spec_package_error = None
    if spec_candidates:
        source_root = path / "sources"
        if not source_root.is_dir():
            spec_package_error = f"generation sandbox is missing source inputs: {source_root}"
        else:
            answer_file = path / "harness-answers.yaml"
            try:
                package_manifest = _write_spec_package(source_root, destination,
                                                      destination / SPEC_PACKAGE_FILENAME,
                                                      pilot=str(meta["pilot"]),
                                                      answers=answer_file if answer_file.is_file() else None)
            except SandboxError as exc:
                spec_package_error = str(exc)
            else:
                spec_package = {"path": SPEC_PACKAGE_FILENAME,
                                "spec_path": package_manifest["spec_path"],
                                "spec_sha256": package_manifest["spec_sha256"],
                                "file_count": len(package_manifest["files"])}
    record_dir = path / "record"
    record = {
        "label": label,
        "collected_at": _now().isoformat(timespec="seconds"),
        "sandbox": meta,
        "record_files": {name.name: name.read_text(encoding="utf-8").strip() for name in sorted(record_dir.glob("*.txt"))},
        "transcript": "record/transcript.jsonl" if transcript.is_file() else None,
        "inputs": json.loads((path / MANIFEST_FILE).read_text(encoding="utf-8"))["inputs"],
        "outputs": _digests(path, ["generated"]),
        "specs": [str(spec.relative_to(destination)) for spec in spec_candidates],
        "bundle_checks": bundle_checks,
        "packaged_bundles": packaged_bundles,
        "spec_package": spec_package,
        "spec_package_error": spec_package_error,
    }
    _write(destination / "generation-record.json", json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return destination


def package_spec(generation: str | Path) -> Path:
    """Backfill a portable spec package for an older collected generation."""
    directory = Path(generation).resolve()
    record_path = directory / "generation-record.json"
    if not record_path.is_file():
        raise SandboxError(f"not a collected generation (missing generation-record.json): {directory}")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    sandbox_meta = record.get("sandbox") or {}
    pilot = Pilot.load(sandbox_meta.get("pilot", ""))
    source_root = pilot.path("sources")
    expected = {name: digest for name, digest in (record.get("inputs") or {}).items()
                if name.startswith("sources/") and not any(part in {"__pycache__", ".DS_Store"} for part in Path(name).parts)}
    if not expected:
        raise SandboxError("generation record has no source digests; cannot prove the source package matches the original run")
    actual = {f"sources/{path.relative_to(source_root).as_posix()}": sha256_file(path)
              for path in source_root.rglob("*") if path.is_file()
              and not any(part in {"__pycache__", ".DS_Store"} for part in path.relative_to(source_root).parts)}
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        changed = sorted(key for key in set(expected) & set(actual) if expected[key] != actual[key])
        extra = sorted(set(actual) - set(expected))
        detail = "; ".join(part for part, values in (("missing", missing), ("changed", changed), ("extra", extra)) if values)
        raise SandboxError(f"current pilot sources do not match the recorded generation inputs ({detail}); refusing to package")
    expected_outputs = {name: digest for name, digest in (record.get("outputs") or {}).items()
                        if name.startswith("generated/") and not name.startswith(("generated/build/", "generated/record/"))
                        and Path(name).suffix != ".zip"
                        and Path(name).name != "generation-record.json"
                        and not any(part in {"__pycache__", ".DS_Store"} for part in Path(name).parts)}
    actual_outputs = {f"generated/{path.relative_to(directory).as_posix()}": sha256_file(path)
                      for path in directory.rglob("*") if path.is_file()
                      and not any(part in {"build", "record"} for part in path.relative_to(directory).parts)
                      and path.name != "generation-record.json" and path.suffix != ".zip"
                      and not any(part in {"__pycache__", ".DS_Store"} for part in path.relative_to(directory).parts)}
    if actual_outputs != expected_outputs:
        missing = sorted(set(expected_outputs) - set(actual_outputs))
        changed = sorted(key for key in set(expected_outputs) & set(actual_outputs)
                         if expected_outputs[key] != actual_outputs[key])
        extra = sorted(set(actual_outputs) - set(expected_outputs))
        detail = "; ".join(part for part, values in (("missing", missing), ("changed", changed), ("extra", extra)) if values)
        raise SandboxError(f"collected HarnessSpec package files differ from the original generation record ({detail}); refusing to package")
    input_digests = record.get("inputs") or {}
    answer_path = pilot.root / "harness-answers.yaml"
    answers = answer_path if answer_path.is_file() and input_digests.get("harness-answers.yaml") == sha256_file(answer_path) else None
    archive = directory / SPEC_PACKAGE_FILENAME
    if archive.exists():
        raise SandboxError(f"spec package already exists: {archive}")
    manifest = _write_spec_package(source_root, directory, archive, pilot=pilot.name, answers=answers)
    record["spec_package"] = {"path": SPEC_PACKAGE_FILENAME, "spec_path": manifest["spec_path"],
                              "spec_sha256": manifest["spec_sha256"], "file_count": len(manifest["files"])}
    _write(record_path, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return archive


def record_execution(sandbox: str | Path, *, evidence_root: Path | None = None) -> Path:
    """Copy an execution sandbox's record, outputs, intermediate artifacts and check into the evidence package."""
    path, meta = load_sandbox(sandbox)
    if meta.get("kind") != "execution":
        raise SandboxError(f"{path} is not an execution sandbox")
    destination = (evidence_root or EVIDENCE_DIR) / meta["name"]
    if destination.exists():
        raise SandboxError(f"already recorded: {destination}")
    destination.mkdir(parents=True)
    for name in (SANDBOX_FILE, "check.json", "prompt.md", "RUNBOOK.md"):
        if (path / name).is_file():
            shutil.copyfile(path / name, destination / name)
    for subdir in ("output", "record"):
        if (path / subdir).is_dir():
            shutil.copytree(path / subdir, destination / subdir)
    for intermediate in ("workspace/artifacts", "workspace/_workspace"):
        if (path / intermediate).is_dir():
            shutil.copytree(path / intermediate, destination / intermediate)
    manifest = json.loads((path / MANIFEST_FILE).read_text(encoding="utf-8"))
    manifest["outputs"] = _digests(path, ["output", "workspace/artifacts", "workspace/_workspace"])
    manifest["recorded_at"] = _now().isoformat(timespec="seconds")
    _write(destination / MANIFEST_FILE, json.dumps(manifest, indent=2) + "\n")
    return destination
