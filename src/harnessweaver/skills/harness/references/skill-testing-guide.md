# Skill Testing and Iterative Improvement Guide

This guide explains how to verify the quality of skills built with the harness and improve them over multiple rounds. It is a reference that supplements step 6 of `SKILL.md`.

---

## Table of contents

1. [Testing approach overview](#1-testing-approach-overview)
2. [How to write test prompts](#2-how-to-write-test-prompts)
3. [Comparing the with-skill run and the baseline run](#3-comparing-the-with-skill-run-and-the-baseline-run)
4. [Running A/B tests as a workflow (v2)](#4-running-ab-tests-as-a-workflow-v2)
5. [Quantitative evaluation with assertions](#5-quantitative-evaluation-with-assertions)
6. [Using specialist agents](#6-using-specialist-agents)
7. [Iterative improvement procedure](#7-iterative-improvement-procedure)
8. [Verifying `description` trigger conditions](#8-verifying-description-trigger-conditions)
9. [Test workspace structure](#9-test-workspace-structure)

---

<a id="1-testing-approach-overview"></a>

## 1. Testing approach overview

Skill quality is checked with both **qualitative evaluation**, where a person judges the artifacts, and **quantitative evaluation**, where assertions drive the scoring.

| Evaluation type | Method | Suitable skills |
|----------|------|-----------|
| **Qualitative evaluation** | The user reviews the artifacts directly. | Skills whose quality judgment requires a human eye, such as writing style, design, or creative work |
| **Quantitative evaluation** | Scoring is automated according to assertions. | Skills whose results can be checked objectively, such as file creation, data extraction, or code generation |

Proceed in the order **write → run tests → evaluate → improve → test again**.

## 2. How to write test prompts

### Writing principles

Write test prompts as **concrete, natural sentences a real user would actually type**. Abstract or deliberately contrived prompts make it hard to tell whether the skill works in real usage.

**Bad examples:** `"Process the PDF"`, `"Extract the data"`

**Good example:**

```
"From 'Q4_revenue_final_v2.xlsx' in the Downloads folder, use column C (revenue) and
column D (costs) to add a profit margin (%) column, then sort by it, descending."
```

### How to vary the prompts

- Mix formal phrasing with casual phrasing.
- Mix requests that state the intent outright with requests where the intent must be inferred from context. For example, include both cases where the file format is stated explicitly and cases where it must be inferred.
- Mix simple tasks with complex ones, and include abbreviations, typos, and everyday expressions in some prompts.

### Coverage of use cases

Start with two or three prompts. Always include one core use case and one edge case, and if needed add one more case that requests several tasks at once.

<a id="3-comparing-the-with-skill-run-and-the-baseline-run"></a>

## 3. Comparing the with-skill run and the baseline run

### 3-1. How to compare the two runs

For each test prompt, run two sub-agents **in parallel** within a single message.

- **With-skill run**: Reads the skill first, does the work, and saves the results to `_workspace/iteration-N/eval-{id}/with_skill/outputs/`.
- **Baseline run**: Handles the same prompt without the skill and saves the results to `_workspace/iteration-N/eval-{id}/without_skill/outputs/`.

### 3-2. How to choose the baseline run

| Situation | Baseline run |
|------|----------|
| Creating a new skill | Run the same prompt without the skill. |
| Improving an existing skill | Preserve the pre-edit skill as a separate copy and use it. |

### 3-3. Record run time and token usage

As soon as a sub-agent's completion notification arrives, save `total_tokens` and `duration_ms` **immediately**. These two values are only visible when the completion notification is received and cannot be recovered later.

<a id="4-running-ab-tests-as-a-workflow-v2"></a>

## 4. Running A/B tests as a workflow (v2)

When there are three or more test cases, or when verification must be repeated over several rounds, build the A/B test itself as a workflow script. Use it only when the user has agreed to run the tests.

```javascript
export const meta = {
  name: 'skill-ab-test',
  description: 'Runs the with-skill and baseline runs, then grades them blind',
  phases: [{ title: 'Run' }, { title: 'Grade' }],
}
const RUN_RESULT = { type: 'object', required: ['saved', 'files'], properties: {
  saved: { type: 'boolean' },
  files: { type: 'array', minItems: 2, items: { type: 'string', minLength: 1 } } } }
const SLOT_GRADE = { type: 'object', required: ['expectations', 'summary'], properties: {
  expectations: { type: 'array', items: { type: 'object',
    required: ['text', 'passed', 'evidence'], properties: {
      text: { type: 'string' }, passed: { type: 'boolean' }, evidence: { type: 'string' } } } },
  summary: { type: 'object', required: ['passed', 'failed', 'total', 'pass_rate'], properties: {
    passed: { type: 'integer' }, failed: { type: 'integer' }, total: { type: 'integer' },
    pass_rate: { type: 'number' } } } } }
const GRADE = { type: 'object', required: ['A', 'B', 'comparison'], properties: {
  A: SLOT_GRADE,
  B: SLOT_GRADE,
  comparison: { type: 'object', required: ['preferred', 'reason'], properties: {
    preferred: { type: 'string', enum: ['A', 'B', 'tie'] },
    reason: { type: 'string' } } } } }

const results = await pipeline(
  args.evals,   // [{id, prompt, assertions, skillPath, withSkillSlot: 'A' | 'B'}]
  e => {
    const withSkillSlot = e.withSkillSlot === 'B' ? 'B' : 'A'
    const baselineSlot = withSkillSlot === 'A' ? 'B' : 'A'
    return parallel([
      () => agent(
        `${e.prompt}\n\nFirst read and follow ${e.skillPath}. Save the artifacts to ${args.ws}/${e.id}/with_skill/outputs/ and also save the same files to ${args.ws}/${e.id}/blind/${withSkillSlot}/outputs/. Return every saved file path.`,
        { label: `with-skill:${e.id}`, phase: 'Run', schema: RUN_RESULT }),
      () => agent(
        `${e.prompt}\n\nSave the artifacts to ${args.ws}/${e.id}/without_skill/outputs/ and also save the same files to ${args.ws}/${e.id}/blind/${baselineSlot}/outputs/. Return every saved file path.`,
        { label: `baseline:${e.id}`, phase: 'Run', schema: RUN_RESULT }),
    ])
  },
  (runs, e) => {
    const completed = (runs ?? []).filter(Boolean)
    if (completed.length !== 2 || completed.some(r => !r.saved || r.files.length < 2)) {
      log(`${e.id}: skipping grading because the artifacts of the with-skill run and the baseline run are not all present.`)
      return null
    }
    return agent(
      `First confirm that artifacts exist in both ${args.ws}/${e.id}/blind/A/outputs/ and ${args.ws}/${e.id}/blind/B/outputs/. If either path is empty, do not grade and report the reason for the failure. If both artifacts are present, grade A and B separately and judge the better one as A, B, or tie. To preserve anonymity, do not open eval_metadata.json, with_skill/, or without_skill/. Assertions: ${JSON.stringify(e.assertions)}`,
      { label: `grade:${e.id}`, phase: 'Grade', schema: GRADE })
      .then(grade => {
        if (!grade) log(`${e.id}: skipping this case because no blind grading result was received.`)
        return grade
})
  }
)
const mapped = results.map((grade, index) => {
  if (!grade) return null
  const e = args.evals[index]
  const withSkillSlot = e.withSkillSlot === 'B' ? 'B' : 'A'
  const baselineSlot = withSkillSlot === 'A' ? 'B' : 'A'
  return {
    evalId: e.id,
    withSkill: grade[withSkillSlot],
    baseline: grade[baselineSlot],
    comparison: {
      preferred: grade.comparison.preferred === 'tie'
        ? 'tie'
        : grade.comparison.preferred === withSkillSlot ? 'with_skill' : 'baseline',
      reason: grade.comparison.reason,
    },
  }
}).filter(Boolean)
return { results: mapped }
```

The main agent assigns `withSkillSlot` alternately to A and B across the test cases. The grader reads only the neutral `blind/A/` and `blind/B/` paths, so it cannot tell which side used the skill. Only cases where both runs produced artifacts get graded, and once grading finishes, the main agent maps the A/B results back to the with-skill run and the baseline run. The mapped results are stored in each run directory's `grading.json`. Grading starts as soon as a single test case finishes, so there is no need to wait for every case to complete. After editing the skill, rerunning with `resumeFromRunId` reuses cached results and skips unchanged cases.

<a id="5-quantitative-evaluation-with-assertions"></a>

## 5. Quantitative evaluation with assertions

### 5-1. How to write assertions

A **good assertion** can be judged objectively true or false, makes it clear from its wording alone what is being checked, and measures an outcome that should improve when the skill is applied. Conditions that always pass even without the skill (for example, "output exists") or that require subjective human judgment (for example, "well written") are poor assertions.

### 5-2. Conditions checkable with code

Write assertions that can be verified with code as scripts. This is faster than eyeballing, produces more trustworthy results, and the same scripts can be reused across iterations.

### 5-3. Watch out for assertions with no discriminating power

An assertion that both the with-skill run and the baseline run pass 100% of the time measures no difference from using the skill. When you find one, delete it or rewrite it to be strict enough to expose the gap between the two runs.

### 5-4. Grading result schema

Follow the `grading.json` format (`text`/`passed`/`evidence` and `summary`) defined in `skill-writing-guide.md`.

## 6. Using specialist agents

| Role | What it does | When to use |
|------|--------|------------|
| **Grader** | Records whether each assertion passed along with the evidence, cross-checks factual claims in the artifacts, and also reviews the quality of the assertions themselves. | Every iteration |
| **Blind comparator** | Masks which artifact used the skill, shuffles the A/B order, and compares quality. | When you need to rigorously confirm that the new version is truly better |
| **Analyzer** | Analyzes statistical patterns such as assertions without discriminating power, eval cases with high result variance, and trade-offs between time and token usage. | After three or more iterations of results have accumulated |

<a id="7-iterative-improvement-procedure"></a>

## 7. Iterative improvement procedure

### 7-1. Improvement principles

1. **Generalize the feedback.** Fixing only the single test case that failed leads to overfitting. Rewrite it as a principle that applies to other cases too.
2. **Delete instructions that do not help.** Read the agents' work logs, and if the skill is causing unnecessary work, remove that instruction.
3. **Explain the why.** Even for short feedback, first identify why it matters, then change the skill so that the reason shows through.
4. **Add the tools that repeated work needs, in advance.** If every test rebuilds the same helper script, put that script in `scripts/`.

### 7-2. Iteration order

```
1. Revise the skill.
2. Rerun every test case in a new `iteration-{N+1}/` directory.
3. Present the results compared with the previous iteration to the user.
4. Apply the feedback, revise again, and repeat the same order.
```

**Stop condition:** Stop when the user is satisfied, when there is no feedback left to incorporate, or when no further meaningful improvement is possible.

### 7-3. Reread the draft with fresh eyes

When revising a skill, produce a draft first. Then, imagining yourself as a reviewer reading the draft for the first time, reread it from the top and fix it. Do not try to write it perfectly from the start.

<a id="8-verifying-description-trigger-conditions"></a>

## 8. Verifying `description` trigger conditions

### 8-1. Writing requests that evaluate invocation

Create 20 evaluation requests: 10 `should-trigger` requests that must invoke the skill and 10 `should-NOT-trigger` requests that must not.

**Criteria for writing evaluation requests:**

- Write concrete, natural sentences a real user would actually type.
- Include specifics such as file paths, the user's situation, column names, or company names.
- Focus on **boundary cases** where deciding whether to apply the skill is hard, rather than obvious cases.

**`should-trigger`:** Include requests that express the same intent in several different ways, requests that do not mention the file type but clearly need this skill, uncommon use cases, and requests that overlap with other skills but where this skill must be chosen.

**`should-NOT-trigger`:** **Near-miss boundary cases — similar wording but out of scope — are the important ones.** Include requests whose words look similar but where another tool or skill fits better. Obviously unrelated requests are not worth testing.

### 8-2. Check for conflicts with existing skills

1. Collect the `description` of every existing skill.
2. Check that the new skill's `should-trigger` requests do not wrongly invoke an existing skill.
3. If conflicts arise, write the scope and exclusion conditions in the `description` more explicitly.

### 8-3. Automated optimization (optional, advanced)

1. Split the 20 evaluation requests into 60% training and 40% test data.
2. Measure the current `description`'s trigger accuracy.
3. Analyze the failed cases and improve the `description`.
4. **Choose the best-performing `description` based on the test-set results.** Choosing by training-set results leads to overfitting.
5. Repeat this process up to five times.

> Check with a script that automates the headless invocation method (`claude -p`). It consumes a lot of tokens, so run it as the last step once the skill is sufficiently stable.

<a id="9-test-workspace-structure"></a>

## 9. Test workspace structure

```
_workspace/
├── iteration-1/
│   ├── eval-descriptive-name/
│   │   ├── eval_metadata.json
│   │   ├── with_skill/    (outputs/ + timing.json + grading.json)
│   │   ├── without_skill/ (outputs/ + timing.json + grading.json)
│   │   └── blind/         (A/outputs/ + B/outputs/)
│   └── benchmark.json
├── iteration-2/
└── evals/evals.json
```

**Retention rules:**

- Give `eval` directories names that describe their content instead of numbers (for example, `eval-multi-page-table-extraction`).
- Create a separate directory for each iteration and do not overwrite previous `iteration` directories.
- Do not delete `_workspace/`; it is needed for post-hoc verification and change history tracking.
