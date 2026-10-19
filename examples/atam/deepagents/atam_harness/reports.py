"""Load typed case inputs and compose, validate, and write report models."""

import json
from pathlib import Path

from .models import (
    AtamCaseDocument,
    AtamCaseInputs,
    AtamReportContent,
    AtamReportDocument,
    AtamReportPayload,
)


def load_case(path: Path) -> AtamCaseInputs:
    """Load the allowed evaluation inputs into a model, ignoring reference outputs."""
    source = AtamCaseDocument.model_validate_json(path.read_text(encoding="utf-8"))
    return AtamCaseInputs(evaluation_inputs=source.atam_evaluation.evaluation_inputs)


def compose_report(
    case: AtamCaseInputs,
    payload: AtamReportPayload,
    session_id: str,
) -> AtamReportDocument:
    """Convert model output into the complete typed report and preserve source inputs."""
    # Revalidate both public inputs to guard against dynamically constructed values.
    validated_case = AtamCaseInputs.model_validate(case)
    validated_payload = AtamReportPayload.model_validate(payload)
    return AtamReportDocument(
        atam_evaluation=AtamReportContent(
            # This runner-owned title keeps the generated report linked to its run.
            title=f"ATAM Evaluation — Session {session_id}",
            metadata=validated_payload.metadata,
            evaluation_inputs=validated_case.evaluation_inputs,
            evaluation_results=validated_payload.evaluation_results,
        )
    )


def validate_report(report: AtamReportDocument) -> AtamReportDocument:
    """Revalidate the complete report against the typed JSON contract."""
    # Pydantic enforces required report sections and forbids fields such as ground_truth_outputs.
    return AtamReportDocument.model_validate(report)


def session_output_path(output_path: Path, session_id: str) -> Path:
    """Add the run ID to the requested report filename while preserving its folder."""
    return output_path.with_name(f"{output_path.stem}-{session_id}{output_path.suffix or '.json'}")


def write_report(report: AtamReportDocument, output_path: Path, session_id: str) -> Path:
    """Validate and serialize the typed report at a session-specific path."""
    validated_report = validate_report(report)
    destination = session_output_path(output_path, session_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    serialized = validated_report.model_dump(mode="json", by_alias=True)
    destination.write_text(json.dumps(serialized, indent=2) + "\n", encoding="utf-8")
    return destination
