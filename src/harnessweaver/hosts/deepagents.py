"""Generic DeepAgents host for generated stage-pipeline bundles described by `wiring.yaml`.

One deep agent runs per stage with that stage's `AGENTS.md` as memory and its `skills/` tree,
both mounted read-only at `/agent/`. Everything else, including `/artifacts/`, lives in the
run workspace. Stage order and completion checks are deterministic Python, never model choices.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any, Protocol

from jsonschema import Draft202012Validator
from rich.console import Console
from rich.panel import Panel

from harnessweaver._integrity import sha256_file
from harnessweaver.wiring import WIRING_FILENAME, Wiring, WiringError, WiringStage, load_wiring

RECORD_FILENAME = "host-record.json"
GATE_PENDING = "pending"
GATE_BYPASSED = "bypassed (unattended run)"
MAX_ARTIFACT_REPAIR_ATTEMPTS = 1
MAX_SCHEMA_DIAGNOSTICS = 20
console = Console(stderr=True, highlight=False)


class StageAgent(Protocol):
    def invoke(self, payload: Mapping[str, Any]) -> Any: ...


# Builds the agent for one stage from (stage directory, run workspace).
StageAgentFactory = Callable[[Path, Path], StageAgent]


@dataclass(frozen=True)
class StageRun:
    number: int
    dir: str
    status: str
    elapsed_seconds: float
    artifacts: tuple[str, ...]
    problems: tuple[str, ...] = ()
    repair_attempts: int = 0
    structured_output: bool = False
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class HostResult:
    status: str
    stages: tuple[StageRun, ...]
    output_path: Path | None
    human_gates: tuple[dict[str, Any], ...] = ()
    problems: tuple[str, ...] = ()


@dataclass
class _RunState:
    stages: list[StageRun] = field(default_factory=list)
    gates: list[dict[str, Any]] = field(default_factory=list)


def _workspace_path(workspace: Path, virtual: str) -> Path:
    return workspace / virtual.lstrip("/")


def _schema_error_problems(artifact: str, schema_ref: str, errors: list[Any]) -> list[str]:
    """Group repeated array-item violations so repair feedback covers every error shape."""
    grouped: dict[tuple[str, str], list[str]] = {}
    for error in errors:
        parts = list(error.path)
        path = "/".join(str(part) for part in parts) or "<root>"
        pattern = "/".join("[*]" if isinstance(part, int) else str(part) for part in parts) or "<root>"
        grouped.setdefault((pattern, error.message), []).append(path)

    problems = []
    for (pattern, message), paths in list(grouped.items())[:MAX_SCHEMA_DIAGNOSTICS]:
        detail = f"/artifacts/{artifact} violates {schema_ref} at {pattern}: {message}"
        if len(paths) > 1:
            examples = ", ".join(paths[:3])
            detail += f" (applies to {len(paths)} locations; examples: {examples})"
        problems.append(detail)
    omitted = sum(len(paths) for paths in list(grouped.values())[MAX_SCHEMA_DIAGNOSTICS:])
    if omitted:
        problems.append(f"/artifacts/{artifact}: {omitted} additional schema error(s) omitted")
    return problems


def _check_stage_artifacts(wiring: Wiring, stage: WiringStage, workspace: Path,
                           validators: dict[str, Draft202012Validator]) -> list[str]:
    """Each declared artifact must exist, parse as JSON, and satisfy its schema when one is named."""
    problems: list[str] = []
    for artifact in stage.artifacts:
        path = _workspace_path(workspace, f"/artifacts/{artifact}")
        if not path.is_file():
            problems.append(f"/artifacts/{artifact} is missing after stage {stage.number}")
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            problems.append(f"/artifacts/{artifact} is not valid JSON: {exc}")
            continue
        schema_ref = stage.schemas.get(artifact) or (wiring.output_schema if artifact == wiring.output_artifact else None)
        if schema_ref:
            if schema_ref not in validators:
                validators[schema_ref] = Draft202012Validator(json.loads((wiring.root / schema_ref).read_text(encoding="utf-8")))
            errors = sorted(validators[schema_ref].iter_errors(value), key=lambda error: list(error.path))
            if errors:
                problems.extend(_schema_error_problems(artifact, schema_ref, errors))
    return problems


def _persist_structured_response(stage: WiringStage, workspace: Path, result: Any) -> list[str]:
    """Persist the Pydantic structured response as the stage's declared JSON artifacts."""
    if not isinstance(result, Mapping) or result.get("structured_response") is None:
        return ["agent returned no structured_response"]
    response = result["structured_response"]
    if hasattr(response, "model_dump"):
        payload = response.model_dump(mode="json", by_alias=True, exclude_unset=True)
    elif isinstance(response, Mapping):
        payload = dict(response)
    else:
        return [f"structured_response has unsupported type {type(response).__name__}"]

    if len(stage.artifacts) == 1:
        artifact_values = {stage.artifacts[0]: payload}
    else:
        artifact_values = {}
        for index, artifact in enumerate(stage.artifacts, start=1):
            key = f"artifact_{index}"
            if key not in payload:
                return [f"structured_response is missing {key} for /artifacts/{artifact}"]
            artifact_values[artifact] = payload[key]

    for artifact, value in artifact_values.items():
        if not isinstance(value, (dict, list)):
            return [f"structured response for /artifacts/{artifact} must be a JSON object or array"]

    for artifact, value in artifact_values.items():
        path = _workspace_path(workspace, f"/artifacts/{artifact}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return []


def _write_record(out_dir: Path, wiring: Wiring | None, bundle: Path, state: _RunState, status: str,
                  output_path: Path | None, problems: list[str], started: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    wiring_path = bundle / WIRING_FILENAME
    record = {
        "host": "harnessweaver.hosts.deepagents",
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "bundle": str(bundle),
        "wiring_sha256": sha256_file(wiring_path) if wiring_path.is_file() else None,
        "spec": dict(wiring.spec) if wiring else None,
        "stages": [asdict(stage) for stage in state.stages],
        "human_gates": state.gates,
        "output": str(output_path) if output_path else None,
        "output_sha256": sha256_file(output_path) if output_path else None,
        "problems": problems,
    }
    (out_dir / RECORD_FILENAME).write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_stages(
    bundle: str | Path,
    input_dir: str | Path,
    workspace: str | Path,
    out_dir: str | Path,
    agent_factory: StageAgentFactory,
    *,
    continue_past_gates: bool = False,
    require_structured_output: bool = False,
) -> HostResult:
    """Run every stage in order; stop at the first incomplete stage or at an unreviewed human gate."""
    bundle, input_dir, workspace, out_dir = Path(bundle), Path(input_dir), Path(workspace), Path(out_dir)
    started = datetime.now(timezone.utc).isoformat()
    state = _RunState()

    def finish(status: str, output_path: Path | None = None, problems: list[str] | None = None,
               wiring: Wiring | None = None) -> HostResult:
        _write_record(out_dir, wiring, bundle, state, status, output_path, problems or [], started)
        return HostResult(status, tuple(state.stages), output_path, tuple(state.gates), tuple(problems or []))

    try:
        wiring = load_wiring(bundle)
    except WiringError as exc:
        return finish("failed", problems=[f"wiring: {issue}" for issue in exc.issues])

    # Inputs come only from the sandbox input directory, one file per declared port.
    missing = [item.port for item in wiring.inputs if not (input_dir / f"{item.port}.json").is_file()]
    if missing:
        available = sorted(path.name for path in input_dir.glob("*.json")) if input_dir.is_dir() else []
        return finish("failed", problems=[f"missing input file(s) for port(s) {missing} in {input_dir}; found {available}"],
                      wiring=wiring)
    for item in wiring.inputs:
        target = _workspace_path(workspace, str(item.path))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(input_dir / f"{item.port}.json", target)

    validators: dict[str, Draft202012Validator] = {}
    gates_by_stage: dict[int, list[str]] = {}
    for gate in wiring.human_gates:
        gates_by_stage.setdefault(gate.after_stage, []).append(gate.id)

    for stage in wiring.stages:
        stage_dir = bundle / stage.dir
        begin = monotonic()
        console.print(f"[cyan]Stage {stage.number}/{len(wiring.stages)}[/] · {stage.dir} — starting")
        structured_output_warning: str | None = None
        invocation_error: Exception | None = None
        problems: list[str] = []
        agent: StageAgent | None = None
        try:
            agent = agent_factory(stage_dir, workspace)
            with console.status(f"Stage {stage.number}/{len(wiring.stages)} · {stage.dir} is working…", spinner="dots"):
                stage_result = agent.invoke({"messages": [{"role": "user", "content": stage.handoff_prompt}]})
        except Exception as exc:  # the record must survive any provider or tool failure
            invocation_error = exc
            # Some agents write schema-valid artifacts through filesystem tools,
            # then fail only while parsing their separate final status response.
            # Preserve those files only when deterministic validation confirms all
            # declared outputs; a Pydantic/parser failure never bypasses schemas.
            if require_structured_output and type(exc).__name__ == "StructuredOutputValidationError":
                existing_problems = _check_stage_artifacts(wiring, stage, workspace, validators)
                if not existing_problems:
                    stage_result = None
                    structured_output_warning = (
                        "Final structured response did not match the Pydantic artifact model; "
                        "accepted the stage's existing files after JSON Schema validation."
                    )
                else:
                    problems = [f"{type(exc).__name__}: {str(exc)[:4000]}", *existing_problems]
            else:
                state.stages.append(StageRun(stage.number, stage.dir, "failed", round(monotonic() - begin, 3), stage.artifacts,
                                             (f"{type(exc).__name__}: {exc}",),
                                             structured_output=require_structured_output))
                return finish("failed", wiring=wiring)
        if structured_output_warning:
            problems = _check_stage_artifacts(wiring, stage, workspace, validators)
        elif invocation_error is None:
            has_response = isinstance(stage_result, Mapping) and stage_result.get("structured_response") is not None
            problems = _persist_structured_response(stage, workspace, stage_result) if require_structured_output and has_response else []
            if not problems:
                problems = _check_stage_artifacts(wiring, stage, workspace, validators)
        repair_attempts = 0
        while problems and repair_attempts < MAX_ARTIFACT_REPAIR_ATTEMPTS:
            if agent is None:
                break
            repair_attempts += 1
            console.print(f"[yellow]RETRY[/] · stage {stage.number}/{len(wiring.stages)} · "
                          f"{stage.dir}: repairing artifact validation issues "
                          f"({repair_attempts}/{MAX_ARTIFACT_REPAIR_ATTEMPTS})")
            repair_prompt = (
                "The host's deterministic artifact validation found these structural problems in the files "
                "produced by your stage:\n\n"
                + "\n".join(f"- {problem}" for problem in problems)
                + "\n\nResolve every listed problem, not only the first one. Correct only the listed "
                  "missing-artifact, JSON syntax, or schema problems in this stage's "
                  "declared artifacts. "
                  "Read the applicable schemas and treat them as authoritative if an instruction or example "
                  "conflicts. Use only identifiers and facts present in the available artifacts; do not invent "
                  "replacement IDs or remove substantive analysis to satisfy a constraint. Make the smallest "
                  "correction that brings each field into schema compliance while preserving its meaning. "
                  "Do not edit prior-stage artifacts unless your stage explicitly owns them. "
                + (
                    "Use the matching Pydantic-validated artifact writer tool to save each corrected output; "
                    "do not write paths under /artifacts/ with filesystem tools. "
                    if require_structured_output and len(stage.artifacts) > 1
                    else "Return the required structured response; the host writes its contents to the declared artifact files. "
                )
                + "Then re-read and validate every artifact your stage produces."
            )
            try:
                with console.status(f"Stage {stage.number}/{len(wiring.stages)} · {stage.dir} is repairing…", spinner="dots"):
                    repair_result = agent.invoke({"messages": [{"role": "user", "content": repair_prompt}]})
            except Exception as exc:  # retain diagnostics from both validation and repair invocation
                if require_structured_output and type(exc).__name__ == "StructuredOutputValidationError":
                    remaining = _check_stage_artifacts(wiring, stage, workspace, validators)
                    if not remaining:
                        problems = []
                        structured_output_warning = (
                            "Repair response did not match the Pydantic artifact model; "
                            "accepted repaired files after JSON Schema validation."
                        )
                    else:
                        problems = remaining + [
                            f"repair structured response failed: {type(exc).__name__}: {str(exc)[:4000]}"
                        ]
                else:
                    problems.append(f"repair attempt failed: {type(exc).__name__}: {exc}")
                break
            has_repair_response = isinstance(repair_result, Mapping) and repair_result.get("structured_response") is not None
            problems = _persist_structured_response(stage, workspace, repair_result) if require_structured_output and has_repair_response else []
            if not problems:
                problems = _check_stage_artifacts(wiring, stage, workspace, validators)
        state.stages.append(StageRun(stage.number, stage.dir, "failed" if problems else "completed",
                                     round(monotonic() - begin, 3), stage.artifacts, tuple(problems), repair_attempts,
                                     require_structured_output,
                                     (structured_output_warning,) if structured_output_warning else ()))
        console.print(f"[{'red' if problems else 'green'}]{'FAILED' if problems else 'PASS'}[/] · "
                      f"stage {stage.number}/{len(wiring.stages)} · {stage.dir} "
                      f"({round(monotonic() - begin, 1)}s)"
                      + (" · accepted schema-valid files after structured-response parse failure"
                         if structured_output_warning and not problems else "")
                      + (f" · structural repairs: {repair_attempts}" if repair_attempts else ""))
        if problems:
            return finish("failed", wiring=wiring)

        is_last = stage.number == len(wiring.stages)
        for gate_id in gates_by_stage.get(stage.number, []):
            # The host never approves a gate; it records it and, mid-pipeline, stops for review.
            status = GATE_PENDING if is_last or not continue_past_gates else GATE_BYPASSED
            state.gates.append({"id": gate_id, "after_stage": stage.number, "status": status})
        if not is_last and any(gate["status"] == GATE_PENDING for gate in state.gates):
            return finish("awaiting_review", wiring=wiring)

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / wiring.output_artifact
    shutil.copyfile(_workspace_path(workspace, f"/artifacts/{wiring.output_artifact}"), output_path)
    status = "awaiting_review" if any(gate["status"] == GATE_PENDING for gate in state.gates) else "completed"
    return finish(status, output_path, wiring=wiring)


def stage_permissions(*, artifact_writer_tools: bool = False) -> list[Any]:
    """Stage definitions are read-only; agents write only into the workspace."""
    from deepagents import FilesystemPermission

    permissions = [FilesystemPermission(operations=["write"], paths=["/agent/**"], mode="deny")]
    if artifact_writer_tools:
        permissions.append(FilesystemPermission(operations=["write"], paths=["/artifacts/**"], mode="deny"))
    return permissions


def build_stage_agent(stage_dir: Path, workspace: Path, chat_model: Any, *, structured_output: bool = False) -> StageAgent:
    """Create one stage agent, optionally enforcing its schema through Pydantic structured output."""
    try:
        from deepagents import create_deep_agent
        from deepagents.backends import CompositeBackend, FilesystemBackend
    except ImportError as exc:
        raise RuntimeError("DeepAgents is required for this host; install the 'deepagents' extra") from exc

    backend = CompositeBackend(
        default=FilesystemBackend(root_dir=str(workspace), virtual_mode=True),
        routes={"/agent/": FilesystemBackend(root_dir=str(stage_dir), virtual_mode=True)},
    )
    declared_stage = next(
        (item for item in load_wiring(stage_dir.parent).stages if item.dir == stage_dir.name), None
    )
    if declared_stage is None:
        raise ValueError(f"stage {stage_dir.name!r} is not declared by {stage_dir.parent / WIRING_FILENAME}")
    multi_artifact_writer = structured_output and len(declared_stage.artifacts) > 1
    agent_options: dict[str, Any] = {
        "model": chat_model,
        "memory": ["/agent/AGENTS.md"],
        "skills": ["/agent/skills/"],
        "backend": backend,
        "permissions": stage_permissions(artifact_writer_tools=multi_artifact_writer),
        "system_prompt": (
            "Complete the stage's ordered tasks and write each final artifact using its matching "
            "Pydantic-validated write_artifact tool. The tool validates and saves one artifact at a time; call it "
            "again if a later task revises that artifact. Do not use filesystem write or edit tools for paths under "
            "/artifacts/. You may use the workspace filesystem to read inputs and for scratch work."
            if multi_artifact_writer else (
                "Produce the declared artifact contents using the configured structured response. "
                "The final structured response must contain exactly the artifact data defined by its schema, not a "
                "progress summary, status report, or tool bookkeeping. The host persists that validated response "
                "to the artifact files. You may use the workspace filesystem to read inputs and for scratch work."
            )
        ) if structured_output else None,
    }
    if structured_output:
        if multi_artifact_writer:
            from harnessweaver.hosts.structured_output import stage_artifact_writer_tools

            agent_options["tools"] = stage_artifact_writer_tools(stage_dir.parent, stage_dir.name, workspace)
        else:
            from harnessweaver.hosts.structured_output import stage_response_model

            response_model, _ = stage_response_model(stage_dir.parent, stage_dir.name)
            # LangChain selects ProviderStrategy when supported and ToolStrategy otherwise.
            agent_options["response_format"] = response_model
    return create_deep_agent(
        **agent_options,
    )


def deepagents_factory(model_name: str, request_timeout_seconds: float) -> StageAgentFactory:
    """Factory for real runs: one env-configured chat model shared by every stage."""
    from langchain.chat_models import init_chat_model

    chat_model = init_chat_model(model_name, timeout=request_timeout_seconds)
    return lambda stage_dir, workspace: build_stage_agent(stage_dir, workspace, chat_model, structured_output=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m harnessweaver.hosts.deepagents",
                                     description="Run a generated DeepAgents stage-pipeline bundle.")
    parser.add_argument("--bundle", required=True, type=Path, help="directory containing wiring.yaml and stage directories")
    parser.add_argument("--input", required=True, type=Path, help="directory with one <port>.json file per wiring input")
    parser.add_argument("--workspace", required=True, type=Path, help="writable run workspace (holds /artifacts/)")
    parser.add_argument("--out", required=True, type=Path, help="directory for the output artifact and host-record.json")
    parser.add_argument("--model", required=True, help="LangChain model id, e.g. openai:gpt-5.4-mini")
    parser.add_argument("--timeout", type=float, default=180, help="per-request timeout in seconds")
    parser.add_argument("--continue-past-gates", action="store_true",
                        help="record mid-pipeline human gates as bypassed instead of stopping")
    args = parser.parse_args(argv)
    result = run_stages(args.bundle, args.input, args.workspace, args.out,
                        deepagents_factory(args.model, args.timeout), continue_past_gates=args.continue_past_gates,
                        require_structured_output=True)
    status_style = "green" if result.status in ("completed", "awaiting_review") else "red"
    console.print(Panel(f"Status: {result.status}\nRun record: {args.out / RECORD_FILENAME}\n"
                        f"Outputs: {args.out}", title="DeepAgents run", border_style=status_style, expand=False))
    for stage in result.stages:
        console.print(f"  stage {stage.number} {stage.dir}: {stage.status}" + "".join(f"\n    {p}" for p in stage.problems))
    for problem in result.problems:
        print(f"  {problem}", file=sys.stderr)
    return 0 if result.status in ("completed", "awaiting_review") else 1


if __name__ == "__main__":
    raise SystemExit(main())
