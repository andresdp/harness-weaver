# Workflow Usage Examples — Script Skeletons and Points to Watch

Explains script patterns that can be put in coordination skills when building a harness in workflow coordination mode (mode A). Scripts are written in pure JavaScript and passed via the `script` parameter of the `Workflow` tool.

---

## Contents

1. [Basic skeleton](#1-basic-skeleton)
2. [Distributed execution (fan-out) + adversarial verification](#2-distributed-execution-fan-out--adversarial-verification)
3. [Judge panel](#3-judge-panel)
4. [Repeat until there are no new items (Loop-until-dry)](#4-repeat-until-there-are-no-new-items-loop-until-dry)
5. [Repetition tied to the token budget](#5-repetition-tied-to-the-token-budget)
6. [Custom types + structured output](#6-custom-types--structured-output)
7. [Points to watch (verification list)](#7-points-to-watch-verification-list)

---

## 1. Basic skeleton

A full runnable script starts with a `meta` literal. The titles used in `phase()` calls must exactly match the `title`s in `meta.phases`.

```javascript
export const meta = {
  name: 'domain-task',
  description: 'One-line description (shown in the permission dialog)',
  phases: [
    { title: 'collect', detail: 'research each perspective in parallel' },
    { title: 'verify', detail: 'verify each found item by looking for grounds to refute it' },
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
- **Use `pipeline()` by default, and use `parallel()` only when a synchronization barrier is truly needed.** A synchronization barrier is needed only when the next stage must compare **all** of the previous stage's results with each other. Deduplication, early termination when the total result is 0 items, and prompts that say "compare with other findings" fall into this case.
- Don't write the values of the item list directly in the script. Where possible, pass the list that the main agent finalized by pre-investigation as `args.items`.
- If a timestamp is needed, pass it as `args.now`. `Date.now()` cannot be used.

## 2. Distributed execution (fan-out) + adversarial verification

Collect review results from each perspective, then verify the results one by one. Don't wait until the other perspectives' research finishes; verify the results from a perspective as soon as that perspective's research finishes.

```javascript
export const meta = {
  name: 'review-fanout-verify',
  description: 'Reviews per perspective, then verifies each found item by looking for grounds to refute it',
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
  args.dimensions,   // e.g., [{key:'security', prompt:'...'}, {key:'perf', prompt:'...'}]
  d => agent(d.prompt, { label: `review:${d.key}`, phase: 'review', schema: FINDINGS }),
  review => parallel((review?.findings ?? []).map(f => () =>
    agent(`Verify the following review result. Judge confirmed if the evidence is sufficient, refuted if clearly refuted, and uncertain if hard to judge: ${JSON.stringify(f)}`,
      { label: `verify:${f.file}`, phase: 'verify', schema: VERDICT })
      .then(v => ({ ...f, verdict: v }))))
)
const confirmed = results.flat().filter(Boolean)
  .filter(f => f.verdict?.status === 'confirmed')
log(`${confirmed.length} of ${results.flat().filter(Boolean).length} items passed verification.`)
return { confirmed }
```

To make verification stricter, run three adversarial verification agents for each found item. Pass only items that two or more of them judge `confirmed` with sufficient evidence. Giving each agent different verification criteria, such as correctness, security, and reproducibility, finds more varied problems than checking repeatedly by the same criteria.

## 3. Judge panel

A pattern used for design work with many possible solutions. Make N mutually independent drafts, judge them in parallel, and make the final version based on the judging results.

```javascript
export const meta = {
  name: 'design-judge-panel',
  description: 'Makes N independent drafts, judges them, and writes the final version based on the top-scoring draft',
  phases: [{ title: 'draft' }, { title: 'judge' }, { title: 'synthesize' }],
}

const angles = args.angles?.length
  ? args.angles
  : ['MVP-first', 'risk-management-first', 'user-experience-first']
const judgeCount = args.judgeCount ?? 3

phase('draft')
const drafts = (await parallel(angles.map(a => () =>
  agent(`Write a draft independently from the ${a} perspective: ${args.brief}`,
    { label: `draft:${a}`, phase: 'draft' }))))
  .filter(Boolean)
log(`Made ${drafts.length} of ${angles.length} drafts.`)
if (!drafts.length) return { error: 'There are no completed drafts.', drafts: [] }

phase('judge')   // synchronization barrier needed: all drafts must be compared with each other
const SCORE = { type: 'object', required: ['scores'], properties: {
  scores: { type: 'array', items: { type: 'object',
    required: ['index', 'score', 'strengths'], properties: {
      index: { type: 'integer' }, score: { type: 'number' }, strengths: { type: 'string' } } } } } }
const judged = (await parallel(Array.from({ length: judgeCount }, (_, j) => () =>
  agent(`Score the following ${drafts.length} drafts:\n${drafts.map((d, i) => `[${i}] ${d}`).join('\n---\n')}`,
    { label: `judge:${j}`, phase: 'judge', schema: SCORE })))).filter(Boolean)
log(`Received results from ${judged.length} of ${judgeCount} judges.`)
if (!judged.length) return { error: 'There are no completed judging results.', drafts }

phase('synthesize')
const ranked = drafts.map((_, i) => {
  const scores = judged.flatMap(r =>
    r.scores.filter(x => x.index === i).map(x => x.score)).filter(Number.isFinite)
  return scores.length
    ? { index: i, average: scores.reduce((sum, score) => sum + score, 0) / scores.length }
    : null
}).filter(Boolean)
if (!ranked.length) return { error: 'There are no valid per-draft scores.', drafts, judged }
const winner = ranked.reduce((best, item) =>
  item.average > best.average ? item : best).index
const finalDraft = await agent(
  `Write the final version based on the highest-scoring draft. Reflect the strengths of the other drafts where needed.\nTop-scoring draft:\n${drafts[winner]}\nJudges' comments:\n${JSON.stringify(judged)}`,
  { phase: 'synthesize' })
if (!finalDraft) {
  log('Could not write the final version.')
  return { error: 'Could not write the final version.', drafts, judged, winner }
}
return finalDraft
```

## 4. Repeat until there are no new items (Loop-until-dry)

Used for work where it isn't known in advance how many items must be found. Repeat the search until no new items appear for K consecutive rounds.

The code in sections 4–6 consists of fragments to put into the basic skeleton of section 1. When used as a full script, put `meta` at the very front, and define the phase titles and schemas used along with it.

```javascript
const finders = args.finders ?? []
const dryLimit = args.dryRuns ?? 2
const findingKey = finding => JSON.stringify([
  finding.file ?? '', finding.title ?? '', finding.evidence ?? ''
])
const seen = new Set(), confirmed = []
if (!finders.length) return { confirmed, error: 'There are no search criteria.' }
let dry = 0
while (dry < dryLimit) {
  const found = (await parallel(finders.map(f => () =>
    agent(f.prompt, { phase: 'search', schema: FINDINGS })))).filter(Boolean).flatMap(r => r.findings)
  const fresh = found.filter(b => !seen.has(findingKey(b)))   // judge duplicates by seen, not by confirmed.
  if (!fresh.length) { dry++; continue }
  dry = 0
  fresh.forEach(b => seen.add(findingKey(b)))
  const judged = await parallel(fresh.map(b => () =>
    agent(`Verify the following review result. Judge confirmed if the evidence is sufficient, refuted if clearly refuted, and uncertain if hard to judge: ${JSON.stringify(b)}`,
      { phase: 'verify', schema: VERDICT })
      .then(v => ({ b, ok: v?.status === 'confirmed' }))))
  confirmed.push(...judged.filter(Boolean).filter(x => x.ok).map(x => x.b))
  log(`${confirmed.length} items confirmed so far; ${fresh.length} newly found in this round.`)
}
return { confirmed }
```

If duplicates are removed based on `confirmed`, items rejected in verification reappear every round, so the repetition never ends. Duplicates must be removed based on `seen`, which holds every item found even once.

## 5. Repetition tied to the token budget

In sessions where the user specified a token budget such as "+500k", the search range can be adjusted automatically according to the remaining budget. In unlimited sessions without `budget.total`, `remaining()` returns `Infinity`, so always check first in the condition that `budget.total` exists.

```javascript
const findings = []
while (budget.total && budget.remaining() > 50_000) {
  const r = await agent('Proceed with the next search task.', { schema: FINDINGS })
  if (r) findings.push(...r.findings)
  log(`Found ${findings.length} items so far; the remaining token budget is ${Math.round(budget.remaining() / 1000)}k.`)
}
// Approach that fixes the work scale in advance: const FLEET = budget.total ? Math.floor(budget.total / 100_000) : 3
```

## 6. Custom types + structured output

Use the `.claude/agents/{name}.md` definitions made by the harness as they are in the workflow.

```javascript
const r = await agent(
  `Verify the file _workspace/02_draft.md and return the found items`,
  { agentType: 'qa-inspector',      // .claude/agents/qa-inspector.md
    schema: FINDINGS,               // custom types also return only results that match the specified schema
    effort: 'high' })               // it is good to raise reasoning intensity in the verification phase
```

- If `agentType` is omitted, the default workflow sub-agent is used.
- Choose `model` according to the nature of each phase's work. Use `sonnet` for repetitive collection and conversion phases, `opus` for in-depth verification, judging, and design phases, and `fable` for overall planning and long-running phases. See `model-selection-guide.md` for detailed criteria.
- If several agents may modify files at the same time and conflict, specify `isolation: 'worktree'`. Preparing the working environment has a cost, so use it only when conflicts are actually possible.

## 7. Points to watch (verification list)

Check the list below when verifying workflow scripts in step 6-2 of the harness.

| Point to watch | Problem that appears | Prevention |
|------|------|------|
| Using variables or operations in `meta` | The script can't be parsed. | Put only literals in `meta`. |
| Using TypeScript syntax (`: string[]`, etc.) | The script can't be parsed. | Write in pure JavaScript. |
| Using `Date.now()` / `Math.random()` / `new Date()` | An error occurs because of the resume-protection feature. | Pass timestamps and seeds via `args`, and if randomness is needed, write prompts differently by index. |
| Missing `.filter(Boolean)` | The next stage stops because of the `null` returned by a failed agent. | Apply `.filter(Boolean)` before using the results of `parallel()` or `pipeline()`. |
| Unnecessary synchronization barriers | Agents that finished quickly wait for slow agents, so the overall execution time increases. | If the whole results don't need to be compared with each other, rewrite with `pipeline()`. |
| Mismatched `phase` titles | Progress isn't displayed in the intended groups. | Make the `phase()` calls and the `title`s in `meta.phases` match. |
| Calling global `phase()` inside a parallel stage | The groups for displaying progress conflict with each other. | Inside stages, specify `opts.phase` explicitly. |
| Removing duplicates based on `confirmed` | Rejected items reappear and the repetition never ends. | Remove duplicates based on the `seen` set. |
| Missing the `budget.total` check in token-budget repetition | In unlimited sessions, it keeps running until the number of `agent()` calls reaches the per-workflow limit. | Use the condition `while (budget.total && ...)`. |
| Processing only part without disclosing the processing range | Reports "all done" after processing only the top N. | State the number of unprocessed items in `log()`. |
| Not checking the execution record (`journal`) when diagnosing results | Mistakes empty results taken from the cache for success. | Before diagnosing a completed workflow, check the `journal` in the execution history (`transcript`) directory. |
| Writing the script to a file first | It goes through an unnecessary step. | Pass the script content directly in `script`. The file is preserved automatically on calling; when revising repeatedly, `Edit` the preserved file and call again with `scriptPath`. |
