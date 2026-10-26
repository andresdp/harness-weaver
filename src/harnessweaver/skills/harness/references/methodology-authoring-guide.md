# Methodology source authoring guide

Use this guide when preparing a domain methodology source for HarnessWeaver. A methodology source explains the work the harness should carry out, how it should judge progress, and what evidence supports its conclusions. It should be understandable without relying on runtime-specific details.

This is an authoring guide, not a formal YAML schema. Unless a project supplies a validator for its methodology format, the field names below are recommended conventions rather than parser-enforced requirements. HarnessWeaver validates the resulting HarnessSpec separately.

## What to put in the methodology source

Include enough information for a designer to answer these questions:

1. What work is this method intended to accomplish, and what are its limits?
2. What activities make up the method, and how do they depend on one another?
3. What does each activity need, produce, and require before it can proceed?
4. What evidence supports findings, and how should uncertainty or missing information be handled?
5. What counts as completion, including when partial results are acceptable?
6. Does a qualified person need to review the result before it is used?
7. Are there data or information boundaries the harness must preserve?
8. Must outputs follow a template, schema, or other contract?

Record the authoritative sources and label adaptations. Do not present an adaptation, assumption, or local design choice as a requirement of the source method.

## Recommended structure

The following is a domain-neutral outline. Omit sections that do not apply; explain important omissions when a reader might otherwise expect them.

```yaml
id: example-methodology
version: 0.1.0
authority: <source method, local profile, or both>
purpose: <the outcome the method supports and its scope>

activities:
  - id: activity-one
    purpose: <what this activity accomplishes>
    inputs: [<required information or prior artifact>]
    readiness: <evidence or condition needed to begin>
    outputs: [<artifact or decision produced>]

completion:
  required: [<outcomes needed for completion>]
  rule: <how to handle gaps, partial results, or unmet conditions>

sources:
  - title: <source name>
    reference: <stable local path, citation, or URL>
    revision: <version, date, or commit when known>
    use: <which parts of the method this source supports>

adaptations:
  - <local change and why it was made>
```

This outline is illustrative, not a fixed schema. Keep the terminology and granularity appropriate to the method. If the method has parallel or iterative activities, say so explicitly instead of forcing them into a linear list.

## Field guidance

| Section | Guidance | Usually needed? |
|---|---|---|
| `id`, `version` | Give the profile a stable identity and version so later changes can be traced. | Recommended for reusable or evaluated work. |
| `authority`, `sources` | Identify the method's source and the authority of local guidance. Include revisions where available. | Required in substance; exact field names depend on the project. |
| `purpose` | State the intended outcome, scope, and important limits. | Core. |
| `activities` | Describe the work in meaningful steps. Include dependencies, inputs, readiness, and outputs where they matter. | Core for a multi-step method; a short procedure can be used for a genuinely simple method. |
| `semantic_state` | Name domain-level progress states or assessments, their allowed values, and the evidence needed to set them. Keep them separate from runtime status such as task completion or retries. | Needed when progress has meaning beyond “finished”; recommended for workflows with review or partial completion. |
| `evidence_rules` | Define acceptable evidence, provenance, uncertainty labels, identifier rules, and how to handle unsupported claims. | Needed when conclusions must be auditable or evidence-grounded. |
| `completion` | Say what must be produced or assessed and whether completion can be partial. Specify how open gaps affect completion. | Core. |
| `human_review` | Identify who reviews, at what point, why, and what must be checked. Do not imply the harness can provide expert approval. | Conditional on risk, policy, or method. |
| `reference_boundary` | Separate operational inputs from evaluation-only, confidential, or otherwise excluded data. State where excluded data may be used, if anywhere. | Required whenever such a boundary exists; otherwise omit. |
| `report_contract` | Identify the output template or schema and the location/meaning of generated results. Keep input reference answers distinct from generated output fields. | Required when a contract exists; otherwise omit. |
| `source_basis` | Summarize copied source material and distinguish it from local adaptation. Use it to preserve provenance when sources are not bundled with the project. | Recommended for harvested, adapted, or standalone profiles. |

“Core” means the information is needed to design a faithful harness; it does not mean a current parser enforces a particular YAML key. Projects should define a versioned schema if they need machine enforcement.

## Writing activities that can become stages

Describe activities by their purpose and artifacts, not by agent names or tools. For each activity, make clear:

- what inputs it consumes;
- what condition makes it ready to run;
- what outputs it creates;
- what evidence or checks support those outputs;
- whether it can run in parallel, must follow another activity, or may repeat;
- how it handles missing, contradictory, or low-confidence inputs.

Avoid prescribing runtime details such as a Claude Code skill path, a DeepAgents API call, a model name, or a filesystem location. Those belong in target-specific configuration or materialization. The methodology should remain portable across runtimes.

## Describing evidence and uncertainty

Use explicit categories that fit the domain. A useful general distinction is:

- **Observed:** directly present in an input or validated artifact.
- **Inferred:** reasoned from evidence; state the reasoning and preserve uncertainty.
- **Assumed:** not established by the inputs; record as an assumption or gap rather than a fact.

Specify the identifiers or references allowed for each evidence type when the domain has structured IDs. State which claims cannot be made without measurements, thresholds, expert confirmation, or other missing evidence. If sources conflict, preserve the conflict and identify how it should be resolved; do not silently choose one.

## Describing semantic state and completion

Semantic state describes progress in the method or domain, not the execution engine. For each assessment, define:

- its meaning and permitted values;
- what evidence is required to set each value;
- what remains to be done when it is partial, unknown, or unmet;
- whether it can be marked complete by the harness or requires human review.

Completion should not mean merely that all steps ran. Define what outputs and checks must be present, how unresolved gaps affect the result, and when a draft is complete but not approved for use.

## Data boundaries and output contracts

When a project uses reference answers, evaluation labels, private material, or other restricted data, state the boundary concretely:

- which fields or files are valid task inputs;
- which fields or files are reserved for evaluation or excluded from the generated harness;
- which process, if any, may access the excluded material;
- what output field contains generated findings.

Keep the generated result separate from reference answers in both names and structure. Point to a local copy of a template or schema when the generated project must work independently of the source repository. Explain any changes made to that contract and their provenance.

## Common problems to avoid

- Listing activities without saying what they consume or produce.
- Treating a runtime's “task completed” status as proof that the method is complete.
- Describing requirements only in prose when exact values, IDs, or output shapes can be stated.
- Mixing source-method requirements with local adaptations or unresolved assumptions.
- Saying “use the evidence” without defining acceptable evidence or how claims cite it.
- Omitting uncertainty and gap behavior, which encourages unsupported completion.
- Putting case-specific data, secrets, or evaluator-only reference answers in a reusable methodology source.
- Embedding model, tool, or runtime configuration in the domain method.

## Before handing the source to HarnessWeaver

- [ ] The purpose and limits are clear.
- [ ] Activities have meaningful inputs, readiness conditions, and outputs.
- [ ] Dependencies and any iteration or parallel work are stated.
- [ ] Evidence, uncertainty, conflicts, and gaps have explicit handling rules where relevant.
- [ ] Completion and partial-completion rules are clear.
- [ ] Semantic progress is distinguishable from runtime execution status.
- [ ] Human review requirements are stated where needed.
- [ ] Data boundaries and output contracts are included where applicable.
- [ ] Sources, revisions, authority, and local adaptations are identifiable.
- [ ] The source contains no case secrets or evaluation-only answers.
- [ ] Runtime-specific implementation details are kept out.

During intake, use this source to design the HarnessSpec's methodology references, stages, artifacts, semantic state, completion criteria, verification, and human gates. Ask the author about material ambiguity; do not silently fill gaps with invented method rules.
