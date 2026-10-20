"""Generate one immutable, structured SAAM WRCS pilot run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from benchmarks.saam import pilot

ROOT = Path(__file__).resolve().parents[2]
BASELINE_PROMPT = Path(__file__).with_name("baseline_prompt.md")
SPEC_GUIDED_PROMPT = Path(__file__).with_name("spec_guided_prompt.md")


class StrictModel(BaseModel):
    """Reject unrequested fields so both arms share a stable output contract."""

    model_config = ConfigDict(extra="forbid")


class Scenario(StrictModel):
    """One source scenario as represented in the case or generated report."""

    scenario_id: str = Field(description="The source scenario identifier")
    scenario_text: str = Field(description="Verbatim source scenario text")


class EvidenceReference(StrictModel):
    """One JSON Pointer to a source fact visible in the generation input."""

    source_pointer: str = Field(description="RFC 6901 JSON Pointer within the supplied evaluation inputs")


class EvidenceClaim(StrictModel):
    """A synthesized finding or recommendation with traceable source support."""

    statement: str
    evidence_refs: list[EvidenceReference] = Field(min_length=1)


class Classification(StrictModel):
    """SAAM direct/indirect classification and its evidence-based rationale."""

    scenario_id: str
    classification: str = Field(description="Direct or Indirect")
    rationale: str
    evidence_refs: list[EvidenceReference] = Field(min_length=1)


class ScenarioEvaluation(StrictModel):
    """Supported architecture impact analysis for one represented scenario."""

    scenario_id: str
    architecture_id: str | None = None
    affected_components: list[str] = Field(default_factory=list)
    change_description: str | None = None
    change_extent: str | None = None
    estimated_effort: str | None = None
    issues_identified: list[str] = Field(default_factory=list)
    evidence_refs: list[EvidenceReference] = Field(min_length=1)


class ScenarioInteraction(StrictModel):
    """Evidence-supported interaction between scenarios and shared components."""

    interaction_id: str
    interacting_scenarios: list[str] = Field(default_factory=list)
    shared_components: list[str] = Field(default_factory=list)
    interaction_effect: str | None = None
    modularity_implication: str
    evidence_refs: list[EvidenceReference] = Field(min_length=1)


class OverallResults(StrictModel):
    """Synthesis restricted to supported strengths and weaknesses."""

    architectural_strengths: list[EvidenceClaim] = Field(default_factory=list)
    architectural_weaknesses: list[EvidenceClaim] = Field(default_factory=list)
    modifiability_assessment: EvidenceClaim | None = None


class SaamEvaluation(StrictModel):
    """Shared generated report contract for the baseline and spec-guided arms."""

    scenarios: list[Scenario]
    scenario_classification: list[Classification]
    scenario_evaluations: list[ScenarioEvaluation]
    scenario_interactions: list[ScenarioInteraction]
    overall_results: OverallResults
    recommendations: list[EvidenceClaim]


def sha256_text(value: str) -> str:
    """Fingerprint prompt text without exposing provider credentials or hidden state."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_messages(instruction: str, input_body: dict[str, Any]) -> list[tuple[str, str]]:
    """Put the treatment instructions in the system message and case facts in the user message."""
    return [
        ("system", instruction),
        ("human", json.dumps(input_body, ensure_ascii=False, indent=2)),
    ]


def generate(run_id: str, arm: str, model_name: str) -> Path:
    """Call a LangChain chat model once and retain prompt, prediction, and settings."""
    if arm not in {"baseline", "spec-guided"}:
        raise ValueError("arm must be baseline or spec-guided")
    run_dir = pilot.prepare(run_id, arm)
    prompt_paths = [BASELINE_PROMPT]
    spec_path: Path | None = None
    spec_digest: str | None = None
    if arm == "spec-guided":
        prompt_paths.append(SPEC_GUIDED_PROMPT)
    instruction = ""
    prediction = run_dir / "prediction.json"
    settings: dict[str, Any] = {
        "provider_model": model_name,
        "temperature": None,
        "structured_output": "Pydantic SaamEvaluation",
        "instruction_treatment": arm,
        "prompt_files": [path.name for path in prompt_paths],
        "prompt_sha256": None,
        "instructions_passed_as_system_message": False,
        "harness_spec_sha256": None,
    }
    started: float | None = None
    latency: float | None = None
    try:
        instruction = "\n\n".join(path.read_text(encoding="utf-8") for path in prompt_paths)
        if arm == "spec-guided":
            spec_path = pilot.resolve(pilot.read_json(pilot.CONFIG_PATH)["harness_spec"])
            spec_bytes = spec_path.read_bytes()
            spec_content = spec_bytes.decode("utf-8")
            spec_digest = hashlib.sha256(spec_bytes).hexdigest()
            instruction += "\n\nHarnessSpec (YAML):\n" + spec_content
        (run_dir / "instructions.md").write_text(instruction, encoding="utf-8")
        settings.update({
            "prompt_sha256": sha256_text(instruction),
            "instructions_passed_as_system_message": True,
            "harness_spec_sha256": spec_digest,
        })

        # Load a root .env file if python-dotenv is installed; do not serialize its values.
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env", override=False)
        except ImportError:
            pass
        try:
            from langchain.chat_models import init_chat_model
        except ImportError as exc:
            raise RuntimeError("The harness environment must include LangChain and a provider integration") from exc

        input_doc = json.loads((run_dir / "evaluation_input.json").read_text(encoding="utf-8"))
        input_body = input_doc["SAAM_Evaluation_Extract"]["evaluation_inputs"]
        model = init_chat_model(model_name).with_structured_output(SaamEvaluation)
        started = time.perf_counter()
        output = model.invoke(build_messages(instruction, input_body))
        latency = time.perf_counter() - started
        if isinstance(output, BaseModel):
            output_data: dict[str, Any] = output.model_dump(mode="json")
        elif isinstance(output, dict):
            output_data = SaamEvaluation.model_validate(output).model_dump(mode="json")
        else:
            raise TypeError(f"structured model returned unsupported type: {type(output).__name__}")
        prediction.write_text(json.dumps({"SAAM_Evaluation": output_data}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        problems = pilot.check(prediction)
        status = "succeeded" if not problems else "partial"
        (run_dir / "checker.json").write_text(json.dumps({"checker_version": pilot.CHECKER_VERSION, "status": status, "problems": problems}, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        # Any failed run lifecycle remains visible without storing provider error text.
        if started is not None and latency is None:
            latency = time.perf_counter() - started
        pilot.record_execution(
            run_dir, arm=arm, runtime="langchain-single-call", model=model_name,
            settings=settings, prediction=prediction, latency_seconds=latency,
            status="failed", error_type=type(exc).__name__,
        )
        raise
    pilot.record_execution(
        run_dir, arm=arm, runtime="langchain-single-call", model=model_name,
        settings=settings, prediction=prediction, latency_seconds=latency,
        status=status,
    )
    return run_dir


def main() -> int:
    """Provide a small CLI so each arm is run independently and immutably."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--arm", choices=("baseline", "spec-guided"), required=True)
    parser.add_argument("--model", default=os.environ.get("HW_SAAM_MODEL", "openai:gpt-5.4-mini"))
    args = parser.parse_args()
    print(generate(args.run_id, args.arm, args.model))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
