# Workflow usage recipes — basic script skeletons and pitfalls

This describes script patterns you can put in an orchestration skill when building a harness in workflow orchestration mode (mode A). Scripts are written in pure JavaScript and passed via the `Workflow` tool's `script` parameter.

---

## Table of contents

1. [Basic skeleton](#1-basic-skeleton)
2. [Fan-out + adversarial verification](#2-fan-out--adversarial-verification)
3. [Judge panel](#3-judge-panel)
4. [Loop-until-dry](#4-loop-until-dry)
5. [Token-budget-driven loops](#5-token-budget-driven-loops)
6. [Custom types + structured output](#6-custom-types--structured-output)
7. [Pitfalls (verification checklist)](#7-pitfalls-verification-checklist)

---

## 1. Basic skeleton

A complete runnable script starts with the `meta` literal. The titles used in `phase()` calls must exactly match the `title` values in `meta.phases`.

```javascript
export const meta = {
  name: 'domain-task',
  description: 'One-line description (shown in the permission dialog)',
  phases: [
    { title: 'collect', detail: 'search in parallel from each perspective' },
    { title: 'verify', detail: 'verify each finding by looking for rebutting evidence' },
  ],
}

phase('collect')
const raw = await pipeline(args.items, item =>
  agent(`...${item}...`, { label: `collect:${item}`, phase: 'collect', schema: COLLECT_SCHEMA }))

phase('verify')
// ...

return { result }   // the final return value is passed to the main agent
```

**Principles:**
- **Use `pipeline()` by default; use `parallel()` only when a synchronization barrier is truly required.** A barrier is required only when the next step must compare the **entire** results of the previous step against each other. Deduplication, early exit when the overall result set is empty, and "compare with the other findings" prompts fall in this category.
- Do not hardcode the item list in the script. Where possible, the main agent passes the list fixed during pre-research as `args.items`.
- If you need a timestamp, pass it as `args.now`. `Date.now()` is not available.

## 2. Fan-out + adversarial verification

Collect review results from each perspective, then verify them one by one. Do not wait for the other perspectives' searches to finish; as soon as one perspective finishes, verify the results that came out of it.

```javascript
export const meta = {
  name: 'review-fanout-verify',
  description: 'review each perspective, then verify each finding by looking for rebutting evidence',
  phases: [{ title: 'review' }, { title: 'verify' }],
}

const FINDINGS = { type: 'object', required: ['findings'], properties: {
  findings: { type: 'array', items: { type: 'object',
    required: ['title', 'file', 'evidence'], properties: {
      title: { type: 'string' }, file: { type: 'string' }, evidence: { type: 'string' } } } } } }
const VERDICT = { type: 'object', required: ['status', 'reason'], properties: {
  status: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] },
  reason: { type: 'string' } } }

const results = await pipeline(
  args.dimensions,   // e.g. [{key:'security', prompt:'...'}, {key:'perf', prompt:'...'}]
  d => agent(d.prompt, { label: `review:${d.key}`, phase: 'review', schema: FINDINGS }),
  review => parallel((review?.findings ?? []).map(f => () =>
    agent(`Verify the following review finding. Judge it confirmed if the evidence is sufficient, refuted if it is clearly rebutted, or uncertain if it is hard to decide: ${JSON.stringify(f)}`,
      { label: `verify:${f.file}`, phase: 'verify', schema: VERDICT })
      .then(v => ({ ...f, verdict: v }))))
)
const confirmed = results.flat().filter(Boolean)
  .filter(f => f.verdict?.status === 'confirmed')
log(`Of ${results.flat().filter(Boolean).length} total findings, ${confirmed.length} passed verification.`)
return { confirmed }
```

To verify more strictly, run three adversarial verification agents per finding. Only items that at least two of them judge as `confirmed` with sufficient evidence pass. Giving each agent a different verification criterion — accuracy, security, reproducibility — finds a wider variety of problems than repeating an identical check.

## 3. Judge panel

Use this pattern for design work with many possible solutions. Build N independent drafts, judge them in parallel, then produce the final draft from the judging results.

```javascript
export const meta = {
  name: 'design-judge-panel',
  description: 'build N independent drafts, judge them, then write the final draft based on the top-scoring one',
  phases: [{ title: 'draft' }, { title: 'judge' }, { title: 'synthesize' }],
}

const angles = args.angles?.length
  ? args.angles
  : ['MVP-first', 'risk-management-first', 'user-experience-first']
const judgeCount = args.judgeCount ?? 3

phase('draft')
const drafts = (await parallel(angles.map(a => () =>
  agent(`Write an independent draft from a ${a} perspective: ${args.brief}`,
    { label: `draft:${a}`, phase: 'draft' }))))
  .filter(Boolean)
log(`Produced ${drafts.length} of ${angles.length} drafts.`)
if (!drafts.length) return { error: 'No draft was completed.', drafts: [] }

phase('judge')   // a synchronization barrier is required: all drafts must be compared with each other
const SCORE = { type: 'object', required: ['scores'], properties: {
  scores: { type: 'array', items: { type: 'object',
    required: ['index', 'score', 'strengths'], properties: {
      index: { type: 'integer' }, score: { type: 'number' }, strengths: { type: 'string' } } } } } }
const judged = (await parallel(Array.from({ length: judgeCount }, (_, j) => () =>
  agent(`Score the following ${drafts.length} drafts:\n${drafts.map((d, i) => `[${i}] ${d}`).join('\n---\n')}`,
    { label: `judge:${j}`, phase: 'judge', schema: SCORE })))).filter(Boolean)
log(`Received results from ${judged.length} of ${judgeCount} judges.`)
if (!judged.length) return { error: 'No completed judging results.', drafts }

phase('synthesize')
const ranked = drafts.map((_, i) => {
  const scores = judged.flatMap(r =>
    r.scores.filter(x => x.index === i).map(x => x.score)).filter(Number.isFinite)
  return scores.length
    ? { index: i, average: scores.reduce((sum, score) => sum + score, 0) / scores.length }
    : null
}).filter(Boolean)
if (!ranked.length) return { error: 'No valid per-draft scores.', drafts, judged }
const winner = ranked.reduce((best, item) =>
  item.average > best.average ? item : best).index
const finalDraft = await agent(
  `Write the final draft based on the top-scoring draft. Fold the strengths of the other drafts in where needed.\nTop-scoring draft:\n${drafts[winner]}\nJudging notes:\n${JSON.stringify(judged)}`,
  { phase: 'synthesize' })
if (!finalDraft) {
  log('Failed to produce the final draft.')
  return { error: 'Failed to produce the final draft.', drafts, judged, winner }
}
return finalDraft
```

## 4. Loop-until-dry

Use this for tasks where you cannot know in advance how many items there are to find. Repeat the search until K consecutive rounds produce no new items.

The code in sections 4–6 is a fragment to insert into the skeleton from section 1. To use it as a full script, put `meta` at the top and define the phase titles and schemas you use along with it.

```javascript
const finders = args.finders ?? []
const dryLimit = args.dryRuns ?? 2
const findingKey = finding => JSON.stringify([
  finding.file ?? '', finding.title ?? '', finding.evidence ?? ''
])
const seen = new Set(), confirmed = []
if (!finders.length) return { confirmed, error: 'No search criteria provided.' }
let dry = 0
while (dry < dryLimit) {
  const found = (await parallel(finders.map(f => () =>
    agent(f.prompt, { phase: 'search', schema: FINDINGS })))).filter(Boolean).flatMap(r => r.findings)
  const fresh = found.filter(b => !seen.has(findingKey(b)))   // dedupe against seen, never against confirmed
  if (!fresh.length) { dry++; continue }
  dry = 0
  fresh.forEach(b => seen.add(findingKey(b)))
  const judged = await parallel(fresh.map(b => () =>
    agent(`Verify the following review finding. Judge it confirmed if the evidence is sufficient, refuted if it is clearly rebutted, or uncertain if it is hard to decide: ${JSON.stringify(b)}`,
      { phase: 'verify', schema: VERDICT })
      .then(v => ({ b, ok: v?.status === 'confirmed' }))))
  confirmed.push(...judged.filter(Boolean).filter(x => x.ok).map(x => x.b))
  log(`${confirmed.length} items confirmed so far; ${fresh.length} newly found in this round.`)
}
return { confirmed }
```

If you dedupe against `confirmed`, items refuted during verification reappear every round and the loop never ends. Deduplicate against `seen`, the set of everything ever found at least once.

## 5. Token-budget-driven loops

In sessions where the user specifies a token budget such as "+500k", you can automatically adjust the search scope to the remaining budget. In unlimited sessions with no `budget.total`, `remaining()` returns `Infinity`, so always check that `budget.total` exists first.

```javascript
const findings = []
while (budget.total && budget.remaining() > 50_000) {
  const r = await agent('Proceed with the next search task.', { schema: FINDINGS })
  if (r) findings.push(...r.findings)
  log(`Found ${findings.length} items so far; remaining token budget is ${Math.round(budget.remaining() / 1000)}k.`)
}
// To fix the fleet size up front: const FLEET = budget.total ? Math.floor(budget.total / 100_000) : 3
```

## 6. Custom types + structured output

Use the `.claude/agents/{name}.md` definitions the harness created directly in the workflow.

```javascript
const r = await agent(
  `Validate the file _workspace/02_draft.md and return the findings`,
  { agentType: 'qa-inspector',      // .claude/agents/qa-inspector.md
    schema: FINDINGS,               // custom types also return only results matching the given schema
    effort: 'high' })               // raising the reasoning effort is a good idea for verification steps
```

- Omit `agentType` to use the default workflow sub-agent.
- Choose `model` by the character of each stage's work: `sonnet` for repetitive collection and transformation stages, `opus` for deep verification, judging, and design stages, and `fable` for overall planning and long-running stages. See `model-selection-guide.md` for detailed criteria.
- If multiple agents could edit files at the same time and conflict, set `isolation: 'worktree'`. Preparing work environments has a cost, so use it only when a real conflict is possible.

## 7. Pitfalls (verification checklist)

Check this list when verifying a workflow script in step 6-2 of the harness.

| Pitfall | Resulting problem | Prevention |
|------|------|------|
| Using variables or expressions in `meta` | The script cannot be parsed. | Put only literals in `meta`. |
| Using TypeScript syntax (`: string[]`, etc.) | The script cannot be parsed. | Write pure JavaScript. |
| Using `Date.now()` / `Math.random()` / `new Date()` | Errors occur because of the run-resume protection. | Pass timestamps and seeds via `args`; when randomness is needed, vary the prompts by index. |
| Missing `.filter(Boolean)` | A later stage breaks on `null` returned by a failed agent. | Apply `.filter(Boolean)` before using results from `parallel()` or `pipeline()`. |
| Unnecessary synchronization barriers | Fast agents wait for slow ones, so the total run time grows. | If results do not need to be compared with each other, rewrite with `pipeline()`. |
| Mismatched `phase` titles | Progress is not displayed in the intended groupings. | Make `phase()` calls match the `title` values in `meta.phases`. |
| Calling the global `phase()` inside a parallel stage | The progress groupings conflict with each other. | Inside a stage, set `opts.phase` explicitly. |
| Deduplicating against `confirmed` | Refuted items reappear and the loop never ends. | Deduplicate against the `seen` set. |
| Missing `budget.total` check in a token-budget loop | In unlimited sessions it keeps running until `agent()` calls hit the per-workflow cap. | Use the `while (budget.total && ...)` condition. |
| Processing only part of the scope without disclosing it | Reports "all done" after handling only the top N. | State the number of unprocessed items in `log()`. |
| Diagnosing results without checking the run record (`journal`) | Empty results served from cache are mistaken for success. | Before diagnosing a completed workflow, check the `journal` in the run transcript directory. |
| Writing the script to a file first | Adds an unnecessary step. | Pass the script content directly in `script`. The file is preserved automatically on invocation; for repeated edits, `Edit` the preserved file and invoke again with `scriptPath`. |
