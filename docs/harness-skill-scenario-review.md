# Harness and evolve skill scenario review

**Date:** 2026-10-20  
**Scope:** U4 focused design scenarios in [harness-skill-trigger-scenarios.md](harness-skill-trigger-scenarios.md), checked against the canonical [harness skill](../harness-en/skills/harness/SKILL.md) and [evolve skill](../harness-en/skills/evolve/SKILL.md).

This is a manual desk-check: the expected response for each fixture was worked through using the canonical skill instructions and the listed project artifacts. It is not a live Claude skill invocation or a model-generated test run. The trigger fixtures explicitly distinguish themselves from automated trigger validation. The Claude CLI is not authenticated in this environment.

| Scenario | Expected behavior | Desk-check result | Evidence |
|---|---|---|---|
| Simple one-off | Use a brief without forcing a saved HarnessSpec. | With no ADR text supplied, ask for the ADR or state the checklist will remain generic; keep the design brief in the conversation and omit a saved spec. | Harness skill, Core principles 7; Harness IR content. No case-specific facts are asserted. |
| Reusable method with semantic state | Preserve provenance, methodology, readiness, evidence, gaps, and semantic progress separately from runtime status. | Use the SAAM profile and its v0.2 spec; keep source references, method stages, evidence gaps, and assessment state explicit. The example SAAM spec validates. | `examples/saam/harnessspec.yaml`; `conda run -n harness hw validate examples/saam/harnessspec.yaml` passed. |
| Conflicting sources | Retain authority and revision, surface the conflict, and avoid silently resolving it. | Synthetic input: Guide A v1 says evidence is sufficient after one source; Guide B v2 requires corroboration. Record both references and the unresolved criterion, ask which authority governs, and withhold the completion claim. | Harness skill, Resolve the design inputs; conflict and missing evidence rules. Synthetic sources are a desk-check fixture, not repository evidence. |
| Missing evidence | Mark absent goals as unknown or gaps and state what would resolve them. | Synthetic architecture input has no business goals. Keep context/goal status unknown or partial, add a gap and a request for the goals or explicit acceptance of the gap; do not invent priorities. | Harness skill, Resolve the design inputs; Evidence and uncertainty. Synthetic case is a desk-check fixture. |
| Runtime tasks complete, method evidence missing | Keep execution bookkeeping separate and withhold semantic completion. | Treat “all tasks finished” as runtime success only; keep the two unsupported risk analyses open, record missing architecture evidence, and leave the ATAM report as a draft pending evidence or human acceptance. | Harness skill, Core principle 9; Harness IR content, Semantic progress and completion; ATAM semantic-state and human-review requirements in `examples/atam/harnessspec-v0.2.yaml`. |
| Layered evolution | Separate method/state changes from runtime fixes, preserve baselines, and compare under the same protocol. | Treat the omitted method checkpoint as a method/spec correction and duplicate retries as runtime behavior; preserve prior spec, prompts, and run records, then compare revisions with the same case and checks before claiming improvement. | Evolve skill, Phase 2 feedback mapping and Phase 3 generalize and apply; sequential prompt evolution records in `benchmarks/atam/pilot-status.md`. |

## Evidence and limits

- `docs/harness-skill-trigger-scenarios.md` contains ten positive trigger prompts for each skill, ten boundary prompts, and the six focused design scenarios. These remain fixtures rather than measured activation results.
- The saved ATAM, SAAM, and design-exploration HarnessSpecs validate with the `harness` Conda environment. Those checks validate spec structure, not skill-generated scenario outputs.
- The shared canonical skill source is `harness-en/skills/`; `harness-en/README.md` documents its ownership and states that the repository does not maintain a second in-repository copy of those shared design skills.
- `harness-en/skills/deepagents-port/` documents adapter losses. The ATAM runtime records its supported mappings and unsupported Claude collaboration semantics in `benchmarks/atam/pilot-status.md` and session sidecars.

**Gate status:** Manual desk-checks completed for all six U4 design scenarios. Runtime-generated outputs, live trigger/near-miss validation, and baseline-versus-skill comparisons remain unverified.
