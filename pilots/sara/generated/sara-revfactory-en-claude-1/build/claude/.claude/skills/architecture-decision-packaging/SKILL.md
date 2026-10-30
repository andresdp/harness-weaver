---
name: architecture-decision-packaging
description: Assembles the final SARA deliverables after Stage 4 — architecture_decision.json conforming exactly to the architecture-decision output contract, copies of adr.md and architecture_diagram.mmd, and a merged assumptions_and_gaps.json — by copying reviewed content without altering it. Used by the sara-decision-packager agent at the end of the sara-orchestrator run; not for writing or editing ADRs.
---

# Architecture Decision Packaging

The output contract (`.claude/skills/sara-artifact-review/references/architecture-decision.schema.json`) is a
JSON envelope adapted for a JSON-only host: the ADR and the Mermaid source travel as strings. Packaging is pure
transfer — any wording change here would break traceability between the package and the reviewed artifacts.

## Inputs (all under `_workspace/artifacts/`)

`alternatives.json`, `alternative_selection.json`, `adr.md`, `architecture_diagram.mmd`,
`stage1_assumptions_gaps.json` … `stage4_assumptions_gaps.json`, and the non-blocking reviewer findings collected by
the orchestrator — given as JSON in your prompt (workflow mode) or in `_workspace/review_findings.json` (fallback mode).

## Procedure

1. Read `alternative_selection.json`. Confirm `selected_alternative_id` exists in `alternatives.json`.
2. Read `adr.md` and `architecture_diagram.mmd` in full.
3. Pre-check the contract rules; if any fails, stop and report (do not patch):
   - `adr.md` content starts with `# ADR:` and is at least 80 characters.
   - `.mmd` content starts with one of `flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|erDiagram|C4Context|C4Container|C4Component|C4Dynamic` and is at least 20 characters, with no ``` fences.
4. Build the object with **exactly** these four keys and no others:

   | Key | Value |
   |-----|-------|
   | `selected_alternative_id` | `alternative_selection.json` → `selected_alternative_id`, verbatim |
   | `selection_rationale` | `alternative_selection.json` → `selection_rationale`, verbatim |
   | `adr_markdown` | full content of `adr.md` (trailing newline may be trimmed; nothing else) |
   | `architecture_diagram_mermaid` | full content of `architecture_diagram.mmd` (same rule) |

   Escape newlines, quotes and backslashes correctly as JSON strings.
5. Write `<output>/architecture_decision.json` (pretty-printed, UTF-8).
6. Copy `adr.md` → `<output>/adr.md` and `architecture_diagram.mmd` → `<output>/architecture_diagram.mmd` unchanged.
7. Write `<output>/assumptions_and_gaps.json`: `selected_alternative_id`, `entries` = concatenation of the four
   stage registers' `entries` in stage order, and `review_findings_carried` = the non-blocking findings passed to
   you (empty array if none). This sidecar exists because the contract forbids
   additional properties in `architecture_decision.json`.
8. Read every written file back. Re-parse both JSON files. Confirm `architecture_decision.json` has exactly four keys.

## Return value

Return the exact object written to `architecture_decision.json`.
