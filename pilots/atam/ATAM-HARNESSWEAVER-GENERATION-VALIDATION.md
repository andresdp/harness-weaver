# ATAM pilot walkthrough: from case inputs to a checked DeepAgents run

This walkthrough follows the HarnessWeaver ArchEval-ATAM pilot from its authored inputs through generated harnesses and the first recorded execution. It describes the evidence available for the **DeepAgents banking run recorded on 25 October 2026**. It also distinguishes what has been validated mechanically from what still needs human review.

## Executive view

The experiment began with two different kinds of input:

1. **Generation inputs:** a runtime-independent intent, an ATAM methodology profile, domain skills, report contracts, and a set of recorded design answers. These described what an architecture evaluation assistant should do and how it should handle evidence, uncertainty, and review.
2. **Execution input:** a banking architecture case containing only `evaluation_inputs`. It was supplied later to the generated runtime. The case's `ground_truth_outputs` stayed outside the runtime sandbox for checking.

Claude Code used the generation inputs and HarnessWeaver skills to create a HarnessSpec 0.2 and target bundles for Claude Code and DeepAgents. The generated DeepAgents bundle then ran the banking case through five stages. The host recorded every stage as complete, and the output passed the external schema, ATAM-pilot, and reference-leakage checks.

There is an important qualification: the original generated review artifact flagged a performance-risk wording failure and a security-evidence warning. Those two findings were corrected in the recorded artifacts after the run, and the deterministic checks were rerun successfully. The report remains a draft and still requires architect review before decision use. This is a feasibility run, not evidence that the ATAM analysis is decision-ready.

## 1. The initial generation request

The starting prompt in `pilots/atam/prompts/generation.md` instructed Claude Code to:

> Build an agent harness that performs an evidence-grounded ATAM architecture evaluation, using the materials in `sources/` (start with `sources/intent.yaml`, `sources/methodology.yaml` and `sources/domain/`).

It set `generated/` as the output directory, required all new files to stay there, said the harness would later receive architecture evaluation inputs not included in the source directory, prohibited inventing case data, and asked Claude to ask questions before writing files.

That distinction matters: **the generation prompt did not include the banking case**. The design-time job was to produce a case-independent harness. The banking example was introduced later in an execution sandbox.

Generation ran in an isolated sandbox created for pilot `atam`, arm `harnessweaver`, with the recorded answers file:

```bash
hw sandbox create-generation atam \
  --arm harnessweaver \
  --answers pilots/atam/harness-answers.yaml
```

The answers file settled known choices, including a fresh build, a saved HarnessSpec, both target runtimes, use of the supplied report contract, and the bounded scope. Other design decisions remained interactive. Claude Code ran with the user's subscription login:

```bash
cd "/path/printed/by/create-generation"
ISOLATION=settings ./run.sh
```

The generation record identifies Claude Code version `2.1.283`, the `settings` isolation mode, and the saved session. The sandbox was named `gen-atam-harnessweaver-20261025T195652`. Its recorded session began at 19:57:43Z and finished at 20:40:08Z; that elapsed wall time includes the interactive session and should not be treated as measured hands-on implementation effort.

## 2. How the ATAM work was specified

The method and guardrails were authored in standalone pilot files before generation. They are the human-readable sources from which the HarnessSpec was elaborated.

### Intent: purpose, scope, and exclusions

`pilots/atam/sources/intent.yaml` defines the goal as producing an **evidence-grounded ATAM evaluation draft** for review by a software architect familiar with the system. The scope includes:

- Architecture description and supporting evidence.
- Business drivers and constraints.
- Quality-attribute drivers refined into prioritized scenarios.
- Architecture approaches and scenario analysis, including risks, non-risks, sensitivity points, and tradeoff points.
- Evidence-backed methodology state and open gaps.

The exclusions are equally central: the assistant must not conduct or simulate stakeholder workshops, invent stakeholder priorities or measurements, accept architecture decisions without expert review, or use reference evaluation outputs during generation. The intended output is a JSON report that remains `draft` until reviewed. Both `claude-code` and `deepagents` are named as target runtimes.

### Methodology: activities and readiness

`pilots/atam/sources/methodology.yaml` is a bounded, standalone ATAM adaptation profile. It describes five activities, their readiness conditions, and outputs:

| Activity | Ready when | Main outputs |
|---|---|---|
| Establish context | Evaluation inputs are present | System scope, business drivers, architecture evidence, open questions |
| Build utility tree | Business drivers are identified; unknowns remain explicit | Quality-attribute scenarios, priority tuples, response measures |
| Identify approaches | Architecture evidence is available | Architecture approaches and supporting evidence |
| Analyze scenarios | Scenarios and relevant evidence are available | Analysis records, risks, non-risks, sensitivity points, tradeoff points |
| Synthesize and review | Earlier artifacts exist and unresolved gaps are recorded | ATAM report and review findings |

It defines methodology semantic state separately from runtime activity. `context_status`, `driver_status`, and `architecture_evidence_status` use `missing`, `partial`, or `sufficient`; `scenario_analysis_status` uses `not_started`, `partial`, or `reviewed`; and `report_status` uses `not_started`, `draft`, or `reviewed`. Each state requires evidence. Tool calls, messages, checkpoints, and runtime task completion are explicitly not proof that the ATAM method progressed.

The profile allows a report draft from partial inputs only when material gaps and assumptions are explicit and unsupported claims are not presented as facts. A software architect familiar with the system must review method coverage, evidence grounding, risks, tradeoffs, and unknowns before decision use. Only a recorded architect review can move the report or analysis status to `reviewed`.

### Domain assets and output contract

`pilots/atam/sources/domain/` contains a source catalog, portable domain skills, a report JSON Schema, and a template. The source catalog documents the local authorities and provenance. The report contract is derived from the HarnessWeaver ATAM report model; the template is derived from the ArchEval ATAM template but uses `evaluation_results` for generated findings, keeping these distinct from the dataset's evaluator-only `ground_truth_outputs`.

The two domain skills have complementary purposes:

- `evaluate-architecture` guides the ATAM analysis and evidence-grounded report production.
- `check-evaluation` guides review of report structure, semantic state, evidence traceability, uncertainty, and methodology coverage.

The profile copies the necessary methodological guidance into local configuration and records its source basis. It adapts the source method by adding explicit readiness, evidence and gap tracking, a reference-data boundary, and human review.

## 3. The banking execution input and reference boundary

The execution case is `pilots/atam/cases/banking.yaml`. It binds the pilot to a sample event framework. Its `generation_inputs` describe:

- A framework in which application logic and framework components are interdependent.
- A Main module within the framework, an Event Manager, an Event Queue, and base and specialized handlers.
- Discovery inquiries about reuse, extensibility, invalid input, behavioral consistency, modifiability, component interaction, and event processing.
- Runtime constraints such as FIFO dispatch, idle waiting for input, and application logic embedded in framework components.
- Five stated business/architectural drivers: Variability, Reliability, Conceptual Integrity, Functionality, and Modifiability.
- Sixteen raw candidate scenarios, including handling user errors, recovery after failure, performance, security, extensibility, reuse, and consistency.

The case also has an `evaluator_only` section with reference approaches, utility-tree priorities, scenarios, and analysis records. That section is for evaluation by the external checker; it is **not** an input to the generation session or runtime. When an execution sandbox is created, HarnessWeaver extracts only `ATAM_Evaluation.evaluation_inputs` into the sandbox input file. The checker retains access to the original case and can detect leakage without revealing reference answers to the model.

## 4. From source files to HarnessSpec 0.2

The collected generation is `pilots/atam/generated/atam-hw-oauth-1/`. The main design artifact is `harnessspec.yaml`, with `spec_version: '0.2'` and ID `archeval-atam-harness`. It turns the intent and method into an explicit, runtime-neutral model.

### Intent and methodology in the model

The HarnessSpec carries the purpose, scope, exclusions, and report requirement into its `intent` section. Its `methodology` section names `atam-evaluation-methodology`, refers to the local source profile, and records key adaptations:

- Stakeholder roles from the source protocol are not simulated; the Customer is represented by the input port and the Architect by a human review gate.
- Intermediate artifacts carry `basis` values (observed, inferred, or assumption) and `source_refs` so evidence provenance can reach report reasoning.
- The harness never sets `scenario_analysis_status` to `reviewed` itself.

The `domain` describes architecture evaluation concepts such as business drivers, utility trees, scenarios, architecture approaches, and ATAM findings. The `sources` list associates each input with its kind, authority, and, where applicable, a content hash.

### Roles and declared artifacts

Six roles are specified: `context-analyst`, `utility-tree-analyst`, `approach-analyst`, `scenario-analyst`, `report-synthesizer`, and `evaluation-reviewer`. The roles refer to the domain skills, while later materializers express them using runtime-specific agent and skill conventions.

The HarnessSpec declares typed JSON artifact ports:

| Artifact | Direction | Purpose |
|---|---|---|
| `evaluation_inputs` | Input | Case input; rejects `ground_truth_outputs` and `evaluation_results` |
| `context` | Intermediate | Scope, business drivers, architecture evidence, questions, assessments, gaps |
| `utility_tree` | Intermediate | Quality attributes, measurable scenarios, evidence-based priorities, analysis order |
| `approaches` | Intermediate | Observed or inferred architecture approaches linked to evidence |
| `analysis` | Intermediate | Per-scenario ATAM records and explicit unanalyzed scenarios/gaps |
| `atam_report` | Output | Contract-conforming report draft with methodology state |
| `review_findings` | Output | Checks, unsupported claims, revision record, review readiness and architect focus |

The supplied report schema is used unchanged. Additional schemas define the intermediate artifacts and review findings, making each handoff checkable rather than leaving the model to compose one untyped narrative.

### Workflow and verification

The selected workflow is `atam-sequential-pipeline`, a five-stage pipeline aligned to the methodology table above. Stage inputs and outputs are explicit. The design notes say `identify-approaches` could run in parallel with `build-utility-tree` because it depends only on the case inputs and context; this DeepAgents materialization serializes it as stage 3.

The model defines verification criteria for:

- Keeping evaluator-only answers out of inputs and generated artifacts.
- Schema validation of intermediate and final artifacts.
- Cross-reference integrity for business-driver, architecture-evidence, approach, and scenario identifiers.
- Evidence traceability and distinction between observed information, inference, and assumption.
- Semantic-state values and evidence, including the `draft` ceiling before architect review.
- Gap preservation and coverage of every scenario or an explicit reason it was not analyzed.

An artifact that fails structural verification can be retried once with structural validation feedback; a second failure stops the pipeline rather than substituting guessed content. The HarnessSpec also records human gate `H1-architect-review` after synthesis and before decision use.

### Materialization into two runtime bundles

The same collected generation contains:

- `build/claude/`: Claude Code project instructions, generated skills, specialist subagent definitions, schemas, and a materialization report.
- `build/deepagents/`: a host wiring file, schemas, stage-specific `AGENTS.md` and skills, runner entry point, README, and materialization report.

This is the intended model-to-runtime mapping: the common task, artifact contracts, and methodology are represented in the HarnessSpec, while agent configuration, skill packaging, and orchestration details are runtime-specific. The bundles passing structural checks does not yet prove behaviorally equivalent execution.

Generation notes record that the 0.2 spec passed `hw validate` with SHA prefix `f35ed8f1…`, and both target bundles passed `hw check-bundle`. Those checks were performed in the generation sandbox before collection. They are materialization checks, separate from execution validation.

## 5. Collect the generated project

Once Claude Code finished, generation output was collected from the repository root:

```bash
hw sandbox collect \
  "/path/to/gen-atam-harnessweaver-20261025T195652" \
  --label atam-hw-oauth-1
```

Collection copied the generated specification, source snapshot, contracts, design notes, target builds, and provenance into `pilots/atam/generated/atam-hw-oauth-1/`. It also retained the Claude transcript and generation record. The generation record hashes source inputs and generated files, enabling the bundle and its origins to be inspected later.

The `design-notes.md` explains the choices and fidelity limits. In particular, it says the generated project did not contain case data; the DeepAgents reviewer is not an independent runtime/agent; and the design is a bounded profile, not a complete workshop process. These are relevant when interpreting the results.

## 6. Create and run the DeepAgents execution sandbox

An execution sandbox was created for:

- Pilot: `atam`
- Case: `banking`
- Target: `deepagents`
- Bundle: `pilots/atam/generated/atam-hw-oauth-1/build/deepagents`
- Requested model: `openai:gpt-5.4-mini`

The sandbox is `run-atam-deepagents-banking-20261025T225711`. Its `sandbox.yaml` records the bundle source, case binding, repository commit, target and model. Its manifest fingerprints the copied bundle and inputs. The isolated input is only `evaluation_inputs`; evaluator-only reference outputs were excluded.

The model provider credentials are separate from Claude Code subscription OAuth. The Claude subscription was used for generation; the DeepAgents execution called the configured OpenAI model and needed credentials for that provider.

From the printed execution-sandbox directory, the run command was:

```bash
./run.sh
```

The DeepAgents host loaded the generated wiring and ran these five stages in order:

1. `stage1-establish_context` wrote `01_context.json`.
2. `stage2-build_utility_tree` wrote `02_utility_tree.json`.
3. `stage3-identify_approaches` wrote `03_approaches.json`.
4. `stage4-analyze_scenarios` wrote `04_analysis.json`.
5. `stage5-synthesize_and_review` wrote `05_atam_report.json` and `06_review_findings.json`.

For this run, Pydantic structured output was active for every stage. The host record shows **zero repair attempts** on all five stages. The stage 5 report and review findings were separate outputs. The review findings were produced within the configured stage, however; the design notes explicitly do not treat that as an independent DeepAgents reviewer.

The report contains 15 utility-tree scenarios, 15 analysis records, and five architectural approaches. Its semantic state records context, driver, and architecture-evidence status as `sufficient`, scenario-analysis status as `partial`, and report status as `draft`. This does not mean all uncertainty is resolved: gaps are retained, and the architect review gate remains pending.

## 7. External checks and review findings

After the run, the sandbox was checked outside its runtime environment:

```bash
hw check "/path/to/run-atam-deepagents-banking-20261025T225711"
```

The recorded `check.json` shows:

| Check | Result | Meaning |
|---|---|---|
| `no-reference-leakage` | PASS | The evaluator-only reference answers were not leaked into the runtime input/output. |
| `schema` | PASS | The final report conforms to the declared report schema. |
| `atam-pilot` | PASS | The deterministic ATAM-pilot checks passed. |

Evidence was copied to the repository with:

```bash
hw sandbox record "/path/to/run-atam-deepagents-banking-20261025T225711"
```

The resulting package is `docs/cain-2027/evidence/run-atam-deepagents-banking-20261025T225711/`. It includes `sandbox.yaml`, a hash manifest, `check.json`, host record, timestamps and exit status, runbook, final report, and all stage artifacts.

The external checks must be read alongside `workspace/artifacts/06_review_findings.json`. In the original model-produced review, the stage:

- Structure and semantic-state checks passed.
- Method coverage passed: all 15 scenarios had analysis records.
- Reference-boundary review passed.
- Flagged R-2 because it was labeled `observed` despite drawing an inference from qualitative performance evidence.
- Warned that R-1 cited `G-3-3`, a gap identifier, as if it were an architecture evidence reference.
- Reported `revision.applied: false` and left `ready_for_architect_review: false`, despite the generated workflow specifying one revision pass.

The two findings were then corrected in the recorded stage 4 artifact and report: R-2 is explicitly an inference, with the missing workload, benchmark, and response-time target stated; R-1 cites only architecture evidence IDs and treats the absence of security controls as an unresolved inference. The review artifact now records those corrections, and `hw check` was rerun against the revised evidence package; all three checks still pass. `post-run-revision.md` records that this was a human editorial correction after the model run. The host record remains the original runtime record.

The green `hw check` results establish schema and configured pilot-rule validity; they do not substitute for a software architect's review of whether the analysis is substantively sound.

## 8. What is demonstrated, and what is still open

### Demonstrated by the recorded run

- The authored intent and ATAM methodology were expressed as a versioned HarnessSpec 0.2.
- The same generation produced Claude and DeepAgents bundles from shared pilot sources.
- The DeepAgents bundle executed all five stages on a banking case without structural repairs.
- Structured output was enabled at every stage in the successful run.
- The report passed the three external checks, and the execution inputs and outputs were recorded with provenance.
- Two review findings were corrected in a transparent post-run edit, and the revised artifacts passed the external checks again.

### Still needed before broader paper claims

- Run, check, and record the generated Claude target on the same ATAM banking case to examine runtime-specific artifacts and interventions.
- Run and record the Korean baseline with English-translated skills, capturing equivalent input, model/runtime settings, effort, corrections, and changed files.
- Obtain a recorded architect review before describing the report as ready for decision use.
- The generation prompt and saved answers now require report synthesis, review, and revision as separate runtime stages. The collected bundle described in this walkthrough has not been regenerated, so those workflow changes take effect in the next generation.
- **Runtime review-independence follow-up:** In the collected bundles, Claude uses a separate reviewer agent and can send findings to the synthesizer for one revision; DeepAgents performs synthesis, review, and revision as ordered tasks within the same Stage 5 agent. This difference comes from the target-specific generation choices and mapping: G5 sets DeepAgents `subagents: false`, and the current DeepAgents host creates one agent per stage without configuring subagents. It is not a difference in the shared ATAM method. Before the next generation, decide whether DeepAgents needs a separately delegated reviewer. If so, update the target design and host/adapter support as well as the G5 choice; changing the answer alone will not make the current host independent. Regenerate and check the bundle, then compare the review behavior across runtimes.
- Do not infer time savings, lower implementation effort, runtime equivalence, or superior assistant quality from this single successful DeepAgents run. Those require measured comparisons.
- A second domain such as Architecture Design/SARA is an additional scope item, not evidence present in this run.

## File map for reproducing and auditing the walkthrough

| Purpose | Repository location |
|---|---|
| Generation prompt | `pilots/atam/prompts/generation.md` |
| Recorded generation decisions | `pilots/atam/harness-answers.yaml` |
| Pilot identity and sources | `pilots/atam/pilot.yaml`, `pilots/atam/sources/` |
| ATAM intent | `pilots/atam/sources/intent.yaml` |
| ATAM activity/state profile | `pilots/atam/sources/methodology.yaml` |
| Banking case and evaluator-only data | `pilots/atam/cases/banking.yaml` |
| Generated model and notes | `pilots/atam/generated/atam-hw-oauth-1/harnessspec.yaml`, `design-notes.md` |
| Runtime materializations | `pilots/atam/generated/atam-hw-oauth-1/build/claude/`, `build/deepagents/` |
| Generation provenance | `pilots/atam/generated/atam-hw-oauth-1/generation-record.json` |
| DeepAgents execution evidence | `docs/cain-2027/evidence/run-atam-deepagents-banking-20261025T225711/` |
| General sandbox commands | `docs/cain-2027/SANDBOX-RUNBOOK.md` |
