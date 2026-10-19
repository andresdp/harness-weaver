"""Coordinate configuration, agent execution, and report output for one run."""

import sys
from uuid import uuid4

from harnessweaver.adapters.deepagents import DeepAgentsRuntimeAdapter
from harnessweaver.runtime import RunRequest

from .config import ResolvedRunConfig, format_resolved_settings
from .models import AtamReportPayload
from .orchestration import AtamDeepAgentsOperations
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
    request = RunRequest(
        run_id=run_id,
        case_id=config.case.stem,
        inputs=case.evaluation_inputs,
        profile=config.execution_profile,
        model=config.model,
        spec_path=config.harness_spec,
        output_path=config.output,
        streaming=config.streaming,
        verbose=config.verbose,
        settings={"workflow_strategy": config.workflow_strategy, "agent_interaction": config.agent_interaction},
    )
    adapter = DeepAgentsRuntimeAdapter(lambda run_request: AtamDeepAgentsOperations(run_request))
    result = adapter.run(request)
    if result.status != "succeeded" or result.artifact is None:
        raise ValueError(f"DeepAgents run failed: {result.status}")
    structured_response = AtamReportPayload.model_validate(result.artifact)

    report = compose_report(case, structured_response, session_id)
    output_path = write_report(report, config.output, session_id)
    print(f"Wrote ATAM report to {output_path} (runtime: {result.elapsed_seconds:.2f}s)")
