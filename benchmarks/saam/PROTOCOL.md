# SAAM WRCS partial-reference pilot protocol

## Case and boundaries

This HarnessWeaver-owned pilot uses the WRCS extraction in `case-studies/architecture-eval/SAAM/data/revision_control_system.json`. Its `completeness: Partial` metadata says that six of fifteen scenarios are represented. The six source scenario texts are S-01 through S-06. The reference has classification records for those six and evaluation records for S-01, S-03, S-04, S-05, and S-06 only. Missing references, including S-02's absent evaluation, are unknown; they are not negative results. Do not infer the other nine scenarios.

The extraction explicitly marks architecture style, evaluator roles, and grouped scenario interaction analysis as inferred. These can be discussed only as extraction-level inferences, with that provenance stated. Do not present them as facts from the original paper. Preparation copies only `evaluation_inputs`. Reference outputs are loaded by the deterministic evaluator and must never enter generation input or a run directory.

The v0.2 HarnessSpec makes SAAM methodology and semantic state explicit. Semantic state concerns method progress, evidence, and gaps; execution state, tool calls, agent scratch work, and token use do not count as method completion.

## Arms and run records

Create separate immutable `baseline` and `spec-guided` runs from the same case input. Match provider, model version, system/developer prompts, decoding settings, tools, and execution limits. Record deviations. Each run ID is unique; preparation fails if it already exists. Keep predictions, prompts/configuration, logs, and execution record within that run. `manifest.json` and `execution.json` are write-once. A partial or failed run remains recorded but cannot support a paired quality claim. Omit unavailable timing or cost; null/unavailable never means zero.

Use `pilot.py prepare --run-id ID --arm baseline|spec-guided`. Save output as `prediction.json`, run `pilot.py check`, then write its execution record with `pilot.py record`. The checker measures structure and reference bounds only. It does not judge reasoning quality.

## Deterministic checks

Record pass/fail for required report sections, all six represented scenario IDs, classification/evaluation reference bounds, and valid links among scenario artifacts. Any reference to a scenario outside S-01 through S-06 fails. Compare classification labels for the six represented scenarios; compare affected components and change extent only for the five scenario evaluations with extracted references. S-02 is represented but has no extracted evaluation answer, so any such analysis remains unscored/unknown. Do not score absent details, inferred extraction fields as original-source facts, or scenario coverage against all fifteen as if the extraction were complete. Similarity or automated judge scores, if later added, are supplementary.

## Blinded human review

Two architecture reviewers independently assess each anonymized output before arm labels are revealed. Reviewers should not see arm prompts/configuration or evaluator reference material while rating method quality. Use a shared review form with a 1–5 scale (1 = absent/unsupported, 3 = mixed/partly supported, 5 = complete and well-supported) and written evidence:

1. SAAM method coverage: scenario classification, impact assessment, interaction analysis, synthesis.
2. Evidence grounding: each material claim points to supplied architecture evidence or is labeled as inference/assumption.
3. Uncertainty discipline: absent scenario facts remain unknown; extraction inferences are identified; six-of-fifteen partialness is explicit.
4. Usefulness and internal consistency of conclusions/recommendations.
5. Critical omissions, unsupported claims, and reviewer confidence.

Keep each review record separate from the prediction and reference data. Report both reviewer scores, rationale, disagreements, and adjudication if performed; do not collapse disagreements into a single score without showing them. Record completion time/change effort only if measured under the same protocol for both arms.

## Current status

No new matched baseline/guided pair is included. Historical SAAM outputs, including WRCS runs, have no verified matched prompts/settings or blinded review under this protocol and are not baselines. Provider credentials, a selected provider/model, matched execution settings, and qualified independent reviewers are needed to run and review the pair. Until then this is a protocol/checker pilot, not a quality comparison.
