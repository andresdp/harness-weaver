# SAAM WRCS partial-reference pilot protocol

## Case and boundaries

This HarnessWeaver-owned pilot uses the WRCS extraction in `case-studies/architecture-eval/SAAM/data/revision_control_system.json`. Its `completeness: Partial` metadata says that six of fifteen scenarios are represented. The six source scenario texts are S-01 through S-06. The reference has classification records for those six and evaluation records for S-01, S-03, S-04, S-05, and S-06 only. Missing references, including S-02's absent evaluation, are unknown; they are not negative results. Do not infer the other nine scenarios.

The extraction explicitly marks architecture style, evaluator roles, and grouped scenario interaction analysis as inferred. These can be discussed only as extraction-level inferences, with that provenance stated. Do not present them as facts from the original paper. Generation input contains `evaluation_inputs` plus the six source scenario IDs and verbatim scenario texts from `ground_truth_outputs.scenarios`. This narrow exception supplies the scenarios the pilot is evaluating. It does not expose classifications, scenario evaluations, interactions, synthesis, recommendations, or other evaluator-derived results to generation. The manifest records this provenance and boundary.

The v0.2 HarnessSpec makes SAAM methodology and semantic state explicit. Semantic state concerns method progress, evidence, and gaps; execution state, tool calls, agent scratch work, and token use do not count as method completion.

## Arms and run records

Create separate immutable `baseline` and `spec-guided` runs from the same case input. Match provider, model version, decoding settings, tools, output contract, and execution limits. The prompt/harness instruction bundle is the controlled treatment: baseline uses the disclosed existing SAAM prompt adapted to the structured WRCS input; spec-guided adds the HarnessSpec methodology, stages, and semantic-state guidance. Record prompt and harness revisions/hashes for each arm and all deviations. Each run ID is unique; preparation fails if it already exists. Keep predictions, prompts/configuration, logs, and execution record within that run. `manifest.json` and `execution.json` are write-once. A partial or failed run remains recorded but cannot support a paired quality claim. Omit unavailable timing or cost; null/unavailable never means zero.

Use `pilot.py prepare --run-id ID --arm baseline|spec-guided`. Save output as `prediction.json`, run `pilot.py check`, then write its execution record with `pilot.py record`. The checker validates structure, represented references, and evidence pointers against generation-visible input values. It does not judge whether the cited evidence logically supports the claim; human review covers that.

## Deterministic checks

Record pass/fail for required report sections, all six represented scenario IDs, classification/evaluation reference bounds, evidence pointers, and valid links among scenario artifacts. Each assessment or synthesis claim must cite at least one non-empty scalar value through an RFC 6901 JSON Pointer rooted at the exact generation input. Pointers must resolve within `evaluation_inputs` plus the six supplied source scenarios; references into ground truth or missing fields fail. Any reference to a scenario outside S-01 through S-06 fails. Compare classification labels for the six represented scenarios; compare affected components and change extent only for the five scenario evaluations with extracted references. S-02 is represented but has no extracted evaluation answer, so any such analysis remains unscored/unknown. Do not score absent details, inferred extraction fields as original-source facts, or scenario coverage against all fifteen as if the extraction were complete. Similarity or automated judge scores, if later added, are supplementary.

## Blinded human review

Two architecture reviewers independently assess each anonymized output before arm labels are revealed. Reviewers should not see arm prompts/configuration or evaluator reference material while rating method quality. Use a shared review form with a 1–5 scale (1 = absent/unsupported, 3 = mixed/partly supported, 5 = complete and well-supported) and written evidence:

1. SAAM method coverage: scenario classification, impact assessment, interaction analysis, synthesis.
2. Evidence grounding: each material claim points to supplied architecture evidence or is labeled as inference/assumption.
3. Uncertainty discipline: absent scenario facts remain unknown; extraction inferences are identified; six-of-fifteen partialness is explicit.
4. Usefulness and internal consistency of conclusions/recommendations.
5. Critical omissions, unsupported claims, and reviewer confidence.

Keep each review record separate from the prediction and reference data. Report both reviewer scores, rationale, disagreements, and adjudication if performed; do not collapse disagreements into a single score without showing them. Record completion time/change effort only if measured under the same protocol for both arms.

## Current status and evidence

The original baseline retry and guided call omitted treatment instructions from the model request and are invalid; preserve them but do not score or circulate their packet. The runner sends the treatment prompt as a system message and the case JSON as the user message. The current matched runs are `u5-baseline-evidence2-20261019` and `u5-spec-guided-evidence2-20261019`; they use the same model, input hash, Pydantic report contract, and execution path. Each includes the same source-pointer evidence contract; the only planned treatment difference is the baseline SAAM instruction versus the added HarnessSpec guidance. Earlier prompted runs are superseded by this contract and must not be circulated for review.

Both current reports pass structure, coverage, source-text, and generation-input evidence-pointer checks. Each matches five of six represented classifications; neither matches the sparse component/change-extent reference values. This deterministic score is partial and does not judge reasoning quality. Two anonymized packets for the current pair are under `runs/review-u5-evidence-pair-20261020/`; the arm key is separate. The project sequence is ATAM demonstration first through the Claude plugin and DeepAgents backend, with WRCS SAAM kept as its own later methodology case.
