## Harness: ATAM architecture evaluation

**Goal:** Produce an evidence-grounded ATAM evaluation draft (JSON report `ATAM_Evaluation`, status `draft`) of a supplied software architecture, for review by a software architect familiar with the system.

**Trigger conditions:** When asked to evaluate an architecture with ATAM, to build a utility tree, to find risks, sensitivity or tradeoff points for an architecture case, or to re-run, revise, re-check or record an architect review of an ATAM draft, use the `atam-evaluation` skill. Simple questions about ATAM may be answered directly.

**Boundary:** Case inputs are supplied at run time. Never read or use reference evaluation outputs (`ground_truth_outputs`).

**Change history:**
| Date | Change | Target | Reason |
| --- | --- | --- | --- |
| 2026-10-25 | First configured with Harness v2 from HarnessSpec `archeval-atam-harness` (spec_version 0.2) | All | Fresh build |
