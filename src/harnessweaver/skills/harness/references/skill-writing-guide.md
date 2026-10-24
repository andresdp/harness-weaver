# Skill Writing Guide

This guide explains in detail how to raise the quality of skills built with the harness. It is a reference that supplements step 4 of `SKILL.md`.

---

## Table of contents

1. [How to write the `description`](#1-how-to-write-the-description)
2. [Body writing style](#2-body-writing-style)
3. [How to define the output format](#3-how-to-define-the-output-format)
4. [How to write examples](#4-how-to-write-examples)
5. [Progressive disclosure](#5-progressive-disclosure)
6. [Criteria for deciding whether to bundle scripts](#6-criteria-for-deciding-whether-to-bundle-scripts)
7. [Data schema standards](#7-data-schema-standards)
8. [What not to include in a skill](#8-what-not-to-include-in-a-skill)
9. [Designing skills for reuse](#9-designing-skills-for-reuse)

---

<a id="1-how-to-write-the-description"></a>

## 1. How to write the `description`

The only skill fields exposed to Claude are `name` and `description`, and the specific trigger conditions go in the `description`. Claude reads these two fields and decides which skill to use.

### How skills get invoked

Claude tends not to invoke a skill for simple tasks it can easily handle with its basic tools. For example, a plain request like "read this PDF for me" may not invoke the skill no matter how well the `description` is written. The more complex the task — the more steps it involves or the more expert judgment it requires — the more likely the skill is to be invoked.

### Writing principles

1. State both **what the skill does** and **the specific situations in which it must be invoked**.
2. If there are lookalike cases where the skill must not be invoked, state the scope and exclusion conditions explicitly.
3. Keep in mind that Claude decides conservatively whether to invoke a skill, so phrase the situations that should trigger it somewhat assertively.
4. For skills that orchestrate multiple tasks, always include **words that signal follow-up work** (rerun, revise, extend, improve previous results).

### Good example

```yaml
description: "Reads PDF files and extracts text and tables, and performs merging,
  splitting, rotation, watermarking, encryption/decryption, and OCR. Always use this
  skill when the user mentions a .pdf file or asks for a PDF artifact. Especially
  useful for tasks needing conversion, editing, or analysis, not just 'reading' a PDF."
```

### Bad examples

- `"A skill that processes data"` — too vague to tell which files or tasks it covers.
- `"PDF-related tasks"` — says nothing about what it can do or when it must be invoked.

<a id="2-body-writing-style"></a>

## 2. Body writing style

### Explain the why first

A large language model (LLM) that understands why a rule exists can judge correctly even in unforeseen cases. Rather than listing do's and don'ts as bare commands, it is more effective to explain why the rule must be followed.

**Bad example:**

```markdown
Always use pdfplumber for table extraction. Never use PyPDF2 on tables.
```

**Good example:**

```markdown
Use pdfplumber when extracting tables. PyPDF2 is built for text extraction, so it
cannot preserve the row-and-column structure of a table. pdfplumber recognizes
cell boundaries and returns structured data.
```

### Rewrite feedback as principles that generalize

When feedback or testing uncovers a problem, do not tack on an instruction that fits only one specific case. Rewrite it as a principle that applies to other cases as well.

**Overfitted fix:** `If there is a "Q4 revenue" column, convert that column to numbers.`

**Generalized fix:** `If a column name contains a quantity word such as "revenue", "amount", or "count", convert that column to a numeric type. Leave values that cannot be converted as they are.`

### Write in the imperative

Prefer "Extract the table" over "This skill will extract the table" or "The table can be extracted". A skill is a set of instructions for an AI agent to follow.

### Reduce the amount of information to consult at once

The amount of information a model can hold in view at once (the context window) is limited. That budget covers not only the skill instructions but also everything else the task needs. Judge whether each sentence is worth its tokens against these criteria:

- "Does Claude already know this?" → Delete it.
- "Would Claude make a mistake without this explanation?" → Keep it.
- "Would one concrete example be clearer than a long explanation?" → Replace it with an example.

<a id="3-how-to-define-the-output-format"></a>

## 3. How to define the output format

For skills where the format of the artifact matters, specify the structure to follow.

```markdown
## Report structure
Follow this template exactly.

# [Title]
## Summary
## Key findings
## Recommendations
```

Keep the format description short and pair it with a real example for better results.

**Artifacts read by the next workflow step:** If the next step reads the artifact as code and processes it, specify a **JSON structure** instead of a markdown template. Also state that the final text is return data handed to the next step, not a message shown to the user. `Workflow`'s `agent()` enforces the return format with `schema`, so the structure defined in the skill and in the scripts must match.

<a id="4-how-to-write-examples"></a>

## 4. How to write examples

Concrete examples communicate rules more clearly than long explanations.

```markdown
## Commit message format

**Example 1:**
Input: Add user authentication using JWT tokens
Output: feat(auth): implement JWT authentication

**Example 2:**
Input: Fix a bug where the show-password button on the login page does not work
Output: fix(login): fix the password visibility toggle button
```

<a id="5-progressive-disclosure"></a>

## 5. Progressive disclosure

### Approach 1: Split files by business domain

```
bigquery-skill/
├── SKILL.md (overview + guidance for choosing a business domain)
└── references/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    └── product.md (API usage, features)
```

When the user asks about revenue, only `finance.md` is loaded.

### Approach 2: Read detailed instructions only when needed

```markdown
## Document editing
For simple edits, modify the XML directly.
**When change tracking is needed**, see [REDLINING.md](references/redlining.md).
```

### Approach 3: Add a table of contents to large references

For reference files longer than 300 lines, put a table of contents at the top of the file.

<a id="6-criteria-for-deciding-whether-to-bundle-scripts"></a>

## 6. Criteria for deciding whether to bundle scripts

Review the work logs of the agents that ran the tests. When the patterns below repeat, include the script or procedure in the skill.

| Recurring pattern | Action |
|------------|------|
| The same helper script is created in all three tests. | Put the script in `scripts/`. |
| The same `pip install` or `npm install` command is run every time. | Document the dependency installation step in the skill. |
| The same multi-step procedure is followed every time. | Write the standard procedure in the skill body. |
| After hitting a similar error, the same workaround is applied each time. | Document the known issue and its workaround in the skill. |

Always run scripts included in a skill yourself to verify they work.

## 7. Data schema standards

Use the standard schemas below so that data flows consistently between skills. The same schemas can be used when testing and evaluating skills built with the harness.

### `eval_metadata.json`

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": [
    "The artifact contains X",
    "A file was created in Y format"
  ]
}
```

### `grading.json`

```json
{
  "expectations": [
    {
      "text": "The artifact contains 'Seoul'",
      "passed": true,
      "evidence": "Confirmed 'extract Seoul-region data' in step 3"
    }
  ],
  "summary": { "passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0 }
}
```

**Field names matter:** Use `text`, `passed`, and `evidence` exactly. Do not rename them to `name`/`met`/`details` or anything else.

### `timing.json`

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

As soon as a sub-agent's completion notification arrives, save `total_tokens` and `duration_ms` immediately. These two values are only visible at the moment the notification is received and cannot be recovered later.

<a id="8-what-not-to-include-in-a-skill"></a>

## 8. What not to include in a skill

- Supplementary documents such as `README.md`, `CHANGELOG.md`, and `INSTALLATION_GUIDE.md`
- Information needed only while building the skill (test results, iteration history)
- User-facing manuals (a skill is a set of instructions for an AI agent to follow)
- General knowledge Claude already has
- Items used only in v1 (`TeamCreate`/`TeamDelete`, experimental flags, a `model` assigned to every agent)

## 9. Designing skills for reuse

Before creating a new skill, compare its functionality against the existing skills in `.claude/skills/`. If you build or extend the harness repeatedly, skills with identical functionality can pile up under different names.

| Relationship to an existing skill | Action |
|------|------|
| The existing skill covers all of the new functionality | Do not create a new one; connect the existing skill to the agent. |
| Only partially overlapping, and generalizing the existing skill would let it cover the new functionality | Generalize and extend the existing skill. |
| Partially overlapping, but the domain is deliberately specialized | Create it as a separate skill. |
| The scope of functionality is entirely different | Create a new one. |

**Principle:** The more a skill focuses on a single role, the easier it is to reuse and the less duplication you get. If it has two or more roles, first consider splitting it.

### How far to generalize

Generalization can go on forever, so stop at the scope of responsibility the skill has taken on. Keep the intentional domain specialization and strip away only the accidental dependencies.

For example, generalizing a "fintech risk assessment PDF" skill looks like this.

| Dependency stripped | Result |
|------|------|
| Fintech | "Assessment result PDF". If the skill's responsibility is assessment reports, stop here. |
| Assessment | "PDF formatting". If a skill with the same capability already exists, use it rather than creating a new one. |

If the scope of responsibility was defined as "fintech risk assessment" from the start, leave it as a separate skill without generalizing.

Extending an existing skill can also change the behavior of the agents that use it. Before extending, check which agents use the skill, and reflect the widened scope in its `description`.
