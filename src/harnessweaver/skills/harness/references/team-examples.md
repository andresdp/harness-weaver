# Real-world team composition examples

Each example shows the criteria for choosing an execution mode that fits the task, plus the basic shape of the Harness v2 syntax. For mode definitions see `execution-modes.md`; for writing workflow scripts see `workflow-recipes.md`.

---

## Example 1: Comprehensive research team — workflow orchestration

**Composition:** Fan-out/Fan-in + adversarial verification

**Why this mode:** the research perspectives can be listed up front, and the per-claim verification procedure can be defined in code.

```
[Main] Pre-research: fix the research perspectives (official sources, media, communities, background)
     → Workflow(script, args: {axes, topic, ws})
         phase 'search': pipeline(axes, axis => agent(..., {schema: FINDINGS}))
         phase 'verify': run adversarial verification agents per claim → only claims that a majority judge as confirmed pass
         phase 'synthesize': run one completeness critic → if perspectives are missing, run additional research
     → Main writes the final report from the structured results returned
```

Define the research principles and the structured output format in `.claude/agents/researcher.md`, and the rebuttal-first verification principles in `.claude/agents/fact-checker.md`. The workflow names both agents with `agentType`.

Never arbitrarily discard conflicting information. Include it in the return schema together with its sources.

## Example 2: SF novel-writing team — mixed mode centered on persistent agents

**Composition:** Pipeline + Producer-Reviewer

**Why this mode:** worldview, characters, and plot must be adjusted in real time so they never contradict each other, so each expert must remember the earlier conversation. The reviewers, by contrast, only need to deliver results from independent perspectives, so sub-agents are sufficient.

```
Step 1 (persistent agents): Agent(name: "worldbuilder") + Agent(name: "character-designer")
               + Agent(name: "plot-architect") run in parallel
               → TaskCreate(worldview, characters, plot; state their mutual dependencies)
               → Leader relays: worldbuilder fixes the social structure
                 → passes it to character-designer via SendMessage
                 → if the characters' occupations clash with the worldview, ask
                   worldbuilder to adjust via SendMessage
                 Because the earlier context is retained, you can instruct
                 fixes on only part of it, e.g. "change only the merchant class
                 in the class structure we just settled on."
Step 2 (sub-agent): invoke prose-stylist once → it reads the three artifacts saved under _workspace/ and writes
Step 3 (parallel sub-agents): science-consultant + continuity-manager each review
Step 4 (persistent agent): you cannot send a SendMessage to prose-stylist, which was invoked only once.
                 If it had been run with a name in step 2, you could tell it to apply the review results.
                 If revisions look likely to repeat, give it a name from the start.
```

Give a `name` at first invocation to any agent you may need to send a revision request to later. An agent invoked only once cannot continue from its earlier conversation.

## Example 3: Comprehensive code review — workflow orchestration

**Composition:** Fan-out/Fan-in + adversarial verification

**Why this mode:** the review perspectives — security, performance, structure, tests — can be fixed up front, and the procedure that re-verifies each finding can also be expressed in code.

```javascript
// Review by perspective → adversarial verification for each finding
// It does not wait for the whole review to finish. As soon as the security review is done,
// findings from the security area are verified immediately even while the performance review is still running.
const FINDINGS = { type: 'object', required: ['findings'], properties: {
  findings: { type: 'array', items: { type: 'object',
    required: ['title', 'file', 'evidence'], properties: {
      title: { type: 'string' }, file: { type: 'string' }, evidence: { type: 'string' } } } } } }
const VERDICT = { type: 'object', required: ['status', 'reason'], properties: {
  status: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] },
  reason: { type: 'string' } } }
const results = await pipeline(
  [
    { key: 'security', prompt: 'Review from a security perspective.' },
    { key: 'perf', prompt: 'Review from a performance perspective.' },
    { key: 'arch', prompt: 'Review from a structural perspective.' },
    { key: 'test', prompt: 'Review from a testing perspective.' },
  ],
  d => agent(d.prompt, { phase: 'review', schema: FINDINGS }),
  r => parallel((r?.findings ?? []).map(f => () =>
    agent(`Verify the following finding. Judge it confirmed if the evidence is sufficient, refuted if it is clearly rebutted, or uncertain if it is hard to decide: ${JSON.stringify(f)}`,
      { phase: 'verify', schema: VERDICT })
      .then(verdict => ({ ...f, verdict }))))
)
const confirmed = results.flat().filter(Boolean)
  .filter(f => f.verdict?.status === 'confirmed')
```

In v1 this used a persistent team where reviewers shared findings over `SendMessage`. As in the example above, when a single finding is enough to verify, include that finding's evidence fully in the prompt and verify it right away. When findings must be compared across perspectives, gather all review results and verify after a synchronization barrier. Use persistent agents only when real-time conversation is genuinely required, such as debating a design direction.

## Example 4: Large-scale code migration — persistent supervisor collaboration or workflow orchestration

**Composition:** Fan-out/Fan-in if the work can be split up front; a supervisor if it must be re-split during execution

**Selection criterion:** choose the execution mode according to whether the work batches can be divided in advance.

Use a workflow when the work batches can be fixed up front.

```javascript
const MIGRATION_RESULT = { type: 'object', required: ['worktreePath', 'changedFiles'], properties: {
  worktreePath: { type: 'string', minLength: 1 },
  changedFiles: { type: 'array', minItems: 1, uniqueItems: true,
    items: { type: 'string', minLength: 1 } } } }
const MIGRATION_VERDICT = { type: 'object', required: ['status', 'reason'], properties: {
  status: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] },
  reason: { type: 'string' } } }
const migrated = await pipeline(args.batches,   // fix the work batches after pre-research estimates complexity
  b => agent(`Migrate the following batch of work and return the absolute path of the isolated worktree and the list of files actually changed: ${b.files.join(', ')}`,
    { agentType: 'migrator', isolation: 'worktree', schema: MIGRATION_RESULT }),
  (r, b) => r && agent(
    `In the isolated worktree ${r.worktreePath}, compare the migration targets with the files actually changed and verify omissions and errors. Original targets: ${b.files.join(', ')}. Actual changes: ${r.changedFiles.join(', ')}`,
    { agentType: 'qa-inspector', schema: MIGRATION_VERDICT })
    .then(verdict => ({ ...r, verdict })))
const confirmed = migrated.filter(Boolean)
  .filter(r => r.verdict?.status === 'confirmed')
return { confirmed }
```

Always pass the isolated worktree path containing the migration result to the adversarial verification agent. When the workflow finishes, the main agent inspects each `confirmed` result's `worktreePath` one by one and either merges the changes into the base branch or cherry-picks only the needed commits. Resolve conflicts before merging the next worktree, and apply the next change only after the integration tests pass. Do not merge `refuted` or `uncertain` results; report the reason they were dropped.

Use persistent agents when the work must be re-split as progress unfolds.

```
Leader registers work batches with TaskCreate (including depends_on)
→ Agent(name: "migrator-1"), Agent(name: "migrator-2"), Agent(name: "migrator-3") run in parallel
→ Check the result each time a completion notice arrives
→ For failed work, ask the cause via SendMessage, then re-assign with TaskUpdate
→ Run integration tests when everything is done
```

## Example 5: Webtoon production — persistent producer and one-shot reviewer

**Composition:** Producer-Reviewer

**Why this mode:** only one producer and one reviewer are needed, and review results go back to the producer at most twice, so a light mixed mode is enough.

```
Step 1: Agent(name: "artist") → generate panels → _workspace/panels/
Step 2: Agent(subagent_type: "webtoon-reviewer", prompt: "Review the panels") invoked once → PASS/FIX/REDO verdict
       → _workspace/review_report.md
Step 3: Only panels that received a REDO verdict are regenerated via SendMessage({to: "artist"}).
       Repeat at most twice. Because artist remembers the earlier context, you can
       narrow the instruction, e.g. "fix only the composition of panel 3."
Retry policy: if two revision rounds still do not pass, report the unresolved state and the reason to the user.
             If 50% or more of the panels get REDO, suggest that the user revise the prompt.
```

---

## How artifacts are stored

- **Agent definitions:** create them at `project/.claude/agents/{name}.md`. Always include the core role, working principles, input and output rules, re-invocation method, error handling, and collaboration method. Add communication rules for persistent agents, and structured output formats for agents used in workflows.
- **Skills:** create them at `project/.claude/skills/{name}/SKILL.md`, with `references/` and `scripts/` if needed.
- **Orchestrators:** always state the execution mode. Use the template in `orchestrator-template.md`.
- **Intermediate artifacts:** store them as `_workspace/{phase}_{agent}_{artifact}.{ext}` and keep them even after verification.
