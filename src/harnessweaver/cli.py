"""Command-line interface: validate specs, check bundles and outputs, and manage sandboxes."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .spec import SpecLoadError, load_spec, validate_spec

console = Console(stderr=True, highlight=False)


def _panel(title: str, lines: list[str], *, style: str = "cyan") -> None:
    body = Text()
    for index, line in enumerate(lines):
        if index:
            body.append("\n")
        body.append(line)
    console.print(Panel(body, title=title, border_style=style, expand=False))


def _print_bundle_checks(checks: dict) -> None:
    table = Table("Target", "Bundle", "Result", box=None, pad_edge=False)
    for bundle, result in checks.items():
        table.add_row(
            str(result.get("target", "unknown")),
            bundle,
            "PASS" if result.get("passed") else "FAIL",
            style="green" if result.get("passed") else "red",
        )
        for issue in result.get("issues", []):
            table.add_row("", "", f"  {issue}", style="red")
    console.print(table)


def _validate(args: argparse.Namespace) -> int:
    try:
        document = load_spec(args.spec)
    except SpecLoadError as exc:
        console.print(Panel(f"{exc}", title="HarnessSpec error", border_style="red", expand=False))
        return 2
    issues = validate_spec(document, args.spec)
    if issues:
        for issue in issues:
            console.print(f"[red]error:[/] {issue}")
        return 1
    supported = set(args.capability)
    unsupported = sorted(set(document.get("runtime_requirements", [])) - supported) if supported else []
    if unsupported:
        for capability in unsupported:
            console.print(f"[red]Unsupported runtime capability:[/] {capability}")
        return 3
    _panel("HarnessSpec valid", [f"Version: {document['spec_version']}", f"ID: {document['id']}"], style="green")
    if not supported and document.get("runtime_requirements"):
        console.print("[yellow]Runtime capabilities were not assessed.[/] Pass --capability to check a target runtime.")
    return 0


def _check_bundle(args: argparse.Namespace) -> int:
    from .bundles import check_bundle

    issues = check_bundle(args.target, args.bundle, args.spec)
    for issue in issues:
        console.print(f"[red]error:[/] {issue}")
    if issues:
        return 1
    _panel("Bundle check passed", [f"Target: {args.target}", f"Bundle: {args.bundle}"], style="green")
    return 0


def _check(args: argparse.Namespace) -> int:
    from .checks import run_checks

    summary = run_checks(args.sandbox)
    table = Table("Check", "Result", "Details", box=None, pad_edge=False)
    for name, result in summary["checks"].items():
        problems = "\n".join(result["problems"]) or "—"
        table.add_row(name, "PASS" if result["passed"] else "FAIL", problems,
                      style="green" if result["passed"] else "red")
    console.print(table)
    check_path = Path(args.sandbox) / "check.json"
    repair_prompt = getattr(args, "repair_prompt", None)
    if repair_prompt is not None:
        schema_result = summary["checks"].get("schema", {})
        problems = schema_result.get("problems", [])
        report = summary.get("report")
        # Only a failed report schema check can trigger repair. Pilot-specific and leakage
        # checker findings are intentionally never included in model-facing feedback.
        if not schema_result.get("passed") and report and problems:
            locations = []
            for problem in problems:
                location = str(problem).split(":", 1)[0].strip()
                if location and location not in locations:
                    locations.append(location)
            prompt_path = Path(repair_prompt)
            if not prompt_path.is_absolute():
                prompt_path = Path(args.sandbox) / prompt_path
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            location_text = "\n".join(f"- {item}" for item in locations) or "- report JSON/schema conformance"
            prompt_path.write_text(
                "The deterministic JSON/schema check found a structural problem in the final report.\n\n"
                f"Report: {report}\n"
                "Affected paths (error details and evaluator findings are withheld):\n"
                f"{location_text}\n\n"
                "Read the applicable report schema and harness instructions available in this sandbox. "
                "Repair only JSON syntax and schema conformance in the final report, preserving its "
                "substantive evidence and meaning. Do not use or seek evaluator-only/reference data, "
                "and do not revise unrelated artifacts. Re-read the report after writing it.\n",
                encoding="utf-8",
            )
            console.print(f"[yellow]Schema repair is available:[/] {prompt_path}")
        elif not summary["passed"]:
            console.print("[dim]No model repair prompt generated: no final report schema issue was found.[/]")
    if summary["passed"]:
        _panel("Execution checks passed", [f"Check record: {check_path}",
                                           f"Next: hw sandbox record {shlex.quote(str(Path(args.sandbox)))}"], style="green")
    else:
        _panel("Execution checks found issues", [f"Check record: {check_path}", "Review the failed checks before recording this run."], style="red")
    return 0 if summary["passed"] else 1


def _sandbox(args: argparse.Namespace) -> int:
    from . import sandbox

    if args.sandbox_command == "create-generation":
        path = sandbox.create_generation_sandbox(args.pilot, args.arm, root=args.root, model=args.model,
                                                 answers=args.answers, include_langchain_skills=not args.no_langchain_skills)
        _panel("Generation sandbox ready", [
            f"Pilot: {args.pilot} · arm: {args.arm}",
            "Read-only inputs: pilot sources and the selected harness skill.",
            "Writable output: generated/ inside the sandbox.",
            f"Next (OAuth): cd {shlex.quote(str(path))} && ISOLATION=settings ./run.sh",
            f"Runbook: {path / 'RUNBOOK.md'}",
        ])
    elif args.sandbox_command == "create-execution":
        path = sandbox.create_execution_sandbox(args.pilot, args.target, args.bundle, args.case,
                                                root=args.root, model=args.model)
        _panel("Execution sandbox ready", [
            f"Pilot: {args.pilot} · target: {args.target} · case: {args.case}",
            "Input boundary: generation inputs only; evaluator-only data was excluded.",
            (f"Next (OAuth): cd {shlex.quote(str(path))} && ISOLATION=settings ./run.sh"
             if args.target == "claude" else "Next: ./run.sh uses the configured provider credentials."),
            f"Runbook: {path / 'RUNBOOK.md'}",
        ])
    elif args.sandbox_command == "collect":
        path = sandbox.collect_generation(args.sandbox, args.label)
        record = json.loads((path / "generation-record.json").read_text(encoding="utf-8"))
        _panel("Generation collected", [
            f"Label: {record['label']}",
            f"Destination: {path}",
            f"Transcript: {record['transcript'] or 'not found'}",
        ], style="green" if record.get("bundle_checks") and all(x.get("passed") for x in record["bundle_checks"].values()) else "yellow")
        if record.get("bundle_checks"):
            _print_bundle_checks(record["bundle_checks"])
        if not record["transcript"]:
            console.print("[yellow]Transcript not found.[/] Copy it into record/transcript.jsonl if available.")
        passed = [bundle for bundle, result in record.get("bundle_checks", {}).items() if result.get("passed")]
        if passed:
            pilot = record["sandbox"]["pilot"]
            cases = sorted(p.stem for p in (Path("pilots") / pilot / "cases").glob("*.yaml"))
            next_steps = ["Next: create an execution sandbox for a passing target and case.",
                          f"Available case(s): {', '.join(cases) or 'see pilots/<pilot>/cases/'}"]
            example_case = cases[0] if cases else "<case-name>"
            for bundle in passed:
                target = record["bundle_checks"][bundle]["target"]
                next_steps.append(
                    f"hw sandbox create-execution {pilot} --target {target} "
                    f"--bundle {shlex.quote(str(path / bundle))} --case {example_case}"
                )
            _panel("Next step", next_steps)
        elif record.get("bundle_checks"):
            _panel("Next step", ["Review the materialization reports and fix bundle-check failures before execution."], style="yellow")
    else:
        path = sandbox.record_execution(args.sandbox)
        _panel("Execution evidence recorded", [
            f"Evidence directory: {path}",
            "Next: review sandbox.yaml, check.json, output/, and record/ in the evidence directory.",
        ], style="green")
    # Keep the path alone on stdout so scripts can capture it; Rich summaries go to stderr.
    print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    from .bundles import TARGETS
    from .sandbox import ARMS

    parser = argparse.ArgumentParser(prog="hw", description="HarnessWeaver tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="load and validate a HarnessSpec")
    validate.add_argument("spec", help="path to a HarnessSpec JSON or YAML file")
    validate.add_argument("--capability", action="append", default=[], help="runtime capability available (repeatable)")
    validate.set_defaults(handler=_validate)

    bundle = subparsers.add_parser("check-bundle", help="structurally check a generated runtime bundle")
    bundle.add_argument("bundle", type=Path, help="bundle directory (e.g. build/claude or build/deepagents)")
    bundle.add_argument("--target", required=True, choices=TARGETS)
    bundle.add_argument("--spec", type=Path, help="HarnessSpec the bundle was generated from (checks the materialization report covers it)")
    bundle.set_defaults(handler=_check_bundle)

    check = subparsers.add_parser("check", help="check an execution sandbox's outputs from outside the sandbox")
    check.add_argument("sandbox", type=Path, help="execution sandbox directory printed by create-execution")
    check.add_argument("--repair-prompt", type=Path,
                       help="write a bounded repair prompt for final-report JSON/schema errors only")
    check.set_defaults(handler=_check)

    box = subparsers.add_parser("sandbox", help="create, collect and record sandboxes")
    box_commands = box.add_subparsers(dest="sandbox_command", required=True)
    generation = box_commands.add_parser("create-generation", help="sandbox for a user-run generation session")
    generation.add_argument("pilot", help="pilot name (pilots/<name>) or directory with pilot.yaml")
    generation.add_argument("--arm", default="harnessweaver", choices=ARMS)
    generation.add_argument("--answers", type=Path, help="harness-answers.yaml to pre-answer gates (harnessweaver arm only)")
    generation.add_argument("--model", default="", help="Claude model for the session (default: Claude Code default)")
    generation.add_argument("--root", type=Path, help="parent directory (default: HW_SANDBOX_ROOT or a sibling of the repository)")
    generation.add_argument("--no-langchain-skills", action="store_true", help="do not add the langchain deep-agents skills")
    execution = box_commands.add_parser("create-execution", help="prepare one runtime bundle and one case for an isolated run")
    execution.add_argument("pilot")
    execution.add_argument("--target", required=True, choices=TARGETS)
    execution.add_argument("--bundle", required=True, type=Path)
    execution.add_argument("--case", required=True, help="case binding name (pilots/<pilot>/cases/<case>.yaml)")
    execution.add_argument("--model", default="", help="model id (required for deepagents, e.g. openai:gpt-5.4-mini)")
    execution.add_argument("--root", type=Path)
    collect = box_commands.add_parser("collect", help="save generation output, check runtime bundles, and show execution commands")
    collect.add_argument("sandbox", type=Path)
    collect.add_argument("--label", required=True)
    record = box_commands.add_parser("record", help="copy an execution sandbox's evidence into docs/cain-2027/evidence/")
    record.add_argument("sandbox", type=Path)
    box.set_defaults(handler=_sandbox)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except ValueError as exc:  # SandboxError, unknown target, malformed inputs
        console.print(Panel(f"{exc}", title="Sandbox command failed", border_style="red", expand=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
