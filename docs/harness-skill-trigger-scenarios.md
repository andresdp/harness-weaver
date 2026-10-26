# HarnessWeaver skill trigger scenarios

Use these prompts to check whether the harness and evolve skills are invoked appropriately. They are test fixtures, not claims of automated trigger validation. The ten positive cases for each skill and the ten boundary cases are ready for later live trigger testing; execution is deferred.

## Should trigger `harness` (10 cases)

1. “Design a reusable multi-stage harness for software architecture tradeoff evaluation. Inspect the project guidance, create a compact HarnessSpec, validate it, and generate the skill-based form.”
2. “I need a quick one-off architecture review harness for this ADR. Keep it lightweight; only save a HarnessSpec if the design turns out to be reusable or complex.”
3. “Generate the DeepAgents backend form of this architecture design workflow from the supplied HarnessSpec, and report any requirements the adapter cannot represent.”
4. “Build an ATAM harness for evaluating availability and modifiability tradeoffs. Use the methodology sources I supplied and keep evidence gaps visible.”
5. “Our architecture group repeats the same design exploration across products. Create a reusable harness that records alternatives, rationale, and architect decisions.”
6. “Review this existing harness design against its HarnessSpec, identify missing roles or artifacts, and update the harness files if needed.”
7. “Turn this lightweight brief into a runnable architecture evaluation harness with a verifier and an explicit human-review checkpoint.”
8. “We need both Claude skills and a DeepAgents backend for the same architecture method. Define the shared spec first and disclose runtime differences.”
9. “Create a software architecture harness that reads ADRs, checks quality-attribute scenarios, and reports source provenance for each finding.”
10. “The architecture team needs a repeatable design review workflow. Inspect the project’s methods and produce the spec, roles, skills, orchestration, and validation plan.”

## Should trigger `evolve` (10 cases)

1. “The last run missed evidence for two architecture risks. Generalize the feedback and update the right spec or harness layer while preserving the baseline.”
2. “Run a retrospective on this harness and use the execution artifacts and project history to identify a bounded improvement.”
3. “This generated harness is too slow. Diagnose the execution feedback and evolve its orchestration without changing the domain requirements.”
4. “Two ATAM reports invented quality-attribute priorities. Trace the issue to the method or runtime layer and correct the harness without overwriting the old version.”
5. “The new DeepAgents adapter loses a review checkpoint from the shared design. Compare its run record with the HarnessSpec and propose a fidelity fix.”
6. “After the last evaluation, reviewers asked for every scenario claim to cite evidence. Incorporate that feedback and compare the revised harness under the same case.”
7. “The harness failed twice while loading its domain skills. Inspect the run artifacts, fix the runtime issue, and keep methodology state unchanged.”
8. “A team member corrected our architecture method mapping. Record the source and revision, update the affected harness layer, and preserve the prior baseline.”
9. “The run marked analysis complete even though the evidence reviewer found gaps. Fix the status transition and add a regression check.”
10. “We changed our acceptance criteria after reviewing the latest harness output. Classify the feedback, update the owning layer, and report any regression.”

## Boundary cases that should not trigger `harness` or `evolve` (10 cases)

1. “Evaluate this architecture and recommend whether to use microservices.” This requests architecture analysis, not harness design or evolution.
2. “Explain what a HarnessSpec is and show me a small example.” This requests an explanation, not a harness change.
3. “Create a skill that summarizes meeting notes.” This is direct skill authoring outside HarnessWeaver’s software-architecture focus.
4. “Refactor this Python function to reduce duplication.” This is a code change, not harness design or evolution.
5. “Use the ATAM evaluation skill to assess this architecture and draft the report.” This asks to run an existing harness, not create or evolve one.
6. “Validate `pilots/atam/harnessspec-v0.2.yaml` and tell me whether it matches the schema.” This asks for structural validation only.
7. “Summarize the attached architecture paper and list its design recommendations.” This is document analysis, not harness construction.
8. “How do I install DeepAgents in my Conda environment?” This is setup guidance, not a request to port or evolve a harness.
9. “Generate a Claude plugin that organizes my personal recipes.” This is plugin/skill creation outside the software-architecture harness scope.
10. “Compare these two architectures and rank them by cost.” This requests architecture analysis with no request to create or change a harness.

## Execution status

- Prepared: ten should-trigger cases per skill and ten boundary cases.
- Not run: live Claude trigger validation, with-skill/baseline comparison, and quantitative or blind grading. Those checks remain deferred; this file records test inputs, not results.

## U4 focused design scenarios

Use these scenarios to review the skill's design output. For reusable/complex cases, the resulting v0.2 HarnessSpec should validate; the lightweight case should not be forced to create a saved spec.

1. **Simple one-off:** “Create a quick checklist for reviewing this single ADR. Keep it in the conversation unless a saved spec would materially help.” Expected: brief intent, domain method or labeled judgment, a few checks, and no unnecessary HarnessSpec.
2. **Reusable method with semantic state:** “Build a reusable SAAM harness from these source materials.” Expected: source provenance, method/version and adaptations, activities with readiness and completion criteria, output artifacts, validation, evidence-linked state, unresolved gaps, and semantic progress kept distinct from runtime task status.
3. **Conflicting sources:** “Use these two evaluation guides; they disagree on when evidence is sufficient.” Expected: authority/revision references, surfaced conflict, stated assumption or question, and no silent resolution or unsupported completion claim.
4. **Missing evidence:** “Assess this architecture although the business goals are absent.” Expected: missing goal evidence marked unknown/gap with a next step; no inferred business goal or completed state.
5. **Execution bookkeeping mismatch:** “The agent finished every task, but the evaluator has no architecture evidence for two risks.” Expected: runtime success remains bookkeeping; semantic state retains gaps and completion is withheld.
6. **Layered evolution:** “The report omitted a method checkpoint, and its retry loop also duplicated work. Improve it.” Expected: separate domain-method/state correction from runtime mechanics, preserve spec/method/run baselines and provenance, and compare under the same evaluation protocol.
