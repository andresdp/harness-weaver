"""Run the HarnessWeaver ATAM evaluation harness with DeepAgents.

The model produces only the typed report sections. This runner supplies the original
evaluation inputs and writes the final JSON after structural validation.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TEMPLATE_PATH = ROOT / "examples/atam/report-template.json"


class _StrictModel(BaseModel):
    """Base for report models that reject fields outside the agreed report contract."""

    # Reject unexpected keys so provider output cannot silently expand the report shape.
    model_config = ConfigDict(extra="forbid")


class AtamMetadata(_StrictModel):
    """Known evaluation context; nullable values mark metadata absent from the case."""

    system_name: str | None = Field(description="Evidence-based system name, or null if unavailable")
    date: str | None = Field(description="Evaluation date, or null if unavailable")
    ref: str | None = Field(description="Source reference, or null if unavailable")
    evaluator_organization: str | None = Field(description="Evaluator organization, or null if unavailable")
    phase_1_attendees: list[str] = Field(description="Known phase 1 attendee roles; use an empty list if unavailable")
    phase_2_attendees: list[str] = Field(description="Known phase 2 attendee roles; use an empty list if unavailable")


class AtamPriorityTuple(_StrictModel):
    """Relative importance and difficulty assigned to a utility-tree scenario."""

    importance: str = Field(description="Relative importance of achieving this scenario")
    difficulty: str = Field(description="Relative difficulty of achieving this scenario")


class AtamUtilityScenario(_StrictModel):
    """A measurable quality-attribute scenario in the utility tree."""

    refinement: str = Field(description="Refinement level or grouping for the scenario")
    scenario_id: str = Field(description="Stable identifier for this scenario")
    scenario_description: str = Field(description="Stimulus, response, and context expressed as a scenario")
    priority_tuple: AtamPriorityTuple | None = Field(description="ATAM priority tuple, or null when not supported")


class AtamQualityAttributeNode(_StrictModel):
    """A quality attribute and its refined utility-tree scenarios."""

    attribute_name: str = Field(description="Name of the quality attribute")
    children: list[AtamUtilityScenario] = Field(description="Scenarios refining this attribute")


class AtamUtilityTree(_StrictModel):
    """Prioritized quality-attribute scenarios organized under a common root."""

    root: str = Field(description="Label for the utility-tree root")
    quality_attribute_nodes: list[AtamQualityAttributeNode] = Field(description="Top-level quality attributes and their scenarios")


class AtamAddressedAttribute(_StrictModel):
    """Quality attribute addressed by an architectural approach and why."""

    quality_attribute: str = Field(description="Quality attribute addressed")
    rationale: str = Field(description="Evidence-based explanation of how it is addressed")


class AtamArchitecturalApproach(_StrictModel):
    """Architectural decision or approach considered during the evaluation."""

    approach_name: str = Field(description="Name of the architectural approach")
    description: str = Field(description="Description grounded in the supplied architecture evidence")
    addressed_attributes: list[AtamAddressedAttribute] = Field(description="Quality attributes this approach addresses")


class AtamScenarioReference(_StrictModel):
    """Reference to a scenario used in an analysis record."""

    id: str = Field(description="Scenario identifier")
    text: str = Field(description="Scenario text")
    type: str = Field(description="Scenario category, such as utility-tree or evaluation scenario")


class AtamRisk(_StrictModel):
    """Risk or non-risk finding with its supporting rationale."""

    id: str = Field(description="Finding identifier")
    description: str = Field(description="Risk or non-risk statement")
    rationale: str = Field(description="Reasoning and evidence supporting the finding")


class AtamSensitivityPoint(_StrictModel):
    """A parameter whose small change can affect a quality attribute."""

    id: str = Field(description="Sensitivity-point identifier")
    parameter: str = Field(description="Architectural parameter that may change")
    correlated_attribute: str = Field(description="Quality attribute affected by the parameter")


class AtamTradeoffPoint(_StrictModel):
    """A parameter that creates competing effects across quality attributes."""

    id: str = Field(description="Tradeoff-point identifier")
    parameter: str = Field(description="Architectural parameter creating the tradeoff")
    conflicting_attributes: list[str] = Field(description="Quality attributes affected in conflicting ways")


class AtamAnalysisFindings(_StrictModel):
    """ATAM findings identified while analyzing an architectural approach."""

    risks: list[AtamRisk] = Field(description="Risks supported by the supplied evidence")
    non_risks: list[AtamRisk] = Field(description="Examined concerns that are not risks, with rationale")
    sensitivity_points: list[AtamSensitivityPoint] = Field(description="Parameters that influence a quality attribute")
    tradeoff_points: list[AtamTradeoffPoint] = Field(description="Parameters that create quality-attribute conflicts")


class AtamAnalysisRecord(_StrictModel):
    """Structured analysis of an approach in response to a specific scenario."""

    scenario_reference: AtamScenarioReference = Field(description="Scenario being analyzed")
    quality_attribute: str = Field(description="Primary quality attribute under analysis")
    environment: str = Field(description="Conditions under which the stimulus occurs")
    stimulus: str = Field(description="Event or condition that exercises the architecture")
    response_measure: str = Field(description="Observable response and its measure")
    architectural_decisions: list[str] = Field(description="Relevant decisions identified in the supplied evidence")
    reasoning: str = Field(description="Reasoning that connects decisions to the scenario response")
    findings: AtamAnalysisFindings = Field(description="Risks, non-risks, sensitivity points, and tradeoffs")


class AtamScenario(_StrictModel):
    """Evaluation scenario and the quality attributes it primarily exercises."""

    scenario_text: str = Field(description="Scenario expressed with stimulus, context, and response")
    primary_quality_attribute: list[str] = Field(description="Primary quality attributes exercised")


class AtamEvaluationResults(_StrictModel):
    """Generated analysis sections required by the ATAM report contract."""

    utility_tree: AtamUtilityTree = Field(description="Utility tree of prioritized quality-attribute scenarios")
    architectural_approaches: list[AtamArchitecturalApproach] = Field(description="Approaches considered in the evaluation")
    analysis_records: list[AtamAnalysisRecord] = Field(description="Scenario-based analyses and their findings")
    scenarios: list[AtamScenario] = Field(description="Scenarios used to evaluate the architecture")


class AtamReportPayload(_StrictModel):
    """Typed model output; the runner attaches original evaluation inputs separately."""

    metadata: AtamMetadata = Field(description="Evaluation metadata supported by the case")
    evaluation_results: AtamEvaluationResults = Field(description="Generated ATAM evaluation results")

# Keep task instructions independent of the user-provided case data.
SYSTEM_PROMPT = """You conduct a bounded, evidence-grounded ATAM software architecture evaluation.
Follow the evaluate-architecture and check-evaluation skills. Use only supplied
evaluation inputs. Do not invent stakeholder priorities, architectural decisions,
measurements, or source evidence. Mark unknowns and assumptions. Return the
structured metadata and evaluation_results required by the response schema. The
runner attaches the original evaluation_inputs after generation. An architect
must review the report before it is used for decisions."""

# These specialist roles share the same local skills but focus on distinct review tasks.
SUBAGENTS = [
    {
        "name": "quality-attribute-analyst",
        "description": "Refines quality attribute scenarios and analyzes approaches, risks, sensitivities, and tradeoffs.",
        "system_prompt": (
            "Analyze only supplied architecture evidence. Return scenario and analysis "
            "findings with source evidence, assumptions, and unresolved questions clearly separated."
        ),
        "skills": ["./skills/"],
    },
    {
        "name": "evidence-reviewer",
        "description": "Checks method coverage, evidence support, uncertainty, and ATAM report completeness.",
        "system_prompt": (
            "Review claims against supplied inputs. Flag unsupported findings, missing evidence, "
            "invented priorities, and unresolved gaps. Do not add architecture facts."
        ),
        "skills": ["./skills/"],
    },
]


def _load_case(path: Path) -> dict[str, Any]:
    """Extract only inputs intended for generation, excluding reference answers."""
    document = json.loads(path.read_text(encoding="utf-8"))
    try:
        inputs = document["ATAM_Evaluation"]["evaluation_inputs"]
    except (KeyError, TypeError) as exc:
        raise ValueError("input must contain ATAM_Evaluation.evaluation_inputs") from exc
    if not isinstance(inputs, dict):
        raise ValueError("ATAM_Evaluation.evaluation_inputs must be an object")
    return inputs


def _build_prompt(evaluation_inputs: dict[str, Any]) -> str:
    """Serialize the allowed case inputs into the model's task prompt."""
    return (
        "Evaluate this architecture using ATAM. Populate every field in the "
        "structured response. Use null or an empty list when metadata is unavailable; "
        "do not invent values.\n\n"
        f"Evaluation inputs:\n{json.dumps(evaluation_inputs, indent=2)}"
    )


def _compose_report(evaluation_inputs: dict[str, Any], payload: AtamReportPayload) -> dict[str, Any]:
    """Convert validated model output to JSON data and preserve the original inputs."""
    # Revalidation also supports callers that pass a plain mapping at runtime.
    validated = AtamReportPayload.model_validate(payload)
    return {
        "ATAM_Evaluation": {
            "metadata": validated.metadata.model_dump(mode="json"),
            "evaluation_inputs": evaluation_inputs,
            "evaluation_results": validated.evaluation_results.model_dump(mode="json"),
        }
    }


def _validate_report(report: dict[str, Any]) -> None:
    """Check required template sections and reject evaluation-only reference data."""
    expected = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    expected_root = expected["ATAM_Evaluation"]
    required = set(expected_root)
    actual = report.get("ATAM_Evaluation")
    if not isinstance(actual, dict):
        raise ValueError("model response must contain an ATAM_Evaluation object")
    if "ground_truth_outputs" in actual:
        raise ValueError("generated reports must not use the evaluation-only ground_truth_outputs field")
    missing = sorted(required - actual.keys())
    if missing:
        raise ValueError(f"ATAM_Evaluation is missing required sections: {', '.join(missing)}")
    if not isinstance(actual.get("metadata"), dict) or not isinstance(actual.get("evaluation_inputs"), dict):
        raise ValueError("metadata and evaluation_inputs must be objects")
    expected_results = set(expected_root["evaluation_results"])
    actual_results = actual.get("evaluation_results")
    if not isinstance(actual_results, dict):
        raise ValueError("evaluation_results must be an object")
    missing_results = sorted(expected_results - actual_results.keys())
    if missing_results:
        raise ValueError(f"evaluation_results is missing required sections: {', '.join(missing_results)}")


def run(case_path: Path, output_path: Path, model: str) -> None:
    try:
        from deepagents import FilesystemPermission, create_deep_agent
        from deepagents.backends.filesystem import FilesystemBackend
    except ImportError as exc:
        raise RuntimeError(
            "DeepAgents is required for this backend; install deepagents/requirements.txt"
        ) from exc

    # Give the agent a virtual view rooted at this example, with skills available locally.
    evaluation_inputs = _load_case(case_path)
    backend = FilesystemBackend(root_dir=str(HERE), virtual_mode=True)
    agent = create_deep_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        backend=backend,
        skills=["./skills/"],
        subagents=SUBAGENTS,
        response_format=AtamReportPayload,
        # The agent may analyze files but cannot write; only this runner emits the report.
        permissions=[
            FilesystemPermission(
                operations=["write"],
                paths=["/**"],
                mode="deny",
            )
        ],
    )
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": _build_prompt(evaluation_inputs),
                }
            ]
        }
    )
    messages = result.get("messages", [])
    if not messages:
        raise ValueError("DeepAgents returned no messages")
    # response_format returns a Pydantic instance in this dedicated result field.
    structured_response = result.get("structured_response")
    if structured_response is None:
        raise ValueError("DeepAgents returned no structured_response")
    report = _compose_report(evaluation_inputs, structured_response)
    _validate_report(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote ATAM report to {output_path}")


def main() -> int:
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise RuntimeError(
            "python-dotenv is required; install examples/atam/deepagents/requirements.txt"
        ) from exc
    # A shell-provided secret/configuration takes precedence over the local .env file.
    load_dotenv(ROOT / ".env", override=False)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="ATAM case JSON; only evaluation_inputs are sent to the model")
    parser.add_argument("--output", type=Path, required=True, help="path for the generated report JSON")
    args = parser.parse_args()
    model = os.environ.get("HW_ATAM_MODEL")
    if not model:
        parser.error("set HW_ATAM_MODEL to a supported provider:model identifier")
    run(args.case, args.output, model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
