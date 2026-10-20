"""Load case-study YAML defaults and merge command-line overrides."""

import argparse
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from harnessweaver.runtime import AgentInteraction, ExecutionProfile, WorkflowStrategy, profile_from_spec
from harnessweaver.spec import SpecLoadError, load_spec

from .paths import DEFAULT_CASE_STUDY_ROOT, DEFAULT_HARNESS_SPEC_PATH, SETTINGS_FILENAME


class RunSettings(BaseModel):
    """Validated settings for a single ATAM DeepAgents run."""

    model_config = ConfigDict(extra="forbid")

    # These paths are interpreted relative to the case-study settings file.
    case: Path = Field(default=Path("data/banking.json"), description="Case JSON, relative to the case-study root")
    output: Path = Field(default=Path("runs/banking-report.json"), description="Report path, relative to the case-study root")
    model: str = Field(default="openai:gpt-5.4-mini", description="LangChain provider:model identifier")
    request_timeout_seconds: float = Field(
        default=180,
        gt=0,
        le=3600,
        description="Maximum time for an individual provider model request",
    )
    harness_spec: Path = Field(default=DEFAULT_HARNESS_SPEC_PATH, description="HarnessSpec path, relative to the case-study root")
    streaming: bool = Field(default=True, description="Stream execution events while the agent runs")
    verbose: bool = Field(default=True, description="Display agent, skill, and tool progress")


class ResolvedRunConfig(BaseModel):
    """Absolute paths and effective values after applying all configuration sources."""

    case: Path
    output: Path
    model: str
    request_timeout_seconds: float
    harness_spec: Path
    workflow_strategy: str
    agent_interaction: str
    streaming: bool
    verbose: bool
    case_study_root: Path

    @property
    def execution_profile(self) -> ExecutionProfile:
        """Expose the validated, separate coordination and interaction selections."""
        return ExecutionProfile(
            WorkflowStrategy(self.workflow_strategy),
            AgentInteraction(self.agent_interaction),
        )


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI; unset options remain None so YAML values can apply."""
    parser = argparse.ArgumentParser(description="Run the ATAM evaluation harness with DeepAgents.")
    parser.add_argument("case_argument", nargs="?", type=Path, help="case JSON (overrides settings.yaml)")
    parser.add_argument("--case", dest="case_option", type=Path, help="case JSON (overrides settings.yaml)")
    parser.add_argument("--case-study", type=Path, help="case-study root containing settings.yaml")
    parser.add_argument("--output", type=Path, help="report path (overrides settings.yaml)")
    parser.add_argument("--model", help="LangChain provider:model (overrides HW_ATAM_MODEL and YAML)")
    parser.add_argument("--harness-spec", type=Path, help="HarnessSpec path (overrides settings.yaml)")
    parser.add_argument("--workflow-strategy", choices=tuple(item.value for item in WorkflowStrategy))
    parser.add_argument("--agent-interaction", choices=tuple(item.value for item in AgentInteraction))
    parser.add_argument("--streaming", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--verbose", action=argparse.BooleanOptionalAction, default=None)
    return parser


def _infer_case_study_root(case_path: Path) -> Path:
    """Find the nearest case-study settings file or use the conventional data/ layout."""
    absolute_case = case_path.expanduser().resolve()
    for parent in absolute_case.parents:
        if (parent / SETTINGS_FILENAME).is_file():
            return parent
    if absolute_case.parent.name == "data":
        return absolute_case.parent.parent
    return absolute_case.parent


def _load_yaml_settings(case_study_root: Path) -> dict[str, Any]:
    """Read settings.yaml, treating a missing file as an empty settings document."""
    settings_path = case_study_root / SETTINGS_FILENAME
    if not settings_path.exists():
        return {}
    parsed = yaml.safe_load(settings_path.read_text(encoding="utf-8"))
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ValueError(f"{settings_path} must contain a YAML mapping")
    return parsed


def _resolve_setting_path(value: Path, root: Path) -> Path:
    """Resolve YAML paths from the case-study folder and absolute paths as given."""
    expanded = value.expanduser()
    return expanded.resolve() if expanded.is_absolute() else (root / expanded).resolve()


def resolve_config(args: argparse.Namespace, environ: dict[str, str] | None = None) -> ResolvedRunConfig:
    """Apply CLI > environment model override > YAML > model defaults."""
    environment = os.environ if environ is None else environ
    case_argument = args.case_option or args.case_argument
    if args.case_option and args.case_argument:
        raise ValueError("provide the case either positionally or with --case, not both")

    if args.case_study:
        case_study_root = args.case_study.expanduser().resolve()
    elif case_argument is not None:
        case_study_root = _infer_case_study_root(case_argument)
    else:
        case_study_root = DEFAULT_CASE_STUDY_ROOT.resolve()

    try:
        configured = RunSettings.model_validate(_load_yaml_settings(case_study_root))
    except ValidationError as exc:
        raise ValueError(f"invalid {case_study_root / SETTINGS_FILENAME}: {exc}") from exc

    # Command-line case/output paths retain the shell's current-directory semantics.
    case = case_argument.expanduser().resolve() if case_argument else _resolve_setting_path(configured.case, case_study_root)
    output = args.output.expanduser().resolve() if args.output else _resolve_setting_path(configured.output, case_study_root)
    model = args.model or environment.get("HW_ATAM_MODEL") or configured.model
    harness_spec = args.harness_spec.expanduser().resolve() if args.harness_spec else _resolve_setting_path(configured.harness_spec, case_study_root)
    try:
        spec_document = load_spec(harness_spec)
        profile = profile_from_spec(
            spec_document,
            strategy=args.workflow_strategy,
            interaction=args.agent_interaction,
        )
    except (OSError, SpecLoadError, ValueError) as exc:
        raise ValueError(f"cannot resolve HarnessSpec orchestration from {harness_spec}: {exc}") from exc
    streaming = configured.streaming if args.streaming is None else args.streaming
    verbose = configured.verbose if args.verbose is None else args.verbose

    return ResolvedRunConfig(
        case=case,
        output=output,
        model=model,
        request_timeout_seconds=configured.request_timeout_seconds,
        harness_spec=harness_spec,
        workflow_strategy=profile.workflow_strategy.value,
        agent_interaction=profile.agent_interaction.value,
        streaming=streaming,
        verbose=verbose,
        case_study_root=case_study_root,
    )


def format_resolved_settings(config: ResolvedRunConfig) -> str:
    """Render the effective YAML settings without internal path-discovery metadata."""
    visible_settings = config.model_dump(mode="json", exclude={"case_study_root"})
    return yaml.safe_dump(visible_settings, sort_keys=False)
