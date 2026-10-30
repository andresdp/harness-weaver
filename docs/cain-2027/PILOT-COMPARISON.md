# ATAM and SARA pilot comparison

This note records the current differences between the two architecture-assistant pilots and the comparison boundary for a Revfactory baseline run on SARA/CampusBike. It is a reference for experiment planning and paper revisions.

## Pilot differences

| Dimension | ATAM | SARA |
|---|---|---|
| Architecture task | Evaluate an existing architecture against business drivers and quality-attribute scenarios; identify risks, non-risks, sensitivities, and trade-offs. | Design an architecture from a project description and functional requirements; derive drivers, create and evaluate alternatives, and record a decision. |
| Method workflow | Five main ATAM activities. The generated DeepAgents workflow has five stages; the Claude workflow separates synthesis, review, and revision more explicitly. | Four ordered stages with eleven harvested skills, from requirements and drivers through solution design and alternative evaluation to an architecture decision. |
| Case | Banking architecture context. | CampusBike project description and thirteen functional requirements from the ReArch case-study line. |
| Primary output | Draft ATAM evaluation report and review findings. | Selected alternative, rationale, ADR, and architecture diagram. The standalone HarnessWeaver host packages the final content in `architecture_decision.json`. |
| Evidence and validation | Schema, ATAM-specific checks, and reference-leakage checks. The case has evaluator-only reference outputs that are withheld from runtime inputs. | Available checks are schema and reference-leakage checks. There is no SARA domain-specific checker, and the case has no evaluator-only reference outputs; therefore, the leakage pass is not substantive evidence against hidden answers. |
| Source preparation | ATAM method profile, intent, skills, contracts, and report template are maintained as pilot sources. | SARA stage instructions and skills are harvested from third-party source material. The local source packet is read-only and ignored by Git. |
| Host adaptation | The generated workflows run through Claude Code or the HarnessWeaver DeepAgents host. | The standalone HarnessWeaver host uses filesystem artifacts and JSON validation instead of SARA's application host and persistence layer. The final JSON envelope is an adaptation, not SARA's original output form. |

## Current results and parity boundary

- **ATAM / HarnessWeaver:** Claude Code and DeepAgents reports passed the configured schema, ATAM, and leakage checks after manual corrections. Both reports remain drafts for architect review.
- **ATAM / Revfactory:** the separate Claude baseline passed schema and leakage checks but failed the ATAM scenario-matching check for 19 analysis records. This is a baseline result, not a result from the HarnessWeaver Claude bundle.
- **SARA / HarnessWeaver:** the same saved HarnessSpec v0.2 was materialized for Claude Code and DeepAgents. Both CampusBike runs completed four stages and passed the available schema and leakage checks. Both selected A3, but their requirement-coverage rationales differed. The case has no domain checker or evaluator-only references, and these outputs have not received independent architect validation.
- **SARA / Revfactory:** the same Claude Code baseline bundle was run twice on CampusBike. Run 1 selected A3 and reported 12/13 requirements satisfied; it resumed after a usage limit, used general-purpose agents for the remaining reviews, and packaged with a direct `jq` copy after the custom agents were unavailable. Its final review reported one major (unsupported HTTP/REST protocol in the diagram) and four minor findings, none blocking. Run 2 completed all stages in one session with the configured agents, required no repairs, passed schema and leakage checks, and selected A1 with 10/13 requirements satisfied. It reported the same non-blocking protocol finding. Both execution evidence directories record schema and leakage passes. Run 1's launcher record still says failed because it records the initial usage-limit exit; the resumed run log records completion. The changed decision and requirement count are direct evidence of outcome variation for the same generated bundle and case, though two runs do not characterize the variation rate. The bundle check passes after normalizing the generated uppercase `MATERIALIZATION_REPORT.md` filename to the required `materialization-report.md`, preserving the original in the execution record.

The appropriate within-pilot runtime comparison is HarnessWeaver Claude Code versus HarnessWeaver DeepAgents on the same case. The generation-baseline comparison is Revfactory Claude Code versus HarnessWeaver Claude Code on the same case. Do not treat the Revfactory arm as a third runtime or compare its Claude output directly with the HarnessWeaver DeepAgents output as if only the runtime changed. For SARA, the HarnessWeaver packages both select A3, but their rationales differ. Revfactory selected A3 in one run and A1 in the other; this prevents summarizing the baseline as a single stable decision. Its requirement counts are model assessments, not independently verified scores.

## SARA baseline protocol

The baseline generation prompt is configured separately from the HarnessWeaver prompt in `pilots/sara/pilot.yaml`. It requests a Claude Code-native assistant based on SARA's harvested workflow, uses the shared final-output schema, excludes CampusBike case facts from generation, and avoids HarnessWeaver-specific hosts and specifications. The execution case is supplied later through `hw sandbox create-execution`.

From the repository root:

```bash
hw sandbox create-generation sara --arm revfactory-en
```

In the printed sandbox, run Claude Code with the user's subscription login:

```bash
cd "/path/printed/by/the-create-command"
ISOLATION=settings ./run.sh
```

After generation, collect it from the repository root with a unique label:

```bash
hw sandbox collect "/path/to/generation-sandbox" --label sara-revfactory-en-claude-1
```

Review the generated Claude bundle and its bundle-check result. Then create and run a CampusBike execution sandbox:

```bash
hw sandbox create-execution sara \
  --target claude \
  --bundle pilots/sara/generated/sara-revfactory-en-claude-1/build/claude \
  --case campus-bike
```

Inside the printed execution sandbox:

```bash
ISOLATION=settings ./run.sh
```

After it finishes, from the repository root:

```bash
hw check "/path/to/execution-sandbox"
hw sandbox record "/path/to/execution-sandbox"
```

For a meaningful comparison, preserve the same CampusBike inputs and final output contract, record the model and runtime versions, and document all manual changes. SARA's available automated checks are weaker than ATAM's, so compare output structure and traceability separately from substantive architecture quality, which requires expert review.
