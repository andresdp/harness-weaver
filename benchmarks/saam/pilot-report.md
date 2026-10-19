# SAAM WRCS pilot report

**Status:** protocol and deterministic tooling implemented; paired generation and human review not run.

The pilot is limited to the partial WRCS extraction. Six of fifteen scenarios are represented. The represented reference contains six classifications and five scenario evaluations. Other scenario facts are unknown. Architecture style, evaluator roles, and scenario-interaction grouping carry extraction inferences and cannot be treated as source-paper facts.

The generation boundary copies only `evaluation_inputs`; evaluator references remain outside run directories. The v0.2 HarnessSpec records the SAAM method, semantic assessments, and open gaps. Deterministic checks cover required report sections and represented scenario bounds. Human method/evidence quality is reviewed separately using `PROTOCOL.md`.

No paired quality, accuracy, completeness, latency, effort, or cost result is reported. Existing historical SAAM WRCS outputs are not matched baselines because their prompts, runtime settings, and review procedure are not established under this protocol. A new baseline and spec-guided run must use matched provider/model/settings, immutable manifests, and blinded independent review. Cost and time remain unavailable until measured; they are not zero.

**Blocking inputs for the paired run:** provider credentials and selection, exact matched prompts/runtime/model/decoding settings, and two qualified independent architecture reviewers. No output has been fabricated to fill these gaps.
