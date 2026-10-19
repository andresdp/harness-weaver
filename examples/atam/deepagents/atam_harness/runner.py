"""Coordinate configuration, agent execution, and report output for one run."""

import sys
from uuid import uuid4

from .agents import build_agent
from .config import ResolvedRunConfig, format_resolved_settings
from .execution import execute_agent
from .reports import compose_report, load_case, write_report


def run(config: ResolvedRunConfig) -> None:
    """Run the ATAM agent and write its validated report."""
    run_id = uuid4()
    session_id = str(run_id)
    print(f"Session ID: {session_id}", file=sys.stderr)
    settings_display = (
        "Effective settings (YAML defaults with overrides applied):\n"
        f"{format_resolved_settings(config)}"
    )
    try:
        from rich.console import Console
    except ImportError:
        print(settings_display, file=sys.stderr, end="")
    else:
        # Dim the configuration block so it stays visible without competing with progress.
        Console(stderr=True).print(settings_display, style="dim white", markup=False, highlight=False)

    case = load_case(config.case)
    agent = build_agent(config.model)
    result = execute_agent(
        agent,
        case.evaluation_inputs,
        run_id=run_id,
        streaming=config.streaming,
        verbose=config.verbose,
    )
    if not result.get("messages"):
        raise ValueError("DeepAgents returned no messages")
    structured_response = result.get("structured_response")
    if structured_response is None:
        raise ValueError("DeepAgents returned no structured_response")

    report = compose_report(case, structured_response, session_id)
    output_path = write_report(report, config.output, session_id)
    print(f"Wrote ATAM report to {output_path}")
