"""Load typed case inputs and compose, validate, and write report models."""

import json
import hashlib
import os
import secrets
import stat
from pathlib import Path

from harnessweaver._integrity import sha256_file
from harnessweaver.runtime import RunResult

from .config import ResolvedRunConfig
from .models import (
    AtamCaseDocument,
    AtamCaseInputs,
    AtamReportContent,
    AtamReportDocument,
    AtamReportPayload,
    AtamRunRecord,
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
    temporary_path: Path | None = None
    file_descriptor: int | None = None
    try:
        # Publish only after the complete JSON is flushed, so cancellation cannot leave a partial report.
        for _ in range(100):
            candidate_path = destination.parent / f".{destination.name}.{secrets.token_hex(8)}.tmp"
            try:
                # Match Path.write_text's normal 0666-and-umask permissions for new reports.
                file_descriptor = os.open(
                    candidate_path,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o666,
                )
                temporary_path = candidate_path
                break
            except FileExistsError:
                continue
        else:
            raise FileExistsError("could not allocate a unique temporary report file")

        try:
            # Path.write_text preserves an existing target's permission bits when truncating it.
            existing_mode = stat.S_IMODE(destination.stat().st_mode)
        except FileNotFoundError:
            existing_mode = None
        if existing_mode is not None:
            os.fchmod(file_descriptor, existing_mode)

        with os.fdopen(file_descriptor, "w", encoding="utf-8") as temporary_file:
            file_descriptor = None
            temporary_file.write(json.dumps(serialized, indent=2) + "\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, destination)
    except BaseException:
        if file_descriptor is not None:
            os.close(file_descriptor)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return destination


def _sha256_file_if_readable(path: Path) -> str | None:
    """Keep a run record writable when the filesystem cannot provide a fingerprint."""
    try:
        return sha256_file(path)
    except OSError:
        # A transient read timeout must not hide the original agent failure or
        # prevent a successfully written report from receiving its sidecar.
        return None


def compose_run_record(
    case: AtamCaseInputs | None,
    config: ResolvedRunConfig,
    result: RunResult | None,
    report_path: Path | None,
    session_id: str,
    *,
    error: BaseException | None = None,
    elapsed_seconds: float | None = None,
) -> AtamRunRecord:
    """Capture effective settings and success/failure evidence for one run."""
    serialized_inputs = (
        json.dumps(
            case.evaluation_inputs,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        if case is not None
        else None
    )
    return AtamRunRecord(
        record_version="0.2",
        status="failed" if error is not None or (result and result.status != "succeeded") else "succeeded",
        session_id=session_id,
        runtime="deepagents",
        model=config.model,
        request_timeout_seconds=config.request_timeout_seconds,
        case_path=config.case,
        case_sha256=_sha256_file_if_readable(config.case),
        evaluation_inputs_sha256=hashlib.sha256(serialized_inputs).hexdigest() if serialized_inputs else None,
        harness_spec_path=config.harness_spec,
        harness_spec_sha256=_sha256_file_if_readable(config.harness_spec),
        workflow_strategy=config.workflow_strategy,
        agent_interaction=config.agent_interaction,
        streaming=config.streaming,
        verbose=config.verbose,
        report_path=report_path,
        report_sha256=_sha256_file_if_readable(report_path) if report_path is not None else None,
        elapsed_seconds=result.elapsed_seconds if result is not None else elapsed_seconds,
        cost_usd=None,
        capabilities=list(result.capabilities) if result is not None else [],
        approximations=list(result.approximations) if result is not None else [],
        unsupported=list(result.unsupported) if result is not None else [],
        error_type=type(error).__name__ if error is not None else None,
        # Provider exceptions may contain headers, URLs, or credentials; keep only the type in persisted records.
        error_message="Error details omitted from persistent record." if error is not None else None,
    )


def write_run_record(record: AtamRunRecord, target: Path | None = None) -> Path:
    """Write session metadata beside its report without replacing an earlier record."""
    if target is None:
        if record.report_path is None:
            raise ValueError("a target path is required for a run without a report")
        target = record.report_path.with_suffix(".runtime.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(record.model_dump(mode="json"), indent=2) + "\n"
    with target.open("x", encoding="utf-8") as destination:
        destination.write(serialized)
    return target
