# SARA architecture design pilot

**Status:** prepared for HarnessWeaver generation; no bundle has been generated yet.

This pilot harvests the architecture-design workflow from the SARA case study and exercises it on CampusBike, the same case used by the ReArch paper. The generation source packet and run-time case are kept separate.

The verbatim SARA source files and copied CampusBike example inputs are local-only, ignored by Git, and not distributed with this repository because they originate in third-party case-study material. To reproduce the pilot, obtain those files from the cited upstream sources and place them at the paths shown below; review their license and provenance before redistributing them.

## Experiment scope

- Harvest SARA's four ordered stages and their eleven skills from `sources/harvest-input/` into draft HarnessWeaver sources.
- Generate the **DeepAgents target only**, from the harvested method and domain sources.
- Run the generated stages with the generic HarnessWeaver stage host on the CampusBike case in `cases/campus-bike.yaml`.
- Treat the run as a standalone workflow-transfer exercise. It does not test integration with SARA's frontend, API, authentication, Firestore persistence, or `PipelineService`.
- Keep any later SARA-host integration as a separate stretch task.

## Deliberate standalone-host adaptation

The SARA application uses its own `PipelineService`, Firestore-backed project data and stage-specific artifact routing. For this experiment, the generic HarnessWeaver host supplies the four-stage sequence and exchanges artifacts through files. This changes the host and persistence mechanism while preserving the stage order, task order, artifact meaning and stage read-back requirements wherever the target supports them.

The HarnessWeaver DeepAgents host currently accepts JSON artifacts. SARA's final stage produces an ADR in Markdown and a Mermaid diagram, so this pilot packages those two source texts in the final JSON artifact `architecture_decision.json`, using `sources/domain/contracts/architecture-decision.schema.json`. This preserves the content while changing its outer format; it does not test SARA's original file or UI handling.

The original SARA files remain unmodified in their nested repository. Known source issues—including the Stage 1 call-contract mismatch and the Stage 4 diagram skill's `/adr.json` reference despite the ADR skill producing `/adr.md`—are documented for the generator and must be reported as source defects. The standalone host avoids depending on the broken SARA call path; it does not repair SARA itself.

## Selected case and input boundary

CampusBike is the case used in the ReArch paper and has a system description plus 13 functional requirements. The case binding embeds only those two inputs. Its `qualities.json` is empty; Stage 1 should identify quality attributes only from evidence in the supplied description and requirements. The paper's quality-attribute list can be added later as a separately attributed input if needed, but is not silently synthesized into this initial run.

Prior results, workflow state, decision files, demo outputs, Chroma databases and other generated material under the SARA examples are excluded from the generation inputs. The case binding has no evaluator-only reference outputs, so the HarnessWeaver leakage check will have no reference passages to compare; do not present that check as substantive leakage evidence for this pilot.

## Files

```text
pilots/sara/
  pilot.yaml                         # HarnessWeaver sandbox configuration
  harness-answers.yaml              # agreed pilot target and host choices
  prompts/generation.md             # request for the interactive harness skill
  sources/
    host-adaptation.md              # explicit standalone-host decision
    harvest-input/                  # local-only, ignored copies of SARA source files
  cases/campus-bike.yaml            # standalone case inputs and provenance
  sources/domain/contracts/
    architecture-decision.schema.json  # final JSON envelope required by this host
```

The generator should create `intent.yaml`, `methodology.yaml`, `domain/`, `harvest-report.md`, `harnessspec.yaml`, `design-notes.md`, and `build/deepagents/` inside its generation sandbox. Review the harvested sources before treating them as authoritative.

## Generation setup

From the HarnessWeaver repository root, create the interactive generation sandbox after reviewing this preparation:

```sh
hw sandbox create-generation sara --answers pilots/sara/harness-answers.yaml
```

The generator will ask the remaining design and write-confirmation questions. Do not run the generated bundle until the harvested sources, HarnessSpec, materialization report, and `hw check-bundle --target deepagents` result have been reviewed.
