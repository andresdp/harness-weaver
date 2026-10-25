"""Render Claude Code's stream-json output while preserving the raw transcript."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def _text(console: Console, message: str, style: str | None = None) -> None:
    console.print(Text(message, style=style))


def _render(event: dict[str, Any], console: Console) -> bool:
    """Show user-facing progress only. Return True when Claude emitted a final result."""
    event_type = event.get("type")
    if event_type == "assistant":
        message = event.get("message") or {}
        for block in message.get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                value = str(block.get("text") or "").strip()
                if value:
                    _text(console, value[:2000])
            elif block.get("type") == "tool_use":
                _text(console, f"Using {block.get('name', 'a tool')}…", "cyan")
    elif event_type == "tool_progress":
        elapsed = event.get("elapsed_time_seconds")
        duration = f" ({elapsed}s)" if elapsed is not None else ""
        _text(console, f"Working: {event.get('tool_name', 'agent')}{duration}…", "dim cyan")
    elif event_type == "rate_limit_event":
        info = event.get("rate_limit_info") or {}
        utilization = info.get("unifiedWindows", {}).get("five_hour", {}).get("utilization")
        percent = f" {round(float(utilization) * 100)}% of the five-hour window" if utilization is not None else ""
        reset = info.get("unifiedWindows", {}).get("five_hour", {}).get("resetsAt")
        reset_text = f"; window resets {datetime.fromtimestamp(reset, timezone.utc).strftime('%H:%M UTC')}" if reset else ""
        _text(console, f"Usage notice ({info.get('status', 'unknown')}){percent}{reset_text}.", "yellow")
    elif event_type == "system" and event.get("subtype") in {"task_progress", "task_notification"}:
        detail = event.get("description") or event.get("message") or event.get("status")
        if detail:
            _text(console, f"Progress: {detail}", "dim")
    elif event_type == "result":
        detail = str(event.get("result") or event.get("subtype") or "Claude session ended")
        success = event.get("subtype") == "success"
        console.print(Panel(Text(detail[:3000]), title="Claude finished" if success else "Claude stopped",
                            border_style="green" if success else "yellow", expand=False))
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Display Claude progress and save its complete JSONL transcript.")
    parser.add_argument("--transcript", required=True, type=Path, help="destination JSONL transcript")
    parser.add_argument("--append", action="store_true", help="append events from a resumed session to the transcript")
    args = parser.parse_args(argv)
    args.transcript.parent.mkdir(parents=True, exist_ok=True)
    console = Console(highlight=False)
    console.print(Panel("Claude is running. Progress appears below; the full event stream is being saved.",
                        title="Execution sandbox", border_style="cyan", expand=False))
    saw_result = False
    try:
        with args.transcript.open("a" if args.append else "w", encoding="utf-8") as transcript:
            for line in sys.stdin:
                transcript.write(line)
                transcript.flush()
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    _text(console, "Received an unrecognized stream event; it is preserved in the transcript.", "yellow")
                    continue
                saw_result = _render(event, console) or saw_result
    except OSError as exc:
        print(f"cannot write Claude transcript {args.transcript}: {exc}", file=sys.stderr)
        return 2
    if not saw_result:
        _text(console, f"Claude's stream ended without a final result event. Transcript: {args.transcript}", "yellow")
    else:
        _text(console, f"Transcript saved: {args.transcript}", "dim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
