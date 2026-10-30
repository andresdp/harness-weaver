# Skill Writing Guide

Explains in detail how to raise the quality of skills made with the harness. A reference that supplements step 4 of `SKILL.md`.

---

## Contents

1. [How to write the `description`](#1-how-to-write-the-description)
2. [How to write the body](#2-how-to-write-the-body)
3. [How to define the output format](#3-how-to-define-the-output-format)
4. [How to write examples](#4-how-to-write-examples)
5. [How to load only the needed information step by step](#5-how-to-load-only-the-needed-information-step-by-step-progressive-disclosure)
6. [Criteria for deciding whether to bundle scripts](#6-criteria-for-deciding-whether-to-bundle-scripts)
7. [Data schema standards](#7-data-schema-standards)
8. [What not to put in a skill](#8-what-not-to-put-in-a-skill)
9. [Skill reuse design](#9-skill-reuse-design)

---

<a id="1-how-to-write-the-description"></a>

## 1. How to write the `description`

The skill fields exposed to Claude are `name` and `description`, and the concrete invocation conditions are written in `description`. Claude reads these two fields to decide which skill to use.

### How skills are run

Claude tends not to run a skill for simple tasks that it can easily handle with its basic tools alone. For example, a simple request such as "read this PDF" may not run the skill even if the `description` is written well. The more complex the task, needing several steps or specialized judgment, the more likely the skill is to run.

### Writing principles

1. Write both **what the skill does** and **the concrete situations in which the skill should run**.
2. If there are cases that look similar but where the skill must not run, write the scope and exclusion conditions clearly.
3. Considering that Claude judges conservatively whether to run a skill, express the situations in which it should run somewhat assertively.
4. In skills that coordinate several tasks, always include **words that indicate follow-up work** (re-run, fix, supplement, improve previous results).

### Good example

```yaml
description: "Reads PDF files and extracts text and tables, and performs merging, splitting, rotation,
  watermarking, encryption and decryption, and OCR. Always use this skill when the user mentions a .pdf file
  or requests a PDF output. Especially useful for work that needs conversion, editing, or analysis,
  rather than a simple request to 'read' a PDF."
```

### Poor examples

- `"A skill that processes data"` — too vague to know which files or tasks it handles.
- `"PDF-related work"` — doesn't say what work it can do or when it should run.

<a id="2-how-to-write-the-body"></a>

## 2. How to write the body

### Explain the reason first

When a large language model (LLM) understands why a rule is needed, it can judge appropriately even in exceptional situations. Telling it why the rule should be followed is more effective than only listing what to do and what not to do as commands.

**Poor example:**

```markdown
Always use pdfplumber for table extraction. Never use PyPDF2 for tables.
```

**Good example:**

```markdown
Use pdfplumber when extracting tables. PyPDF2 is for text extraction,
so it can't preserve the row and column structure of tables. pdfplumber recognizes cell boundaries
and returns structured data.
```

### Fix with principles that can apply to many cases

When feedback or testing finds a problem, don't add instructions that fit only a specific example. Fix it with a principle that can apply to other cases too.

**Overfitted fix:** `If there is a "Q4 sales" column, convert that column to numbers.`

**Generalized fix:** `If a column name contains words that indicate numbers, such as "sales", "amount", or "quantity", convert that column to a numeric type. Leave values that can't be converted as they are.`

### Write in the imperative

Write in the form of directives rather than descriptive or polite statements of what is done or can be done. A skill is a set of instructions that an AI agent must follow.

### Reduce the amount of information to consult at once

The amount of information a model can consult at once (the context window) is limited. That limit includes not only the skill's instructions but also other information needed for the work. Judge, by the following criteria, whether each sentence is necessary enough to justify the tokens it occupies.

- "Is this something Claude already knows?" → delete it.
- "Would Claude make mistakes without this explanation?" → keep it.
- "Is one concrete example clearer than a long explanation?" → replace it with an example.

<a id="3-how-to-define-the-output-format"></a>

## 3. How to define the output format

In skills where the format of the output matters, specify the structure to follow.

```markdown
## Report structure
Follow this template exactly.

# [Title]
## Summary
## Key findings
## Recommendations
```

Keep format descriptions short and include a real example; this is more effective.

**Outputs that the next stage of a workflow will read:** if the next stage reads and processes the output in code, specify a **JSON structure** instead of a Markdown template. Also state that the final text is return data to pass to the next stage, not a message to show the user. `Workflow`'s `agent()` enforces the return format with `schema`, so the structures defined in the skill and the script must match each other.

<a id="4-how-to-write-examples"></a>

## 4. How to write examples

Concrete examples convey rules more clearly than long explanations.

```markdown
## Commit message format

**Example 1:**
Input: add user authentication using JWT tokens
Output: feat(auth): implement JWT authentication

**Example 2:**
Input: fix a bug where the show-password button doesn't work on the login page
Output: fix(login): fix show-password toggle button behavior
```

<a id="5-how-to-load-only-the-needed-information-step-by-step-progressive-disclosure"></a>

## 5. How to load only the needed information step by step (Progressive Disclosure)

### Approach 1: Split files by business area

```
bigquery-skill/
├── SKILL.md (overview + guidance for choosing the business area)
└── references/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (sales opportunities, pipeline)
    └── product.md (API usage, features)
```

When the user asks about revenue, load only `finance.md`.

### Approach 2: Read detailed guidance only when needed

```markdown
## Document editing
For simple edits, modify the XML directly.
**If change tracking is needed**, see [REDLINING.md](references/redlining.md).
```

### Approach 3: Put a table of contents in large references

Put a table of contents at the top of references longer than 300 lines.

<a id="6-criteria-for-deciding-whether-to-bundle-scripts"></a>

## 6. Criteria for deciding whether to bundle scripts

Look over the work records of the agents that ran the tests. If the following things repeat, include a script or procedure in the skill.

| Repeated occurrence | Action |
|------------|------|
| The same helper script is created in all three tests. | Put the script in `scripts/`. |
| The same `pip install` or `npm install` command is run every time. | Write a dependency installation step in the skill. |
| The same multi-step processing procedure is followed every time. | Write the standard procedure in the skill body. |
| After running into similar errors, they are worked around the same way every time. | Write the known problems and solutions in the skill. |

Always verify scripts included in a skill by running them directly.

## 7. Data schema standards

Use the standard schemas below so that data can be exchanged consistently between skills. The same schemas can also be used when testing and evaluating skills made with the harness.

### `eval_metadata.json`

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": [
    "The output contains X",
    "A file was created in format Y"
  ]
}
```

### `grading.json`

```json
{
  "expectations": [
    {
      "text": "The output contains 'Seoul'",
      "passed": true,
      "evidence": "Confirmed 'extract Seoul region data' in the third step"
    }
  ],
  "summary": { "passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0 }
}
```

**Field name caution:** use `text`, `passed`, and `evidence` exactly. Don't change them to other names such as `name`/`met`/`details`.

### `timing.json`

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

When a sub-agent's completion notification arrives, save `total_tokens` and `duration_ms` immediately. These two values can be seen only when the notification is received, and cannot be recovered later.

<a id="8-what-not-to-put-in-a-skill"></a>

## 8. What not to put in a skill

- Supplementary documents such as `README.md`, `CHANGELOG.md`, and `INSTALLATION_GUIDE.md`
- Information needed only during the process of making the skill (test results, revision history)
- Manuals for users (a skill is a set of instructions that an AI agent follows)
- General knowledge that Claude already knows
- Items used only in v1 (`TeamCreate`/`TeamDelete`, experimental flags, a `model` assigned to all agents in bulk)

<a id="9-skill-reuse-design"></a>

## 9. Skill reuse design

Before creating a new skill, compare its function with existing skills in `.claude/skills/`. If a harness is built or extended several times, skills with the same function can pile up under different names.

| Relationship to existing skills | Action |
|------|------|
| An existing skill covers all of the new function | Don't create a new one; connect the existing skill to the agent. |
| It partly overlaps, and generalizing the existing skill lets it handle the new function too | Generalize and extend the existing skill. |
| It partly overlaps, but the domain was intentionally specialized | Create a new, separate skill. |
| The function's scope is entirely different | Create a new one. |

**Principle:** the more a skill focuses on one role, the easier it is to reuse and the less duplication there is. If it has two or more roles, first consider whether it can be split.

### How far to generalize

Generalization can go on endlessly, so stop at the scope of responsibility the skill has taken on. Keep intended domain specialization, and remove only dependencies attached by accident.

For example, generalizing a "fintech risk assessment PDF" skill goes as follows.

| Dependency removed | Result |
|------|------|
| Fintech | "Assessment result PDF". If the scope of responsibility is assessment reports, stop here. |
| Assessment | "PDF form filling". If a skill with the same function already exists, don't create a new one; use that skill. |

If the scope of responsibility was set to "fintech risk assessment" from the start, don't generalize it; keep it as a separate skill.

Extending an existing skill can also change the behavior of agents that use it. Before extending, check which agents use this skill, and reflect the widened scope of use in the `description`.
