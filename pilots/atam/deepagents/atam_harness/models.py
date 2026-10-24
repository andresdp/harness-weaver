"""Pydantic contracts for ATAM model output and runner configuration."""

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """Base for report models that reject fields outside the agreed contract."""

    # The generated report shape is an explicit contract, so unknown fields fail validation.
    model_config = ConfigDict(extra="forbid", revalidate_instances="always")


class AtamMetadata(StrictModel):
    """Known evaluation context; nullable values mark metadata absent from the case."""

    system_name: str | None = Field(description="Evidence-based system name, or null if unavailable")
    date: str | None = Field(description="Evaluation date, or null if unavailable")
    ref: str | None = Field(description="Source reference, or null if unavailable")
    evaluator_organization: str | None = Field(description="Evaluator organization, or null if unavailable")
    phase_1_attendees: list[str] = Field(description="Known phase 1 attendee roles; use an empty list if unavailable")
    phase_2_attendees: list[str] = Field(description="Known phase 2 attendee roles; use an empty list if unavailable")


class AtamPriorityTuple(StrictModel):
    """Relative importance and difficulty assigned to a utility-tree scenario."""

    importance: str = Field(description="Relative importance of achieving this scenario")
    difficulty: str = Field(description="Relative difficulty of achieving this scenario")


class AtamUtilityScenario(StrictModel):
    """A measurable quality-attribute scenario in the utility tree."""

    refinement: str = Field(description="Refinement level or grouping for the scenario")
    scenario_id: str = Field(description="Stable identifier for this scenario")
    scenario_description: str = Field(description="Stimulus, response, and context expressed as a scenario")
    priority_tuple: AtamPriorityTuple | None = Field(description="ATAM priority tuple, or null when not supported")


class AtamQualityAttributeNode(StrictModel):
    """A quality attribute and its refined utility-tree scenarios."""

    attribute_name: str = Field(description="Name of the quality attribute")
    children: list[AtamUtilityScenario] = Field(description="Scenarios refining this attribute")


class AtamUtilityTree(StrictModel):
    """Prioritized quality-attribute scenarios organized under a common root."""

    root: str = Field(description="Label for the utility-tree root")
    quality_attribute_nodes: list[AtamQualityAttributeNode] = Field(description="Top-level quality attributes and their scenarios")


class AtamAddressedAttribute(StrictModel):
    """Quality attribute addressed by an architectural approach and why."""

    quality_attribute: str = Field(description="Quality attribute addressed")
    rationale: str = Field(description="Evidence-based explanation of how it is addressed")


class AtamArchitecturalApproach(StrictModel):
    """Architectural decision or approach considered during the evaluation."""

    approach_name: str = Field(description="Name of the architectural approach")
    description: str = Field(description="Description grounded in the supplied architecture evidence")
    addressed_attributes: list[AtamAddressedAttribute] = Field(description="Quality attributes this approach addresses")


class AtamScenarioReference(StrictModel):
    """Reference to a scenario used in an analysis record."""

    id: str = Field(description="Scenario identifier")
    text: str = Field(description="Scenario text")
    type: str = Field(description="Scenario category, such as utility-tree or evaluation scenario")


class AtamRisk(StrictModel):
    """Risk or non-risk finding with its supporting rationale."""

    id: str = Field(description="Finding identifier")
    description: str = Field(description="Risk or non-risk statement")
    rationale: str = Field(description="Reasoning and evidence supporting the finding")


class AtamSensitivityPoint(StrictModel):
    """A parameter whose small change can affect a quality attribute."""

    id: str = Field(description="Sensitivity-point identifier")
    parameter: str = Field(description="Architectural parameter that may change")
    correlated_attribute: str = Field(description="Quality attribute affected by the parameter")


class AtamTradeoffPoint(StrictModel):
    """A parameter that creates competing effects across quality attributes."""

    id: str = Field(description="Tradeoff-point identifier")
    parameter: str = Field(description="Architectural parameter creating the tradeoff")
    conflicting_attributes: list[str] = Field(description="Quality attributes affected in conflicting ways")


class AtamAnalysisFindings(StrictModel):
    """ATAM findings identified while analyzing an architectural approach."""

    risks: list[AtamRisk] = Field(description="Risks supported by the supplied evidence")
    non_risks: list[AtamRisk] = Field(description="Examined concerns that are not risks, with rationale")
    sensitivity_points: list[AtamSensitivityPoint] = Field(description="Parameters that influence a quality attribute")
    tradeoff_points: list[AtamTradeoffPoint] = Field(description="Parameters that create quality-attribute conflicts")


class AtamAnalysisRecord(StrictModel):
    """Structured analysis of an approach in response to a specific scenario."""

    scenario_reference: AtamScenarioReference = Field(description="Scenario being analyzed")
    quality_attribute: str = Field(description="Primary quality attribute under analysis")
    environment: str = Field(description="Conditions under which the stimulus occurs")
    stimulus: str = Field(description="Event or condition that exercises the architecture")
    response_measure: str = Field(description="Observable response and its measure")
    architectural_decisions: list[str] = Field(description="Relevant decisions identified in the supplied evidence")
    reasoning: str = Field(description="Reasoning that connects decisions to the scenario response")
    findings: AtamAnalysisFindings = Field(description="Risks, non-risks, sensitivity points, and tradeoffs")


class AtamEvidenceBasis(StrictModel):
    """Evidence-backed basis shared by ATAM methodology status assessments."""

    evidence: list[str] = Field(
        min_length=1,
        description="At least one observed input or artifact fact supporting this status, including evidence of absence",
    )

    @field_validator("evidence")
    @classmethod
    def evidence_items_must_contain_text(cls, evidence: list[str]) -> list[str]:
        # Match the benchmark contract: whitespace alone is not evidence.
        if any(not item.strip() for item in evidence):
            raise ValueError("evidence items must contain non-whitespace text")
        return evidence


class AtamAvailabilityAssessment(AtamEvidenceBasis):
    """Status for context, drivers, or architecture evidence availability."""

    value: Literal["missing", "partial", "sufficient"] = Field(description="Availability status")


class AtamReviewAssessment(AtamEvidenceBasis):
    """Status for analysis or report review progress."""

    value: Literal["not_started", "partial", "reviewed"] = Field(description="Review progress status")


class AtamReportAssessment(AtamEvidenceBasis):
    """Status for report drafting and review progress."""

    value: Literal["not_started", "draft", "reviewed"] = Field(description="Report progress status")


class AtamEvidenceGap(StrictModel):
    """A missing item that limits an ATAM activity or finding."""

    description: str = Field(min_length=1, description="What is unknown, conflicting, or incomplete")
    affected_activity: str = Field(min_length=1, description="ATAM methodology activity affected by this gap")
    missing_evidence: str = Field(min_length=1, description="Evidence needed to resolve or reduce the gap")
    resolution_question: str = Field(
        min_length=1,
        description="Question for the architect or stakeholder who can resolve the gap",
    )

    @field_validator("description", "affected_activity", "missing_evidence", "resolution_question")
    @classmethod
    def gap_fields_must_contain_text(cls, value: str) -> str:
        # Keep typed reports consistent with the deterministic report checker.
        if not value.strip():
            raise ValueError("gap fields must contain non-whitespace text")
        return value


class AtamSemanticState(StrictModel):
    """ATAM progress semantics kept distinct from runtime execution status."""

    context_status: AtamAvailabilityAssessment = Field(description="Evidence-backed status for evaluation context")
    driver_status: AtamAvailabilityAssessment = Field(description="Evidence-backed status for quality attribute drivers")
    architecture_evidence_status: AtamAvailabilityAssessment = Field(
        description="Evidence-backed status for architecture evidence"
    )
    scenario_analysis_status: AtamReviewAssessment = Field(
        description="Evidence-backed status for scenario analysis; reviewed requires review evidence"
    )
    report_status: AtamReportAssessment = Field(
        description="Evidence-backed status for report drafting and review"
    )
    gaps: list[AtamEvidenceGap] = Field(description="Material evidence gaps and questions that remain unresolved")


class AtamScenario(StrictModel):
    """Evaluation scenario and the quality attributes it primarily exercises."""

    scenario_text: str = Field(description="Scenario expressed with stimulus, context, and response")
    primary_quality_attribute: list[str] = Field(description="Primary quality attributes exercised")


class AtamEvaluationResults(StrictModel):
    """Generated analysis sections required by the ATAM report contract."""

    utility_tree: AtamUtilityTree = Field(description="Utility tree of prioritized quality-attribute scenarios")
    architectural_approaches: list[AtamArchitecturalApproach] = Field(description="Approaches considered in the evaluation")
    analysis_records: list[AtamAnalysisRecord] = Field(description="Scenario-based analyses and their findings")
    scenarios: list[AtamScenario] = Field(description="Scenarios used to evaluate the architecture")
    semantic_state: AtamSemanticState = Field(
        description="Evidence-based ATAM progress, independent of agent calls and runtime task completion"
    )


class AtamReportPayload(StrictModel):
    """Typed model output; the runner attaches original evaluation inputs separately."""

    metadata: AtamMetadata = Field(description="Evaluation metadata supported by the case")
    evaluation_results: AtamEvaluationResults = Field(description="Generated ATAM evaluation results")


class AtamContextArtifact(StrictModel):
    """Typed context handoff used by sequential and fan-out strategies."""

    metadata: AtamMetadata = Field(description="Known evaluation metadata, leaving unsupported fields null")
    scope_summary: str = Field(description="Concise scope and business-driver summary grounded in the case")
    evidence_gaps: list[str] = Field(description="Missing or uncertain inputs that downstream agents must preserve")


class AtamUtilityTreeArtifact(StrictModel):
    """Utility-tree output and its evaluation scenarios for a declared pipeline stage."""

    utility_tree: AtamUtilityTree = Field(description="Prioritized quality-attribute scenarios")
    scenarios: list[AtamScenario] = Field(description="Evaluation scenarios and their primary quality attributes")


class AtamArchitectureApproachesArtifact(StrictModel):
    """Architecture approaches emitted by the dedicated identification stage."""

    architectural_approaches: list[AtamArchitecturalApproach] = Field(description="Evidence-based architecture approaches")


class AtamPlanningArtifact(StrictModel):
    """Typed utility-tree and architecture-approach work product."""

    utility_tree: AtamUtilityTree = Field(description="Prioritized quality-attribute scenarios")
    architectural_approaches: list[AtamArchitecturalApproach] = Field(description="Evidence-based architecture approaches")
    scenarios: list[AtamScenario] = Field(description="Evaluation scenarios")


class AtamScenarioAnalysisArtifact(StrictModel):
    """Typed analysis records produced by the scenario specialist."""

    analysis_records: list[AtamAnalysisRecord] = Field(description="Scenario-based reasoning and ATAM findings")


class AtamCaseBody(BaseModel):
    """Case-file section containing evaluation inputs and optional reference data."""

    # The source case can carry unrelated metadata and ground truth, which are ignored here.
    model_config = ConfigDict(extra="ignore")

    evaluation_inputs: dict[str, Any] = Field(description="Case inputs that are allowed into generation")


class AtamCaseDocument(BaseModel):
    """Typed view of the source JSON envelope, excluding unrelated root fields."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    atam_evaluation: AtamCaseBody = Field(alias="ATAM_Evaluation", description="ATAM case envelope")


class AtamCaseInputs(StrictModel):
    """Validated evaluation-input payload loaded from an ATAM case file."""

    # Input keys vary by case study, so preserve their JSON shape in this single open map.
    evaluation_inputs: dict[str, Any] = Field(description="Case data permitted for evaluation")


class AtamReportContent(StrictModel):
    """Complete report section persisted under the ATAM_Evaluation JSON key."""

    title: str = Field(description="Report title containing the unique session ID")
    metadata: AtamMetadata = Field(description="Evaluation metadata supported by the case")
    # Preserve the source case payload as JSON while keeping the surrounding report typed.
    evaluation_inputs: dict[str, Any] = Field(description="Original evaluation inputs")
    evaluation_results: AtamEvaluationResults = Field(description="Generated ATAM evaluation results")


class AtamReportDocument(StrictModel):
    """Typed top-level JSON report with the legacy uppercase key as its serialized alias."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, revalidate_instances="always")

    atam_evaluation: AtamReportContent = Field(alias="ATAM_Evaluation", description="Generated ATAM evaluation")


class DeepAgentSubagent(StrictModel):
    """Validated specialist definition loaded from the backend's agent YAML file."""

    name: str = Field(description="Subagent identifier used by DeepAgents task delegation")
    description: str = Field(description="Short description used by the coordinator to select this specialist")
    system_prompt: str = Field(description="Specialist instructions")
    skills: list[str] = Field(default_factory=list, description="Skill directories exposed to this specialist")


class DeepAgentDefinitions(StrictModel):
    """External agent configuration document."""

    subagents: list[DeepAgentSubagent] = Field(description="Named specialist agents available to the coordinator")


class AtamRunRecord(StrictModel):
    """Session-scoped execution and adapter-fidelity metadata for one generated report."""

    record_version: str = Field(description="Version of this runtime record contract")
    status: str = Field(description="Outcome of the run that produced the report")
    session_id: str = Field(description="Session identifier shared with the ATAM report title and filename")
    runtime: str = Field(description="Runtime adapter that produced the report")
    model: str = Field(description="LangChain provider:model identifier used for generation")
    request_timeout_seconds: float = Field(description="Maximum duration configured for each provider request")
    case_path: Path = Field(description="Source case file used to prepare evaluation inputs")
    case_sha256: str | None = Field(description="Fingerprint of the source case, when it could be read")
    evaluation_inputs_sha256: str | None = Field(description="Fingerprint of generation-visible inputs, when loaded")
    harness_spec_path: Path = Field(description="HarnessSpec used to configure this run")
    harness_spec_sha256: str | None = Field(description="Fingerprint of the HarnessSpec, when it could be read")
    workflow_strategy: str = Field(description="Effective workflow strategy after CLI overrides")
    agent_interaction: str = Field(description="Effective specialist interaction style after CLI overrides")
    streaming: bool = Field(description="Whether execution events were streamed")
    verbose: bool = Field(description="Whether progress events were displayed")
    report_path: Path | None = Field(description="Session-specific generated report path, when one was written")
    report_sha256: str | None = Field(description="Fingerprint of the generated report, when one was written")
    elapsed_seconds: float | None = Field(description="Elapsed adapter execution time, if available")
    cost_usd: float | None = Field(description="Provider cost in USD, or null when unavailable")
    capabilities: list[str] = Field(description="Runtime capabilities exercised by this run")
    approximations: list[str] = Field(description="Runtime behaviors approximated during this run")
    unsupported: list[str] = Field(description="Declared behaviors this runtime does not support")
    error_type: str | None = Field(description="Exception type when the run failed")
    error_message: str | None = Field(description="Safe failure note; raw provider exception text is not persisted")
