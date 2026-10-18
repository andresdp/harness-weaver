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
