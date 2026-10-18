"""Command-line interface for validating HarnessSpec files."""

from __future__ import annotations

import argparse
import sys

from .spec import SpecLoadError, load_spec, validate_spec


def main() -> int:
    parser = argparse.ArgumentParser(prog="hw", description="Validate a HarnessSpec document.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="load and validate a spec")
    validate.add_argument("spec", help="path to a HarnessSpec JSON or YAML file")
    validate.add_argument("--capability", action="append", default=[], help="runtime capability available (repeatable)")
    args = parser.parse_args()
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


if __name__ == "__main__":
    raise SystemExit(main())
