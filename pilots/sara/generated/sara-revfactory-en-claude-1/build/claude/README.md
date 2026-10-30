# SARA Architecture-Design Assistant (Claude Code harness)

A Claude Code project that runs the SARA four-stage architecture-design workflow on a project you supply and
returns a traceable architecture decision. It contains only agents, skills, an orchestrator skill, `CLAUDE.md` and
declarative JSON Schemas. There is no runtime code.

## Use

1. Open Claude Code with this directory as the working directory.
2. Give it a project description and its functional requirements (paste them, or point to files), e.g.
   *"Design the architecture for this project: <description> … Functional requirements: RF1 … RF2 …"*.
3. The `sara-orchestrator` skill saves the inputs and runs the stages in order:

   | Stage | Agent | Tasks |
   |-------|-------|-------|
   | 1 Requirements & Drivers | `sara-requirements-analyst` | cross-requirement analysis → quality attributes → drivers |
   | 2 Solution Design | `sara-solution-designer` | pattern candidates → compatibility → alternatives |
   | 3 Alternative Evaluation | `sara-alternative-evaluator` | evaluation → trade-offs → selection |
   | 4 Decision & Modeling | `sara-decision-documenter` | ADR → Mermaid diagram |

   Each stage also writes a gap register. `sara-contract-reviewer` checks each stage before the next one starts.
   `sara-decision-packager` then builds the final package.

4. Follow-ups such as *"redo only Stage 3"* or *"regenerate the diagram"* re-run that stage and every later one,
   reusing the earlier artifacts.

## Outputs

| Path | Content |
|------|---------|
| `output/architecture_decision.json` | Required final output: `selected_alternative_id`, `selection_rationale`, `adr_markdown`, `architecture_diagram_mermaid` (shape set by `.claude/skills/sara-artifact-review/references/architecture-decision.schema.json`) |
| `output/adr.md`, `output/architecture_diagram.mmd` | The same ADR and diagram as standalone files |
| `output/assumptions_and_gaps.json` | Ambiguities, assumptions, unclear evaluations and gaps, each traced to its source artifact |
| `_workspace/00_input/` | Your inputs, saved verbatim (ports `project_description`, `functional_requirements`) |
| `_workspace/artifacts/` | All intermediate SARA artifacts (the traceability chain) |
| `_workspace/run_meta.json`, `_workspace/review_findings.json` | Run record and review results |

## Requirements

You need Claude Code with project agents and skills enabled. The `Workflow` tool is optional: the orchestrator
uses it when the session has it, and otherwise runs the same steps with sequential `Agent` calls.

See `materialization-report.md` for source coverage, adaptations and limitations.
