# Architecture design-exploration review criteria

**Status:** Review protocol prepared; no concrete case has been generated or expert-reviewed.

## Method boundary

This profile uses Attribute-Driven Design (ADD) as its declared method source. It makes design drivers, constraints, alternatives, decisions, and rationale visible for architect review. The HarnessWeaver profile adds explicit evidence links, uncertainty records, and a bounded comparison artifact; those are implementation choices, not claims that the paper prescribes this exact agent workflow.

ReArch is documented as a contrasting exploration method involving search, reflection, and ranking. A future ReArch profile should declare those activities separately and use case-specific criteria. Do not describe this ADD profile as a hybrid or treat ReArch outputs as ground truth.

## Required case inputs

Before generation, record the system boundary, design goals, constraints, prioritized quality attribute scenarios, existing architecture evidence (if any), evaluation horizon, and non-goals. Mark each missing item as an open question. Keep any reference solution or expert-only notes out of generation input.

## Review dimensions

Two qualified software architects should independently review anonymized outputs using a 1–5 scale (1 = absent/unsupported, 3 = mixed, 5 = complete and well-supported), with a written rationale and confidence:

1. **Driver coverage:** Alternatives address the declared goals, constraints, and prioritized quality scenarios.
2. **Structural clarity:** Each alternative communicates components, responsibilities, relationships, and relevant views clearly enough for review.
3. **Rationale and traceability:** Decisions link to drivers and evidence; assumptions and evidence gaps are labeled.
4. **Tradeoff quality:** The comparison describes expected benefits, costs, risks, and unresolved consequences across the same drivers.
5. **Option usefulness:** Alternatives are meaningfully distinct and feasible enough to inform architect deliberation; reviewers explain duplication or implausibility.
6. **Uncertainty discipline:** The report avoids unsupported certainty, false precision, and claims of optimality.
7. **Human usefulness:** The decision record supports, rather than replaces, accountable architect choice.
8. **Iteration control:** Each iteration has a driver-linked goal; the record explains whether the goal was met, what remains unresolved, and why another iteration is or is not proposed. Reviewers assess whether the case needs architect feedback between ADD steps.

Report reviewer scores separately, preserve disagreements, and record any adjudication. Do not collapse the dimensions into a single quality score without a declared weighting and rationale. If comparing a baseline and guided harness, use matched inputs/settings and blind reviewers to arm identity until reviews are locked.

## Current run/review status

No project-specific design brief, generated alternatives, paired baseline, or expert review is included. This directory defines a review-ready profile and protocol only. Published paper examples motivate the method but are not a ground-truth answer for a new system.
