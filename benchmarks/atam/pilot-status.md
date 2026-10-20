# ArchEval ATAM banking pilot status

**Protocol:** `pilot.json` and `pilot.py` in this directory. **Status:** an earlier adapter revision has one successful provider-backed run per declared DeepAgents orchestration profile. Current five-stage adapter verification is tracked separately below. The report contract now requires evidence-backed semantic methodology state; only the refreshed supervisor profile has passed that contract so far. Live Claude validation and generation are deferred; see `examples/atam/CLAUDE-TESTING.md` for the handoff.

> **Run stopped (2026-10-20):** The current-contract sequential retry was stopped at the user's request after several minutes without producing a report. Do not treat it as a completed run; its failed execution record is listed below. Further sequential provider runs are deferred so verification does not wait indefinitely.

## Matched orchestration profile trial on the earlier adapter revision

The three successful trials used the same prepared banking evaluation input, HarnessSpec v0.2, model (`openai:gpt-5.4-mini`), non-streaming/non-verbose settings, and frozen harness asset digest (`6e4db7bc46801eb989906e0d2198b2ef05c3d39a733e0c068267e1faf9e13375`). Each prediction passed `pilot.py check`, including required ATAM sections and exact scenario references.

On 2026-10-20, the checker was tightened to take reference scenarios from the configured source case rather than from `evaluation_inputs` echoed inside each prediction. The supervisor, sequential, and fan-out predictions listed above were rechecked against that source and passed. These checks did not rerun the model; the manifests keep their original asset digests. The runner now records failed provider attempts as session-matched runtime sidecars and persists the configured per-request timeout.

After the filesystem read allowlist and request timeout were added, the current implementation was run once per profile on 2026-10-20. All three wrote a report and runtime sidecar, and all three reports passed the source-bound structural checker. The session-specific outputs remain in the ignored `examples/atam/deepagents/runs/` directory.

| Workflow strategy | Session ID | Runtime | Structural check |
| --- | --- | ---: | --- |
| `supervisor` | `d6fbf0bf-a73a-4d88-bc3a-60bb000c7315` | 57.68 s | Passed |
| `sequential_pipeline` | `f2ca45b7-78be-42e8-aeaa-37b97c834514` | 29.93 s | Passed |
| `fan_out_fan_in` | `96a62769-aa11-4b01-9165-736fac9cd26f` | 124.69 s | Passed |

These reruns verify that all three coordination paths can load their skills through the narrowed filesystem permissions and return reports under the configured timeout. They are single runs on one case; timing and output quality are not compared.

| Workflow strategy | Interaction style | Run record | Latency |
| --- | --- | --- | ---: |
| `supervisor` | `one_shot_specialist_delegation` | `runs/u7-compare2-supervisor-retry-20261019/execution.json` | 41.44 s |
| `sequential_pipeline` | `typed_artifact_handoffs` | `runs/u7-compare2-sequential-20261019/execution.json` | 77.68 s |
| `fan_out_fan_in` | `parallel_specialist_delegation` | `runs/u7-compare2-fanout-20261019/execution.json` | 46.72 s |

After aligning the sequential DeepAgents adapter with the five stage IDs declared by HarnessSpec v0.2, a fresh provider-backed run completed on 2026-10-20. Session `9a394dd6-487b-4044-8aac-96e440c39c52` used `sequential_pipeline` plus `typed_artifact_handoffs`, wrote the session report and runtime sidecar under `examples/atam/deepagents/runs/`, and passed the deterministic ATAM source-scenario checker. The five observed calls were `establish-context`, `build-utility-tree`, `identify-approaches`, `analyze-scenarios`, and `synthesize-and-review`; elapsed runtime was 105.41 seconds. This validates the declared stage mapping for one run, not quality or relative latency.

The current five-stage adapter also completed a fresh `supervisor` run on the same case, model, presentation settings, and asset digest. Session `b6d2f4a1-90c9-462d-9a18-3a6d6fa8c59d` completed in 49.82 seconds and passed the deterministic source-scenario checker. A current-version `fan_out_fan_in` attempt failed with `OpenAIConnectionError` before producing a prediction; its failure is recorded in `runs/u7-current-fanout-retry-20261020/execution.json`. The runner also encountered a transient filesystem timeout while trying to fingerprint that failed attempt. Run-record fingerprinting now treats unreadable files as unavailable fingerprints, and a focused regression test plus the full suite pass. One retry outside the sandbox remained live for over 30 minutes without producing a report and was interrupted. Its record is in `runs/u7-current-fanout-escalated-interrupted-20261020/execution.json`, but the run directory was prepared after interruption; its asset digest is a later snapshot and does not prove which revision the attempt executed. No report or model session ID was retained for that retry. Therefore the earlier successful fan-out record remains evidence for the previous prompt revision, but a matched fan-out run against the current five-stage assets is still outstanding. These trials do not establish output quality or relative latency.

These are single observations on one case. They show that each declared orchestration profile can produce a structurally valid ATAM report; they do not establish relative quality, accuracy, completeness, or reliable latency differences. Model cost was unavailable. An earlier supervisor attempt against the same frozen assets stalled and is retained as a failed record; the successful retry above completed.

## Evidence-linked prompt evolution

The sequential profile produced a report under the preceding prompt revision, but its deterministic check rejected two analysis records whose scenario references did not match a source scenario ID and text. The report, input, spec, model, and settings are preserved in `runs/u7-final-sequential-20261019/`. The prompt was then revised to require exact scenario IDs and verbatim scenario text; a new immutable run with the same case, strategy, model, and settings passed the checker.

| Revision | Run record | Asset digest | Structural check | Latency |
| --- | --- | --- | --- | ---: |
| Preserved baseline | `runs/u7-final-sequential-20261019/execution.json` | `7fb7ef1b78e6101a272ce7836aba5687e3e99526a633b51c69b2ceb1ccc1c8e7` | Failed: two analysis scenario references | 48.32 s |
| Revised prompt | `runs/u7-compare2-sequential-20261019/execution.json` | `6e4db7bc46801eb989906e0d2198b2ef05c3d39a733e0c068267e1faf9e13375` | Passed | 77.68 s |

This is evidence that the revised output meets the deterministic traceability contract for this trial. It does not demonstrate better architecture reasoning or lower execution cost; the latency difference is one stochastic observation per revision and is not interpreted as a performance effect.

## Other evidence and limitations

- The ATAM HarnessSpec validates as v0.2, and the DeepAgents runtime capability check passes for file-based artifact input and output.
- The historical Claude Sonnet banking output at `case-studies/architecture-eval/ATAM/outputs/claude-sonnet-4-5@20250929/banking_output.json` passes deterministic section and scenario-reference checks. This structural check is not a matched baseline: its exact prompt, runtime settings, and execution provenance have not been established by this protocol.
- No blind domain review has been completed for the three new predictions. A matched baseline and two independent reviewers are still needed for paired quality or accuracy claims.
- The ArchEval runner sends model requests through Google Vertex AI or Anthropic Vertex. The existing evaluator also includes an LLM judge and attempts an NLTK data download. Neither is part of the deterministic check command.

Keep `ground_truth_outputs` out of generator inputs and run storage. Store blind review records separately from ground truth; reviewer/evaluator access to reference data belongs in a separate process. The legacy LLM-judge/lexical evaluator is supplementary and must not substitute for blind domain review.

Until matched baseline runs and independent blind reviews are completed, there are no paired quality, speed, completeness, accuracy, or cost claims. A single banking case demonstrates the protocol only and does not generalize to other architecture evaluation tasks.

## Runtime fidelity

All three profiles preserve the ATAM case's evaluation-input boundary, shared domain skills, Pydantic report contract, and deterministic scenario-reference check. Their workflow and interaction mappings differ:

| Profile | Implemented mapping | Fidelity limit |
| --- | --- | --- |
| Supervisor + one-shot specialist delegation | DeepAgents coordinator delegates to the declared quality-attribute and evidence specialists. | Specialists return one-shot results; persistent peer collaboration is not represented. |
| Sequential pipeline + typed artifact handoffs | The five HarnessSpec stages pass validated Pydantic artifacts in declared order: context, utility tree, architecture approaches, scenario analysis, synthesis/review. | Intermediate artifacts are passed in memory; stage completion is runtime bookkeeping and does not establish completion of stakeholder-facing ATAM activities. |
| Fan-out/fan-in + parallel specialist delegation | LangGraph runs declared specialists in parallel and joins their typed results before synthesis. | The barrier and join are explicit; Claude-style persistent agent messaging and shared task-list collaboration are unsupported. |

The ATAM prototype remains a model-generated report draft. It does not conduct stakeholder workshops, elicit priorities directly, or establish expert acceptance. The Claude plugin and DeepAgents outputs both require architect review before decision use. The DeepAgents CLI writes capability, approximation, unsupported-behavior, and timeout facts to a session-matched `.runtime.json` sidecar; failed attempts record their status and error type without publishing a report. Benchmark execution records retain the effective profile and shared asset digest.

## Semantic-state report contract refresh

The shared ATAM report now requires `evaluation_results.semantic_state`: evidence-backed statuses for context, drivers, architecture evidence, scenario analysis, and report review, plus typed evidence-gap records. Runtime task completion alone cannot mark methodology progress, and generated reports remain drafts until an architect reviews them. The Pydantic report contract, all Claude and DeepAgents template copies, and `pilot.py check` enforce this shape. Claude generation and execution have not been rerun against the revised contract.

| Profile | Session / record | Result |
| --- | --- | --- |
| Supervisor + one-shot specialist delegation | `examples/atam/deepagents/runs/u7-semantic-state-supervisor-df7f7865-769b-4f2b-8e87-2e6efbc6ca89.json` | Completed with `openai:gpt-5.4-mini`; deterministic ATAM source-scenario and semantic-state checks passed. Runtime: 37.04 s. |
| Sequential pipeline + typed artifact handoffs | `runs/u7-semantic-state-sequential-interrupted-20261020/execution.json` | Interrupted after about eight minutes without a report. Its run directory and asset fingerprint were recorded after interruption; the fingerprint cannot prove the exact revision used. |
| Fan-out/fan-in + parallel specialist delegation | `runs/u7-semantic-state-fanout-interrupted-20261020/execution.json` | Interrupted after about five minutes without a report. Its run directory and asset fingerprint were recorded after interruption; the fingerprint cannot prove the exact revision used. |

Both interrupted attempts used the same case, model, non-streaming/non-verbose settings, and 180-second per-request timeout as the refreshed supervisor run. The overall profile comparison is incomplete. These failures do not establish a quality or latency comparison.

On 2026-10-20, a current-contract sequential retry with streaming and verbose logging failed in the sandbox before a provider response because DNS resolution for the OpenAI endpoint was unavailable. Its failed runtime sidecar and execution record are in `runs/u7-semantic-state-sequential-streaming-20261020/`. A separately prepared network-enabled retry did not produce a report or console output after several minutes and was stopped at the user's request; its failed execution record is in `runs/u7-semantic-state-sequential-streaming-network-20261020/`. No current-contract sequential provider result is available. The streaming retry used the same ATAM input, model, prompt/assets, and strategy pair; only presentation settings changed to expose progress. This retry is diagnostic and is not a performance comparison.

A bounded current-contract `fan_out_fan_in` attempt used the same case, model, non-streaming/non-verbose settings, 180-second per-request timeout, and parallel-specialist interaction as the successful supervisor run. It produced no report or console output before the four-minute wall-clock cap and was stopped. Its immutable failed benchmark record is `runs/u7-semantic-state-fanout-bounded-20261020/execution.json`; no prediction, latency, or cost is recorded. Ctrl-C reached the `conda run` wrapper before the Python runner could write a session sidecar. The runner's direct `KeyboardInterrupt` handling is covered by a unit test, but this wrapper-level cancellation path is not. No current-contract fan-out provider result is available.

A second capped fan-out retry used `conda run --no-capture-output` to expose console output and deliver Ctrl-C to Python. It failed after 5.6 seconds with `OpenAIConnectionError` caused by DNS resolution failure in the sandbox, before producing a prediction. Its runtime sidecar is `examples/atam/deepagents/runs/u7-semantic-state-fanout-visible-retry-20261020-d3c37ef3-e58a-4ed5-8a5b-c48d37ee4c3f.runtime.json`, and its immutable benchmark record is `runs/u7-semantic-state-fanout-visible-retry-20261020/execution.json`. Latency records the failed attempt only; cost is unavailable. A network-enabled retry is required for a current-contract fan-out provider result.

A network-enabled fan-out retry using the same case, model, profile, and settings ran for the four-minute cap without producing a report. It was interrupted through `conda run --no-capture-output`, but the wrapper exited without the Python runner's runtime sidecar. Its benchmark record, including the cap and failed status, is `runs/u7-semantic-state-fanout-network-20261020/execution.json`; there is no prediction, cost is unavailable, and no current-contract fan-out result was produced. The interrupted attempts show that the remaining provider verification is not completing within a bounded four-minute session in this environment.
