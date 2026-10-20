# SAAM WRCS pilot report

**Status:** matched baseline and spec-guided generation completed; two independent blind reviews are pending. The ATAM harness remains the first-version demonstration; WRCS SAAM is a separate case.

The pilot is limited to the partial WRCS extraction. Six of fifteen scenarios are represented. The represented reference contains six classifications and five scenario evaluations. Other scenario facts are unknown. Architecture style, evaluator roles, and scenario-interaction grouping carry extraction inferences and cannot be treated as source-paper facts.

The generation boundary includes `evaluation_inputs` plus the six verbatim source scenario IDs/texts; classifications and evaluator-derived outputs remain outside run inputs. The v0.2 HarnessSpec records the SAAM method, semantic assessments, and open gaps. The baseline derives from the existing case-study prompt, adapted for structured WRCS input; the guided arm adds the HarnessSpec methodology and stage guidance. Both use the same Pydantic output contract and LangChain single-call execution. Assessment claims also carry JSON Pointer evidence references, which checker v0.5 strictly parses and resolves against generation-visible scalar input values.

## Matched generation pair

| Arm | Run | Model | Input SHA-256 | Model-call latency | Reference checks |
|---|---|---|---|---:|---|
| Baseline | `u5-baseline-evidence2-20261019` | `openai:gpt-5.4-mini` | `e2952932e79078c1bb3fb2c39cd1604990a7253ccdd59f53c6e045976779bde6` | 17.62 s | Partial: 5/6 classifications match; none of the five compared component/change-extent pairs match |
| Spec-guided | `u5-spec-guided-evidence2-20261019` | `openai:gpt-5.4-mini` | `e2952932e79078c1bb3fb2c39cd1604990a7253ccdd59f53c6e045976779bde6` | 16.59 s | Partial: 5/6 classifications match; none of the five compared component/change-extent pairs match |

Both runs used the same structured Pydantic output contract, model, and input. The adapted existing SAAM prompt was passed as the baseline system instruction; the guided treatment added the HarnessSpec methodology/stage instruction and spec. Each run records the complete prompt-file list and effective prompt hash. Checker v0.5 validates report structure, represented scenario coverage, exact source scenario text, duplicate IDs, reference bounds, and each evidence pointer against generation-visible inputs. Both pass those structural and evidence-link checks. The baseline's one classification mismatch is S-02; the guided arm's is S-04. None of the five referenced scenarios matches both the recorded affected components and change extent. These partial-reference comparisons are not judgments of overall SAAM quality. No evaluator reference is provided for S-02's impact, and facts about the nine absent scenarios remain unknown. Versioned checker outputs are retained with each run.

## Superseded exploratory attempts

The initial baseline attempt (`u5-baseline-20261019`) failed because sandbox networking could not resolve the provider host. The subsequent baseline/guided pair (`u5-baseline-20261019-retry`, `u5-spec-guided-20261019`) wrote instructions to disk but did not pass them to the model. Those immutable traces are invalid and are excluded from the comparison. The old packet `runs/review-u5-pair-20261019/` contains those outputs and must not be circulated.

The earlier `u5-baseline-prompted-20261019` / `u5-spec-guided-prompted-20261019` pair was superseded when the evidence-pointer contract was added. Its packet `runs/review-u5-prompted-pair-20261019/` is outdated and must not be circulated. The current anonymized packets are under `runs/review-u5-evidence-pair-20261020/`. The arm key is stored separately under ignored `.review-keys/`; do not provide it or evaluator references to reviewers until their ratings are locked. No quality advantage is claimed. Timing covers the model call; cost is unavailable.

**Remaining review input:** two qualified independent architecture reviewers must return locked ratings using the shared form. The project owner also still needs to provide the promised design brief and reviewer details for U6's expert-review gate. No review result has been fabricated.
