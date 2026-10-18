# ArchEval ATAM banking pilot status

**Protocol:** `pilot.json` and `pilot.py` in this directory. **Status:** comparison not yet run.

## Evidence available

- The ATAM HarnessSpec validates as v0.1. Runtime capability checks were not requested, so the validator reports them as unassessed.
- The historical Claude Sonnet banking output at `case-studies/architecture-eval/ATAM/outputs/claude-sonnet-4-5@20250929/banking_output.json` passes the deterministic section and scenario-reference checks. This is a structural check only.
- The historical output is a baseline candidate, but matching prompt, settings, and execution provenance are not established. It is not a valid matched baseline for the spec-guided arm.
- The ArchEval runner sends model requests through Google Vertex AI or Anthropic Vertex. The existing evaluator also includes an LLM judge and attempts an NLTK data download. No `GOOGLE_CLOUD_PROJECT` or provider API credential variable is present in the current process environment.

## What remains for a valid paired result

Run a fresh baseline and spec-guided arm on the same isolated `evaluation_input.json`, using matched runtime/model/settings. Record exact prompts, model versions, settings, duration, cost when available, and output hashes. Keep `ground_truth_outputs` out of generator inputs and run storage. Apply the deterministic checker, then have independent reviewers score anonymized outputs using the existing human rubric; record reviewer disagreement before labels are revealed. The legacy LLM-judge/lexical evaluator is supplementary and must not substitute for blind domain review.

Until those steps are completed, there are no paired quality, speed, completeness, accuracy, or cost claims. A single banking case will demonstrate the protocol only, not generalize to other architecture evaluation tasks.
