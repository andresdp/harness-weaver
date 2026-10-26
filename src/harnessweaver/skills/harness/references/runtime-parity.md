# Cross-runtime behavior parity

Read this when both Claude Code and DeepAgents are selected for the same HarnessSpec. The goal is to preserve the same **semantic workflow behavior** across targets. Runtime files, APIs, progress display, model selection and storage can differ; required outcomes and safety rules should not silently differ.

## Build one shared behavior contract

Before materializing either target, derive a parity matrix from the same validated spec revision and the same source assets. Include every declared:

- activity, dependency and required execution order;
- artifact, schema, stable identifier and provenance rule;
- verification criterion and the point where it must pass;
- retry, repair, fail-stop, resume and partial-run rule;
- producer/reviewer separation, revision limit and readiness condition;
- human gate, including what stops, who must review, and what records approval.

When the spec combines several steps in one activity, preserve any distinct guarantees those steps establish. In particular, an independent review remains a separate reviewer invocation. A target with one agent per stage can use another stage for the reviewer; disabling subagents does not justify merging the reviewer with the producer.

## Preserve enforcement, not just instructions

For each verification, record where and how it runs in both targets: deterministic schema/code validation, a separate agent review, or an instructed self-check. Keep its inputs, pass/fail criteria, timing, and effect on completion or readiness equivalent.

- If one target has deterministic enforcement, seek an equivalent executable or host-level check in the other target.
- A JSON structure block plus read-back is not equivalent to JSON Schema validation. A reviewer prompt is not equivalent to an independent reviewer invocation.
- If the target host cannot enforce a check, keep the check visible, mark the mapping `approximated`, and state the consequence. Do not report behavioral parity for that requirement.
- Never let a runtime completion flag substitute for methodology completion or review readiness.

Use the same retry policy for recoverable artifact failures, including the retry limit and stop point. Do not retry terminal failures such as missing credentials, exhausted service limits or denied permissions. Keep partial artifacts and unresolved gaps visible in both targets.

## Preserve gates and readiness

Each human gate must stop both workflows at the corresponding point. Neither target may auto-approve a gate or mark a human-reviewed state without the required human record. Calculate readiness from the same final validation results after the same revision/re-review steps. An external `hw check` after a run is useful evidence, but it does not make two runtime readiness behaviors equivalent if only one runtime uses that check before reporting readiness.

## Allowed runtime differences

These differences may remain when they do not change the behavior contract: artifact path and filename conventions, stage/agent API, model tiering, progress presentation, concurrency among independent activities, and persistence or resume mechanics. Keep the same dependency order; parallelize only where the spec permits it. Record any expected effect on timing, repeatability or human interaction.

Model output can vary between runs. Parity means both targets apply the same domain rules and acceptance criteria; it does not require identical prose, finding counts or conclusions. When the method requires complete coverage, each target must account for every required item, including explicit reasons and gaps for any item not analyzed.

## Report the comparison

When both targets are generated, include a `Cross-target behavior parity` table in each `materialization-report.md`:

| Spec behavior | Claude Code implementation and enforcement | DeepAgents implementation and enforcement | Status | Difference and effect |
|---|---|---|---|---|
| <stage, artifact, verification, retry, readiness or human-gate requirement> | <construct and enforcement point> | <construct and enforcement point> | aligned / approximated / different / unsupported | <remaining effect, or —> |

Include every matrix row from the shared behavior contract, not only rows that differ. Use `aligned` only when both targets enforce the same requirement at the corresponding point. A passing bundle check or one successful run does not establish behavioral parity; report those as separate structural or execution evidence.
