# SARA architecture design pilot

**Status:** Claude Code and DeepAgents bundles have been materialized from the same saved HarnessSpec package and run on CampusBike. See the [sandbox runbook](../../docs/cain-2027/SANDBOX-RUNBOOK.md) for the complete two-level generation and execution procedure.

This pilot harvests the architecture-design workflow from the SARA case study and exercises it on CampusBike, the same case used by the ReArch paper. The generation source packet and run-time case are kept separate.

The verbatim SARA source files, copied CampusBike example inputs, and generated SARA bundles/spec packages are local-only, ignored by Git, and not distributed with this repository because they contain or reproduce third-party case-study material. To reproduce the pilot, obtain the source files from the cited upstream sources and place them at the paths shown below; review their license and provenance before redistributing generated bundles.

## Experiment scope

- Harvest SARA's four ordered stages and their eleven skills from `sources/harvest-input/` into draft HarnessWeaver sources.
- Generate the target(s) selected at G4 from the same harvested method and domain sources. The checked-in answer file keeps DeepAgents as the default; Claude Code or both targets can be selected explicitly.
- Run each generated target on the same CampusBike case in `cases/campus-bike.yaml` for a runtime comparison.
- Treat the run as a standalone workflow-transfer exercise. It does not test integration with SARA's frontend, API, authentication, Firestore persistence, or `PipelineService`.
- Keep any later SARA-host integration as a separate stretch task.

## Deliberate standalone-host adaptation

The SARA application uses its own `PipelineService`, Firestore-backed project data and stage-specific artifact routing. For this experiment, the generic HarnessWeaver host supplies the four-stage sequence and exchanges artifacts through files. This changes the host and persistence mechanism while preserving the stage order, task order, artifact meaning and stage read-back requirements wherever the target supports them.

The initial HarnessWeaver DeepAgents target accepts JSON artifacts. SARA's final stage produces an ADR in Markdown and a Mermaid diagram, so that target packages those two source texts in the final JSON artifact `architecture_decision.json`, using `sources/domain/contracts/architecture-decision.schema.json`. This preserves the content while changing its outer format; it does not test SARA's original file or UI handling.

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

The generator creates the shared intent, methodology, domain sources, HarnessSpec and design notes once, then materializes the selected target(s) under `build/<target>/`. Review harvested sources before treating them as authoritative.

## Generation setup

From the HarnessWeaver repository root, create the interactive generation sandbox after reviewing this preparation:

```sh
hw sandbox create-generation sara --answers pilots/sara/harness-answers.yaml
```

To select Claude Code only, add `--target claude`; to generate both from the same HarnessSpec, repeat the option: `--target claude --target deepagents`. The explicit command-line selection overrides only G4 in the copied answer file.

This generates both levels in one session: HarnessWeaver first authors the shared workflow specification, then materializes the selected runtime bundle(s). For example, to materialize both targets:

```sh
hw sandbox create-generation sara \
  --answers pilots/sara/harness-answers.yaml \
  --target claude --target deepagents
```

To add the second target later, use the collected `spec-package.zip` with `--from-package` as shown below. This reuses the shared HarnessSpec and domain/methodology assets.

After collecting a generation, HarnessWeaver creates a hash-checked `spec-package.zip` containing the validated HarnessSpec, its generated source files, original source inputs, contracts, and available gate answers. To add a runtime later, run:

```sh
hw sandbox create-generation sara \
  --from-package pilots/sara/generated/<generation-label>/spec-package.zip \
  --target claude
```

For a generation collected before spec packages were added, create the package once with `hw sandbox package-spec pilots/sara/generated/<generation-label>`. This verifies that the available pilot sources still match the original generation record before packaging them.

The generator will ask any remaining design and write-confirmation questions. Do not run a generated bundle until the harvested sources, HarnessSpec, target materialization report, and corresponding `hw check-bundle <bundle-path> --target <target>` result have been reviewed.

## Running either runtime bundle

Collect the generation first and confirm each target passes `hw check-bundle`. Then create one execution sandbox per target from the repository root.

### Claude Code (subscription OAuth)

```sh
hw sandbox create-execution sara \
  --target claude \
  --bundle pilots/sara/generated/<generation-label>/build/claude \
  --case campus-bike
```

The execution sandbox supplies the project description and functional requirements from the case binding and runs the SARA orchestrator. Enter the printed sandbox directory and run `ISOLATION=settings ./run.sh`. Then run `hw check` and `hw sandbox record` from that sandbox.

### DeepAgents (provider credentials)

Activate the environment with HarnessWeaver and its DeepAgents extra installed. Ensure credentials are available for the selected model provider, then create the execution sandbox:

```sh
hw sandbox create-execution sara \
  --target deepagents \
  --bundle pilots/sara/generated/<generation-label>/build/deepagents \
  --case campus-bike \
  --model openai:gpt-5.4-mini
```

Enter the printed sandbox directory and run `./run.sh`, then run `hw check` and `hw sandbox record`. The Claude and DeepAgents runs use the same case inputs but separate sandboxes, outputs, and runtime credentials.
