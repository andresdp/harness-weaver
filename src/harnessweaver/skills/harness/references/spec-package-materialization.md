# Materialize runtime targets from a saved spec package

Use this workflow when the sandbox contains `generated/harnessspec.yaml` and the gate answers say `start_from: spec:`.

The HarnessSpec and its packaged sources define the shared design. This session is for materializing the explicitly selected runtime target(s), not for harvesting, redesigning the domain workflow, or revising the shared spec.

1. Read the HarnessSpec, its referenced sources, contracts, and `generated/design-notes.md` / `generated/harvest-report.md` when present. The package manifest records the original spec digest and source digests.
2. Validate the saved HarnessSpec before writing target files. If it is invalid, a required source is missing, or its meaning is unclear, stop and report the problem rather than silently editing the shared design.
3. Generate only the targets named in G4. Place each under `generated/build/<target>/`. Do not write another runtime target, modify files outside those target directories, or change the HarnessSpec, methodology, domain sources, contracts, or prior materialization reports.
4. Apply the existing target guidance and write a target-specific `materialization-report.md`. Record the saved spec revision and digest, mapped and approximated elements, unsupported requirements, and target-specific decisions. Keep target differences in this report; do not change shared methodology to hide a runtime limitation.
5. Run `hw check-bundle <bundle> --target <target> --spec generated/harnessspec.yaml` for every selected target. Report the exact result and remaining limitations.
6. Before handing off, confirm that the HarnessSpec and packaged source files still match their original digests. If generation changed any shared file, stop and report it; do not present the result as materialized from the unchanged package.

Only ask the user about decisions that are specific to the selected runtime or that the saved package leaves unresolved. Explain the practical consequence of each question in plain language.
