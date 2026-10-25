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

from harnessweaver._integrity import sha256_file
from harnessweaver.wiring import WIRING_FILENAME, Wiring, WiringError, WiringStage, load_wiring

RECORD_FILENAME = "host-record.json"
GATE_PENDING = "pending"
GATE_BYPASSED = "bypassed (unattended run)"


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
                first = errors[0]
                where = "/".join(str(part) for part in first.path) or "<root>"
                problems.append(f"/artifacts/{artifact} violates {schema_ref} at {where}: {first.message} ({len(errors)} error(s))")
    return problems


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
        try:
            agent = agent_factory(stage_dir, workspace)
            agent.invoke({"messages": [{"role": "user", "content": stage.handoff_prompt}]})
        except Exception as exc:  # the record must survive any provider or tool failure
            state.stages.append(StageRun(stage.number, stage.dir, "failed", round(monotonic() - begin, 3), stage.artifacts,
                                         (f"{type(exc).__name__}: {exc}",)))
            return finish("failed", wiring=wiring)
        problems = _check_stage_artifacts(wiring, stage, workspace, validators)
        state.stages.append(StageRun(stage.number, stage.dir, "failed" if problems else "completed",
                                     round(monotonic() - begin, 3), stage.artifacts, tuple(problems)))
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


def stage_permissions() -> list[Any]:
    """Stage definitions are read-only; agents write only into the workspace."""
    from deepagents import FilesystemPermission

    return [FilesystemPermission(operations=["write"], paths=["/agent/**"], mode="deny")]


def build_stage_agent(stage_dir: Path, workspace: Path, chat_model: Any) -> StageAgent:
    """Create one stage agent following the DeepAgents target pattern."""
    try:
        from deepagents import create_deep_agent
        from deepagents.backends import CompositeBackend, FilesystemBackend
    except ImportError as exc:
        raise RuntimeError("DeepAgents is required for this host; install the 'deepagents' extra") from exc

    backend = CompositeBackend(
        default=FilesystemBackend(root_dir=str(workspace), virtual_mode=True),
        routes={"/agent/": FilesystemBackend(root_dir=str(stage_dir), virtual_mode=True)},
    )
    return create_deep_agent(
        model=chat_model,
        memory=["/agent/AGENTS.md"],
        skills=["/agent/skills/"],
        backend=backend,
        permissions=stage_permissions(),
    )


def deepagents_factory(model_name: str, request_timeout_seconds: float) -> StageAgentFactory:
    """Factory for real runs: one env-configured chat model shared by every stage."""
    from langchain.chat_models import init_chat_model

    chat_model = init_chat_model(model_name, timeout=request_timeout_seconds)
    return lambda stage_dir, workspace: build_stage_agent(stage_dir, workspace, chat_model)


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
                        deepagents_factory(args.model, args.timeout), continue_past_gates=args.continue_past_gates)
    print(f"{result.status}: {args.out / RECORD_FILENAME}")
    for stage in result.stages:
        print(f"  stage {stage.number} {stage.dir}: {stage.status}" + "".join(f"\n    {p}" for p in stage.problems))
    for problem in result.problems:
        print(f"  {problem}", file=sys.stderr)
    return 0 if result.status in ("completed", "awaiting_review") else 1


if __name__ == "__main__":
    raise SystemExit(main())
