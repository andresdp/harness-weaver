---
name: quality-attribute-identification
description: SARA Stage 1, task 2. Identifies the quality attributes (performance, availability, security, interoperability, etc.) supported by explicit or strongly implied evidence in the analyzed requirements and writes quality_attributes.json. Used by the sara-requirements-analyst agent inside the sara-orchestrator run; not for choosing tactics or technologies.
---

# Quality Attribute Identification

Source: SARA `stage1-requirements_drivers/skills/quality-attribute-identification` (adapted paths only).

## Objective

Identify the quality attributes relevant to the system based on explicit or strongly implied evidence. Attributes
listed here become evaluation criteria in Stage 3, so an unsupported attribute distorts the final selection.

## Inputs

- `_workspace/artifacts/requirements_analysis.json`
- `_workspace/00_input/project_description.md` (evidence source)

## Procedure

For each quality attribute determine: `name`, `description`, `rationale`, `source_requirement_ids`, `evidence`,
`priority` (`high` | `medium` | `low`).

Consider attributes such as performance, scalability, availability, reliability, security, modifiability,
interoperability, usability, maintainability. Only include attributes supported by evidence.

## Rules

- Prefer explicit evidence. Strongly implied attributes may be included when justified; say so in `rationale`.
- Do not invent attributes merely because they are common architectural concerns.
- Do not propose tactics, patterns, technologies or architecture styles; make no final decisions.
- Do not confuse a quality attribute with a solution.
  Correct: "Interoperability is relevant because the system must expose functionality through HTTP/REST."
  Incorrect: "The system should use an API Gateway."
- Every `source_requirement_ids` entry must exist in `requirements_analysis.json`.

## Output

Write `_workspace/artifacts/quality_attributes.json`:

```json
{
  "quality_attributes": [
    {
      "name": "...",
      "description": "...",
      "rationale": "...",
      "source_requirement_ids": [],
      "evidence": [],
      "priority": "high"
    }
  ]
}
```

After writing, read the file back and verify it is valid JSON. Do not perform Driver Identification.
