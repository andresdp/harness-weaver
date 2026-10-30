#!/usr/bin/env python3
"""Run the ATAM harness: stage0 intake, then stage1..stage7, each model stage as its own `claude -p` process.

Ordering is fixed in code: every stage is begun and completed through the run ledger (atam.py), so a stage
cannot start before its predecessor's gate has passed. stage7-revise_report always runs after
stage6-check_evaluation, including when the initial review found nothing to correct.

Usage (from the bundle root):
  python3 atam_harness/run.py --input path/to/evaluation_inputs.json
  python3 atam_harness/run.py --from stage4-analyze_scenarios      # partial re-run of an existing workspace
  python3 atam_harness/run.py --input case.json --dry-run          # print the plan, run nothing
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atam  # noqa: E402

NON_RETRYABLE = re.compile(r"usage limit|rate limit|quota|credit balance|authenticat|unauthori[sz]ed|"
                           r"invalid api key|oauth|please run /login|permission denied", re.I)
AGENT_STAGES = atam.STAGE_IDS[1:]


def claude_cmd(args, stage_id: str, prompt: str) -> list[str]:
    return [args.claude, "-p", prompt, "--agent", atam.STAGE_BY_ID[stage_id]["agent"],
            "--permission-mode", "dontAsk", "--output-format", "json", *args.claude_arg]


def run_agent(args, ws: Path, stage_id: str, attempt: int, prompt: str) -> tuple[bool, str]:
    """Return (ok_to_continue, message). ok_to_continue is False only for non-retryable failures."""
    cmd = claude_cmd(args, stage_id, prompt)
    log = ws / atam.RUNTIME / f"{stage_id}.attempt{attempt}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(cmd, cwd=atam.ROOT, capture_output=True, text=True, timeout=args.timeout)
        out, code = proc.stdout + ("\n[stderr]\n" + proc.stderr if proc.stderr else ""), proc.returncode
    except subprocess.TimeoutExpired as exc:
        out, code = f"timeout after {args.timeout}s\n{exc.stdout or ''}", 124
    except FileNotFoundError:
        return False, f"cannot execute {args.claude!r}; install Claude Code or pass --claude"
    log.write_text(f"$ {shlex.join(cmd[:2] + ['<prompt>'] + cmd[3:])}\n[prompt]\n{prompt}\n[exit {code}]\n{out}",
                   encoding="utf-8")
    result_text, is_error = out, code != 0
    try:
        payload = json.loads(proc.stdout) if code != 124 else {}
        result_text = str(payload.get("result", out))
        is_error = is_error or bool(payload.get("is_error"))
    except (json.JSONDecodeError, UnboundLocalError, AttributeError):
        pass
    if is_error and NON_RETRYABLE.search(out):
        return False, f"{stage_id}: non-retryable runtime failure (see {log}):\n{result_text[:800]}"
    return True, result_text.strip()[-1500:]


def record_blocked(ws: Path, stage_id: str, message: str) -> None:
    p = ws / atam.RUNTIME / "blocked.md"
    p.write_text(f"# Run blocked at {stage_id}\n\n{message}\n\nOutputs present in the workspace are exactly the "
                 "files of the completed stages listed by `python3 atam_harness/atam.py status`. Nothing was "
                 "filled in on the blocked stage's behalf. Resolve the cause, then resume with "
                 f"`python3 atam_harness/run.py --resume`.\n", encoding="utf-8")


def gate_errors(ws: Path, stage_id: str) -> list[str]:
    return atam.load_ledger(ws)["stages"].get(stage_id, {}).get("errors", [])


def run_stage(args, ws: Path, stage_id: str, first_flag: str | None) -> int:
    """Begin, invoke and complete one stage, with one retry on a gate failure. Returns an exit code."""
    begin = ["--workspace", str(ws), "stage", "begin", stage_id, "--invocation", "claude-p"]
    if first_flag:
        begin.append(first_flag)
    if atam.main(begin) != 0:
        return 3
    for attempt in (1, 2):
        rec = atam.load_ledger(ws)["stages"][stage_id]
        prompt = atam.stage_prompt(ws, stage_id, gate_errors(ws, stage_id) if attempt == 2 else None)
        print(f"[{stage_id}] attempt {attempt}: claude -p --agent {atam.STAGE_BY_ID[stage_id]['agent']}", flush=True)
        ok, msg = run_agent(args, ws, stage_id, rec["attempts"], prompt)
        if not ok:
            record_blocked(ws, stage_id, msg)
            print(msg, file=sys.stderr)
            return 4
        if atam.main(["--workspace", str(ws), "stage", "complete", stage_id]) == 0:
            return 0
        if attempt == 1:
            print(f"[{stage_id}] gate failed; retrying once with the gate errors", flush=True)
            if atam.main(["--workspace", str(ws), "stage", "begin", stage_id, "--retry",
                          "--invocation", "claude-p"]) != 0:
                return 3
    print(f"[{stage_id}] gate failed twice; stopping. Later stages were not run. "
          f"Errors are in {ws / atam.LEDGER}.", file=sys.stderr)
    return 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", help="template-shaped evaluation-inputs JSON (required for a new run)")
    ap.add_argument("--run-id", help="session id for the report title (default: derived from time and input hash)")
    ap.add_argument("--from", dest="from_stage", choices=AGENT_STAGES,
                    help="re-run this stage and every later stage in the existing workspace")
    ap.add_argument("--resume", action="store_true",
                    help="continue an existing workspace from its first unfinished stage")
    ap.add_argument("--claude", default="claude", help="Claude Code executable")
    ap.add_argument("--claude-arg", action="append", default=[],
                    help="extra argument passed to every `claude -p` call (repeatable), e.g. --claude-arg=--model=opus")
    ap.add_argument("--timeout", type=int, default=3600, help="seconds per stage invocation")
    ap.add_argument("--dry-run", action="store_true", help="print the stage plan and commands; change nothing")
    args = ap.parse_args(argv)
    ws = atam.DEFAULT_WS

    if args.dry_run:
        for sid in atam.STAGE_IDS:
            s = atam.STAGE_BY_ID[sid]
            how = "deterministic (atam.py intake)" if s["agent"] is None else shlex.join(
                claude_cmd(args, sid, "<stage prompt from atam.py stage-prompt>"))
            print(f"{sid}: reads {s['reads'] or ['--input']} -> writes {s['writes']}\n    {how}")
        return 0

    start_flag = None
    if args.from_stage or args.resume:
        if not (ws / atam.LEDGER).exists():
            print("no existing workspace to re-run; start a new run with --input", file=sys.stderr)
            return 1
        ledger = atam.load_ledger(ws)
        if args.from_stage:
            start, start_flag = args.from_stage, "--rerun"
        else:
            pending = [s for s in AGENT_STAGES if ledger["stages"].get(s, {}).get("status") != "completed"]
            if not pending:
                print("all stages are already completed")
                return 0
            start = pending[0]
            st = ledger["stages"].get(start, {}).get("status")
            start_flag = "--retry" if st in ("started", "failed") else None
    else:
        if not args.input:
            print("--input is required for a new run", file=sys.stderr)
            return 1
        inp = Path(args.input).resolve()
        run_id = args.run_id or "atam-{}-{}".format(
            dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            hashlib.sha256(inp.read_bytes()).hexdigest()[:8] if inp.exists() else "noinput")
        rc = atam.main(["--workspace", str(ws), "intake", "--input", str(inp), "--run-id", run_id])
        if rc != 0:
            return rc
        start = AGENT_STAGES[0]

    for sid in AGENT_STAGES[AGENT_STAGES.index(start):]:
        rc = run_stage(args, ws, sid, start_flag if sid == start else None)
        if rc != 0:
            return rc

    final = atam.load_json(ws / atam.F06)
    if atam.load_ledger(ws)["stages"].get("stage7-revise_report", {}).get("status") != "completed":
        print("stage7-revise_report did not complete; no final readiness exists", file=sys.stderr)
        return 2
    print(f"\nFinal report:          {ws / atam.F05}\nFinal review findings: {ws / atam.F06}\n"
          f"ready_for_architect_review: {str(final['ready_for_architect_review']).lower()} "
          f"(remaining blocking findings: {final['readiness_basis']['blocking_findings_remaining']})\n"
          "report_status: draft (a software architect must review it before it informs a decision)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
