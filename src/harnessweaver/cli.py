"""Command-line interface: validate specs, check bundles and outputs, and manage sandboxes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .spec import SpecLoadError, load_spec, validate_spec


def _validate(args: argparse.Namespace) -> int:
    try:
        document = load_spec(args.spec)
    except SpecLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    issues = validate_spec(document, args.spec)
    if issues:
        for issue in issues:
            print(f"error: {issue}", file=sys.stderr)
        return 1
    supported = set(args.capability)
    unsupported = sorted(set(document.get("runtime_requirements", [])) - supported) if supported else []
    if unsupported:
        for capability in unsupported:
            print(f"unsupported runtime capability: {capability}", file=sys.stderr)
        return 3
    print(f"valid HarnessSpec {document['spec_version']}: {document['id']}")
    if not supported and document.get("runtime_requirements"):
        print("runtime capabilities not assessed (pass --capability to check a target runtime)", file=sys.stderr)
    return 0


def _check_bundle(args: argparse.Namespace) -> int:
    from .bundles import check_bundle

    issues = check_bundle(args.target, args.bundle, args.spec)
    for issue in issues:
        print(f"error: {issue}", file=sys.stderr)
    if issues:
        return 1
    print(f"bundle passes {args.target} structural checks: {args.bundle}")
    return 0


def _check(args: argparse.Namespace) -> int:
    from .checks import run_checks

    summary = run_checks(args.sandbox)
    for name, result in summary["checks"].items():
        print(f"{'PASS' if result['passed'] else 'FAIL'} {name}")
        for problem in result["problems"]:
            print(f"    {problem}")
    print(f"wrote {Path(args.sandbox) / 'check.json'}")
    return 0 if summary["passed"] else 1


def _sandbox(args: argparse.Namespace) -> int:
    from . import sandbox

    if args.sandbox_command == "create-generation":
        path = sandbox.create_generation_sandbox(args.pilot, args.arm, root=args.root, model=args.model,
                                                 answers=args.answers, include_langchain_skills=not args.no_langchain_skills)
    elif args.sandbox_command == "create-execution":
        path = sandbox.create_execution_sandbox(args.pilot, args.target, args.bundle, args.case,
                                                root=args.root, model=args.model)
    elif args.sandbox_command == "collect":
        path = sandbox.collect_generation(args.sandbox, args.label)
        record = json.loads((path / "generation-record.json").read_text(encoding="utf-8"))
        for bundle, result in record["bundle_checks"].items():
            print(f"{'PASS' if result['passed'] else 'FAIL'} check-bundle {result['target']}: {bundle}")
            for issue in result["issues"]:
                print(f"    {issue}")
        if not record["transcript"]:
            print("warning: session transcript not found; copy it into record/transcript.jsonl", file=sys.stderr)
    else:
        path = sandbox.record_execution(args.sandbox)
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
    check.add_argument("sandbox", type=Path)
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
    execution = box_commands.add_parser("create-execution", help="sandbox that runs one generated bundle on one case")
    execution.add_argument("pilot")
    execution.add_argument("--target", required=True, choices=TARGETS)
    execution.add_argument("--bundle", required=True, type=Path)
    execution.add_argument("--case", required=True, help="case binding name (pilots/<pilot>/cases/<case>.yaml)")
    execution.add_argument("--model", default="", help="model id (required for deepagents, e.g. openai:gpt-5.4-mini)")
    execution.add_argument("--root", type=Path)
    collect = box_commands.add_parser("collect", help="copy a finished generation into pilots/<pilot>/generated/<label>/")
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
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
