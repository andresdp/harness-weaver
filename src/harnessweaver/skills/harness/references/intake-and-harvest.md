# Intake and harvest

Read this file at gate G0.

## Intake: the four design inputs

| Input | Typical source | Record |
|---|---|---|
| **Intent** | `sources/intent.yaml`, or the request | Goal, scope, exclusions, users, the decision supported, the human-review requirement, intended targets |
| **Methodology** | `sources/methodology.yaml` | Activities and order, readiness, outputs, completion; semantic-state fields and evidence rules; review points; reference boundary |
| **Domain knowledge** | `sources/domain/` (`sources.yaml`, `skills/`, `contracts/`, `references/`) | Every source with authority, revision and provenance; portable domain skills; JSON Schemas of outputs |
| **Runtime constraints** | Gate G4/G5 answers | Target runtimes and their limits; keep them out of domain-method claims |

When the user needs to author a methodology source, follow [`methodology-authoring-guide.md`](methodology-authoring-guide.md). It explains the recommended content and which sections are conditional; it is an authoring convention, not a formal YAML schema.

Keep references to sources; do not copy long guidance into the spec. Mark missing inputs as unknown. Never let an inference become a source fact. If no recognized method is supplied, propose one and label it as a design choice that needs review.

**Case data is not a design input.** Example cases may help understanding, but never copy case facts or reference outputs (ground truth) into the spec, design notes or generated files. Cases are bound when the generated harness runs.

## Harvest: starting from an existing harness or application

Use harvest when G0 says `start_from: harvest:<path>`: an existing Claude Code project, a DeepAgents application with stage directories, or a bespoke agent application whose method is encoded in its prompts and skills.

1. **Inventory.** List the instruction files (`AGENTS.md`, `SKILL.md`, agent definitions, orchestrators, prompt modules), the artifact contracts (declared filenames, JSON structure blocks, schemas) and the application wiring (stage registries, completion checks). Record the path and revision of each item.
2. **Separate the layers.**
   - Intent: what the application is for and what it must not do.
   - Methodology: ordered activities, readiness and completion rules, review points.
   - Domain knowledge: task procedures, rules, examples, evidence standards.
   - Runtime bindings: models, backends, persistence, authentication, API wiring.

   Only the first three become sources. Runtime bindings go into `harvest-report.md` as host requirements.
3. **Write draft sources** under the chosen output: `intent.yaml`, `methodology.yaml`, and `domain/` with the original skills copied verbatim into `domain/skills/` and each listed in `domain/sources.yaml` with `authority: harvested from <repo>@<revision>`.
4. **Write `harvest-report.md`.** For each source item, give its origin file, whether it was copied, summarized or inferred, and its open questions. Also list defects found in the original, such as call-contract mismatches or undeclared artifacts, without fixing them in the original.
5. **Stop for review.** The user reviews the draft sources before design (G1) begins. Harvested material belongs to its owner; do not edit the original repository.
