# SARA architecture-design harness (DeepAgents, HarnessWeaver stage host)

Generated from `../../harnessspec.yaml` (`sara-architecture-design`, revision 0.1.0), harvested from
SARA `NicolasMP51/software-architecture-agent@528ae7ce`. See `materialization-report.md` for the fidelity record.

## Layout

- `wiring.yaml`: input ports, the four serial stages, their artifacts and schemas, and the final output.
- `stage1-requirements_drivers/`, `stage2-solution_design/`, `stage3-alternative_evaluation/`, `stage4-architecture_decision/`: one deep agent per stage (`AGENTS.md` + `skills/`).
- `contracts/`: JSON Schemas the host validates after each stage.

## Run

```shell
python -m harnessweaver.hosts.deepagents --bundle <this dir> --input <dir with project_description.json and functional_requirements.json> \
  --workspace <run dir> --out <out dir> --model <provider:model>
```

The host writes the ports to `/artifacts/00_<port>.json`, runs stages 1→4, validates each stage's artifacts and copies
`architecture_decision.json` to `--out`. No human gate is wired; the run does not pause.

## Post-run review (manual)

The result is a recommendation. Before use, a software architect reviews `architecture_decision.json` and the stage artifacts:

1. **Package fidelity (`v-package-fidelity`).** `adr_markdown` equals `adr_markdown` in `adr.json`; `selected_alternative_id` and `selection_rationale` equal the values in `alternative_selection.json`.
2. **Reference integrity (`v-reference-integrity`).** `source_requirement_ids` exist in `requirements_analysis.json`; alternative ids in the evaluation, trade-offs and selection exist in `alternatives.json`.
3. **Requirement coverage (`v-requirement-coverage`).** Every requirement is evaluated for every alternative.
4. **Architect review (`architect-review`).** The rationale is supported, weaknesses are visible, and the ADR and diagram represent the selected alternative only.

These checks are manual; no executable checker is generated.

## Maintenance

Skill `description` fields are kept for maintainers; skills run in the order `AGENTS.md` pins, not by triggering.
Use the `evolve` skill to apply execution feedback.

## Change history

| Date | Change | Target | Reason |
|---|---|---|---|
| 2026-10-29 | Initial materialization from spec revision 0.1.0 (two-task Stage 4, no runtime gate, manual post-run checks) | deepagents (HarnessWeaver host) | SARA pilot |
