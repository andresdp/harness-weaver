# Architecture design exploration profile

This HarnessSpec is an ADD-informed, review-ready profile for exploring architecture alternatives. It is separate from the ATAM/SAAM evaluation harnesses. It defines the design inputs, iteration goal, intermediate artifacts, evidence and assumption traceability, and an architect review gate. [method-mapping.md](method-mapping.md) traces the profile stages and artifacts to the ADD activities in the cited paper and records where this prototype adapts its human-feedback cadence.

The profile has not been run against a project-specific design brief. See [review-criteria.md](review-criteria.md) for the declared criteria and current evidence limits. Supply a case brief as `design-brief.yaml` before generating alternatives. ReArch is cited as a contrasting research direction and is not folded into this ADD procedure.

Validate from the repository root with:

```sh
conda run -n harness hw validate pilots/design-exploration/harnessspec.yaml
```
