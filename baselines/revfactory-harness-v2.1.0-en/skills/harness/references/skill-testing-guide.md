# Skill Testing and Iterative Improvement Guide

Explains how to verify the quality of skills made with the harness and improve them over several rounds. A reference that supplements step 6 of `SKILL.md`.

---

## Contents

1. [Overview of the testing approach](#1-overview-of-the-testing-approach)
2. [Writing test prompts](#2-writing-test-prompts)
3. [Comparing with-skill runs and baseline runs](#3-comparing-with-skill-runs-and-baseline-runs)
4. [Running A/B tests with a workflow (v2)](#4-running-ab-tests-with-a-workflow-v2)
5. [Quantitative evaluation with verification conditions (assertions)](#5-quantitative-evaluation-with-verification-conditions-assertions)
6. [Using specialist agents](#6-using-specialist-agents)
7. [Iterative improvement procedure](#7-iterative-improvement-procedure)
8. [Verifying `description` invocation conditions](#8-verifying-description-invocation-conditions)
9. [Test working directory structure](#9-test-working-directory-structure)

---

<a id="1-overview-of-the-testing-approach"></a>

## 1. Overview of the testing approach

A skill's quality is checked using both **qualitative evaluation, in which people judge the outputs**, and **quantitative evaluation, scored with verification conditions**.

| Evaluation approach | Method | Suitable skills |
|----------|------|-----------|
| **Qualitative evaluation** | The user reviews the outputs directly. | Skills where judging quality needs human evaluation, such as style, design, and creative work |
| **Quantitative evaluation** | Scored automatically according to verification conditions. | Skills whose results can be checked objectively, such as file creation, data extraction, and code generation |

Proceed in the order **write → run tests → evaluate → improve → test again**.

## 2. Writing test prompts

### Writing principles

Write test prompts as **concrete, natural sentences that a real user might enter**. With abstract or deliberately contrived prompts, it is hard to know whether the skill works well in real use.

**Poor example:** `"Process the PDF"`, `"Extract the data"`

**Good example:**

```
"In 'Q4_sales_final_v2.xlsx' in my Downloads folder, use column C (sales) and column D (costs)
to add a profit margin (%) column. Then sort it in descending order by profit margin."
```

### How to vary prompts

- Mix formal and casual tones.
- Mix requests that state the intent directly with requests whose intent must be inferred from context. For example, include both cases that name the file format directly and cases where it must be inferred from context.
- Mix simple and complex tasks, and put abbreviations, typos, and everyday expressions in some prompts.

### Range of use cases to include

Start with two or three prompts. Always include one core use case and one exceptional situation, and if needed add one case that requests several tasks at once.

<a id="3-comparing-with-skill-runs-and-baseline-runs"></a>

## 3. Comparing with-skill runs and baseline runs

### 3-1. How to compare the two runs

For each test prompt, run two sub-agents **concurrently** in one message.

- **With-skill run**: works after reading the skill and saves the results in `_workspace/iteration-N/eval-{id}/with_skill/outputs/`.
- **Baseline run**: handles the same prompt without the skill and saves the results in `_workspace/iteration-N/eval-{id}/without_skill/outputs/`.

### 3-2. How to choose the baseline run

| Situation | Baseline run |
|------|----------|
| Creating a new skill | Run the same prompt without the skill. |
| Improving an existing skill | Preserve the pre-change skill as a separate copy and use it. |

### 3-3. Recording execution time and token usage

When a sub-agent's completion notification arrives, save `total_tokens` and `duration_ms` **immediately**. These two values can be seen only when the completion notification is received, and cannot be recovered later.

<a id="4-running-ab-tests-with-a-workflow-v2"></a>

## 4. Running A/B tests with a workflow (v2)

If there are three or more test cases, or verification must be repeated several times, make the A/B test itself into a workflow script. Use it only when the user has agreed to running the tests.

```javascript
export const meta = {
  name: 'skill-ab-test',
  description: 'Runs with-skill and baseline executions, then grades them anonymously',
  phases: [{ title: 'run' }, { title: 'grade' }],
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
        `${e.prompt}\n\nFirst read and follow ${e.skillPath}. Save the outputs in ${args.ws}/${e.id}/with_skill/outputs/, and also save the same files in ${args.ws}/${e.id}/blind/${withSkillSlot}/outputs/. Return all the saved file paths.`,
        { label: `with:${e.id}`, phase: 'run', schema: RUN_RESULT }),
      () => agent(
        `${e.prompt}\n\nSave the outputs in ${args.ws}/${e.id}/without_skill/outputs/, and also save the same files in ${args.ws}/${e.id}/blind/${baselineSlot}/outputs/. Return all the saved file paths.`,
        { label: `base:${e.id}`, phase: 'run', schema: RUN_RESULT }),
    ])
  },
  (runs, e) => {
    const completed = (runs ?? []).filter(Boolean)
    if (completed.length !== 2 || completed.some(r => !r.saved || r.files.length < 2)) {
      log(`${e.id}: skipping grading because the outputs of the with-skill run and the baseline run are not both ready.`)
      return null
    }
    return agent(
      `First check that the outputs in both ${args.ws}/${e.id}/blind/A/outputs/ and ${args.ws}/${e.id}/blind/B/outputs/ exist. If either path is empty, don't grade; report the reason for failure. If both outputs exist, grade A and B separately and judge which is better as one of A, B, or tie. To keep anonymity, don't open eval_metadata.json, with_skill/, or without_skill/. Verification conditions: ${JSON.stringify(e.assertions)}`,
      { label: `grade:${e.id}`, phase: 'grade', schema: GRADE })
      .then(grade => {
        if (!grade) log(`${e.id}: skipping this case because no anonymous grading result was received.`)
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

The main agent alternates `withSkillSlot` between A and B for each test case. The grader reads only the neutral `blind/A/` and `blind/B/` paths, so it can't know which side had the skill applied. Only cases where both runs' outputs are ready are graded, and after grading the main agent maps the A/B results back to the with-skill run and the baseline run. The mapped results are saved in `grading.json` in each run directory. Grading starts as soon as one test case finishes, so there is no need to wait until all cases finish. If you re-run with `resumeFromRunId` after modifying the skill, unchanged cases are skipped using cached results.

<a id="5-quantitative-evaluation-with-verification-conditions-assertions"></a>

## 5. Quantitative evaluation with verification conditions (assertions)

### 5-1. Writing verification conditions

**Good verification conditions** can objectively decide true or false, make clear what they check just by reading the wording, and measure results that should improve when the skill is applied. Conditions that always pass even without the skill (e.g., "an output exists") or that need a person's subjective judgment (e.g., "it is well written") are not good.

### 5-2. Conditions that can be checked with code

Write verification conditions that can be checked with code as scripts. This is faster and more reliable than checking by eye, and the same script can be reused even when the iteration round changes.

### 5-3. Beware of verification conditions with no discriminating power

A verification condition that both the with-skill run and the baseline run pass 100% doesn't measure the difference made by using the skill. When you find such a condition, delete it, or change it into a condition demanding enough to reveal the difference between the two runs.

### 5-4. Grading result schema

Follow the `grading.json` format defined in `skill-writing-guide.md` (`text`/`passed`/`evidence` and `summary`).

## 6. Using specialist agents

| Role | What it does | When to use |
|------|--------|------------|
| **Grader** | Records whether each verification condition passed and the evidence, cross-checks the factual claims in the outputs, and also checks the quality of the verification conditions themselves. | Every iteration round |
| **Anonymous comparator** | Hides whether the skill was applied to the two outputs, shuffles the A/B order, and compares quality. | When rigorously checking whether a new version is actually better |
| **Analyzer** | Analyzes statistical patterns, such as verification conditions with no discriminating power, evaluation cases with large result variance, and trade-offs between time and token usage. | After the results of three or more iterations have accumulated |

<a id="7-iterative-improvement-procedure"></a>

## 7. Iterative improvement procedure

### 7-1. Improvement principles

1. **Generalize the feedback.** Fixing to fit only one test case causes overfitting. Fix with principles that can apply to other cases too.
2. **Delete instructions that don't help.** Read the agents' work records, and if the skill is causing them to do unnecessary work, remove that instruction.
3. **Explain the reason.** Even for short feedback, understand why it matters, then fix the skill so that the reason is visible.
4. **Put the tools needed for repeated work in advance.** If every test creates the same helper script anew, put that script in `scripts/`.

### 7-2. Iteration order

```
1. Modify the skill.
2. Re-run all test cases in a new `iteration-{N+1}/` directory.
3. Present the results compared with the previous iteration round to the user.
4. Receive feedback, modify again, and repeat the same order.
```

**Exit condition:** stop when the user is satisfied, when there is no feedback to reflect, or when no further meaningful improvement can be made.

### 7-3. Review the draft again from a fresh perspective

When modifying a skill, make a draft first. Then, thinking of yourself as a reviewer reading the draft for the first time, read it again from the beginning and fix it. Don't try to write it perfectly from the start.

<a id="8-verifying-description-invocation-conditions"></a>

## 8. Verifying `description` invocation conditions

### 8-1. Writing requests to evaluate invocation

Create 20 evaluation requests: 10 `should-trigger` requests where the skill should run, and 10 `should-NOT-trigger` requests where it should not.

**Criteria for writing evaluation requests:**

- Write concrete, natural sentences that a real user might enter.
- Include concrete information such as file paths, the user's situation, column names, and company names.
- Focus on **boundary cases** where it is hard to judge whether the skill applies, rather than obvious cases.

**`should-trigger`:** include requests that express the same intent in several ways, requests that don't specify the file type but clearly need the skill, uncommon use cases, and requests that overlap with other skills but where this skill should be chosen.

**`should-NOT-trigger`:** **boundary cases whose wording is similar but which are not targets (near misses) are what matters.** Include requests that use similar words but for which another tool or skill is more suitable. Obviously unrelated requests are not worth testing.

### 8-2. Checking for conflicts with existing skills

1. Collect the `description` of every existing skill.
2. Check that the new skill's `should-trigger` requests don't wrongly run an existing skill.
3. If a conflict arises, write the scope and exclusion conditions more clearly in the `description`.

### 8-3. Automatic optimization (optional, advanced)

1. Split the 20 evaluation requests into 60% training (Train) and 40% test (Test).
2. Measure the invocation accuracy of the current `description`.
3. Analyze the failed cases and improve the `description`.
4. Choose the `description` with the best performance based on the results on the **test data (Test set)**. Choosing based on the training data results causes overfitting.
5. Repeat this process up to five times.

> Check with a script that automates the headless mode that runs without a screen (`claude -p`). It uses many tokens, so run it as the last step after the skill is sufficiently stable.

<a id="9-test-working-directory-structure"></a>

## 9. Test working directory structure

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

- Give `eval` directories names that reveal their content instead of numbers (e.g., `eval-multi-page-table-extraction`).
- Create an independent directory for each iteration round, and don't overwrite previous `iteration` directories.
- Don't delete `_workspace/`, because it is needed for later verification and change-history tracking.
