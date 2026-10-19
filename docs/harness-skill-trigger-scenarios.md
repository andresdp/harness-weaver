# HarnessWeaver skill trigger scenarios

Use these prompts to check whether the harness and evolve skills are invoked appropriately. They are test fixtures, not claims of automated trigger validation.

## Should trigger `harness`

1. “Design a reusable multi-stage harness for software architecture tradeoff evaluation. Inspect the project guidance, create a compact HarnessSpec, validate it, and generate the skill-based form.”
2. “I need a quick one-off architecture review skill for this ADR. Keep it lightweight; only save a HarnessSpec if the design turns out to be reusable or complex.”
3. “Generate the DeepAgents backend form of this architecture design workflow from the supplied HarnessSpec, and report any requirements the adapter cannot represent.”

## Should trigger `evolve`

1. “The last run missed evidence for two architecture risks. Generalize the feedback and update the right spec or harness layer while preserving the baseline.”
2. “Run a retrospective on this harness and use the execution artifacts and project history to identify a bounded improvement.”
3. “This generated harness is too slow. Diagnose the execution feedback and evolve its orchestration without changing the domain requirements.”

## Near misses

1. “Evaluate this architecture and recommend whether to use microservices.” This requests architecture analysis, not harness design or evolution.
2. “Explain what a HarnessSpec is.” This requests an explanation, not a harness change.
3. “Create a skill that summarizes meeting notes.” This is a direct skill-authoring request outside HarnessWeaver's software-architecture focus unless the user asks to use the HarnessWeaver method.
4. “Refactor this Python function.” This does not request harness design or evolution.

## U4 focused design scenarios

Use these scenarios to review the skill's design output. For reusable/complex cases, the resulting v0.2 HarnessSpec should validate; the lightweight case should not be forced to create a saved spec.

1. **Simple one-off:** “Create a quick checklist for reviewing this single ADR. Keep it in the conversation unless a saved spec would materially help.” Expected: brief intent, domain method or labeled judgment, a few checks, and no unnecessary HarnessSpec.
2. **Reusable method with semantic state:** “Build a reusable SAAM harness from these source materials.” Expected: source provenance, method/version and adaptations, activities with readiness and completion criteria, output artifacts, validation, evidence-linked state, unresolved gaps, and semantic progress kept distinct from runtime task status.
3. **Conflicting sources:** “Use these two evaluation guides; they disagree on when evidence is sufficient.” Expected: authority/revision references, surfaced conflict, stated assumption or question, and no silent resolution or unsupported completion claim.
4. **Missing evidence:** “Assess this architecture although the business goals are absent.” Expected: missing goal evidence marked unknown/gap with a next step; no inferred business goal or completed state.
5. **Execution bookkeeping mismatch:** “The agent finished every task, but the evaluator has no architecture evidence for two risks.” Expected: runtime success remains bookkeeping; semantic state retains gaps and completion is withheld.
6. **Layered evolution:** “The report omitted a method checkpoint, and its retry loop also duplicated work. Improve it.” Expected: separate domain-method/state correction from runtime mechanics, preserve spec/method/run baselines and provenance, and compare under the same evaluation protocol.
