# Practical Team Composition Examples

Each example shows the criteria for choosing an execution mode suited to the work and the basic form of Harness v2 syntax. See `execution-modes.md` for per-mode definitions and `workflow-recipes.md` for how to write workflow scripts.

---

## Example 1: Comprehensive research team — workflow coordination

**Composition:** distribute and integrate (fan-out/fan-in) + adversarial verification

**Reason for choice:** the perspectives to research can be enumerated in advance, and the procedure for verifying each claim can be defined in code.

```
[main] pre-investigation: finalize research perspectives (official sources, press, community, background)
     → Workflow(script, args: {axes, topic, ws})
         phase 'research': pipeline(axes, axis => agent(..., {schema: FINDINGS}))
         phase 'verify': run adversarial verification agents per claim → only claims a majority judges confirmed pass
         phase 'synthesize': run 1 omission reviewer → if a perspective is missing, research further
     → main writes the synthesis report from the returned structured results
```

The research principles and structured output format are defined in `.claude/agents/researcher.md`, and the refutation-first verification principles in `.claude/agents/fact-checker.md`. In the workflow, both agents are specified with `agentType`.

Don't arbitrarily discard one side of conflicting information. Put it in the return schema together with its sources.

## Example 2: Science-fiction novel writing team — hybrid mode centered on persistent agents

**Composition:** pipeline + generate and verify

**Reason for choice:** the world, characters, and plot must be adjusted in real time so they don't contradict each other, so each specialist must remember the earlier conversational context. Reviewers, on the other hand, only need to deliver results from mutually independent perspectives, so sub-agents are enough.

```
Phase 1 (persistent agents): run Agent(name: "worldbuilder") + Agent(name: "character-designer")
               + Agent(name: "plot-architect") in parallel
               → TaskCreate(world, characters, plot, with their mutual dependencies specified)
               → the leader relays: worldbuilder finalizes the social structure
                 → passes it to character-designer with SendMessage
                 → if a character's occupation conflicts with the world, request an adjustment from
                   worldbuilder with SendMessage
                 Since earlier context remains, it can be told to fix only part, such as "in the class
                 structure decided earlier, modify only the merchant class".
Phase 2 (sub-agent): call prose-stylist once → reads the three outputs saved in _workspace/ and writes
Phase 3 (sub-agents in parallel): science-consultant + continuity-manager review separately
Phase 4 (persistent agent): a prose-stylist called only once can't receive SendMessage.
                 If it was run with a name in phase 2, it can be told to reflect the review results.
                 If revisions look likely to repeat, give it a name from the start.
```

Give a `name` from the first run to agents that may be sent revision requests again. An agent called only once can't continue using its earlier conversational context.

## Example 3: Comprehensive code review — workflow coordination

**Composition:** distribute and integrate + adversarial verification

**Reason for choice:** review perspectives such as security, performance, structure, and tests can be fixed in advance, and the procedure for re-verifying each found item can also be expressed in code.

```javascript
// Review per perspective → adversarial verification for each found item
// Don't wait for the whole review. When the security review finishes, verify the problems found
// in the security area right away, even while the performance review is still in progress.
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
    agent(`Verify the following finding. Judge confirmed if the evidence is sufficient, refuted if clearly refuted, and uncertain if hard to judge: ${JSON.stringify(f)}`,
      { phase: 'verify', schema: VERDICT })
      .then(verdict => ({ ...f, verdict }))))
)
const confirmed = results.flat().filter(Boolean)
  .filter(f => f.verdict?.status === 'confirmed')
```

v1 used a persistent team in which reviewers shared findings with each other via `SendMessage`. If, as in the example above, a finding can be verified on its own, put enough of that item's evidence in the prompt and verify it right away. If it must be compared with findings from other perspectives, collect all review results, then verify behind a synchronization barrier. Use persistent agents only when real-time conversation is truly necessary, such as when the design direction must be debated.

## Example 4: Large-scale code migration — persistent supervisor collaboration or workflow coordination

**Composition:** distribute and integrate if the work can be divided in advance; supervisor if it must be re-divided during the work

**Selection criterion:** choose the execution mode according to whether the work batches can be divided in advance.

If the work batches can be fixed in advance, use a workflow.

```javascript
const MIGRATION_RESULT = { type: 'object', required: ['worktreePath', 'changedFiles'], properties: {
  worktreePath: { type: 'string', minLength: 1 },
  changedFiles: { type: 'array', minItems: 1, uniqueItems: true,
    items: { type: 'string', minLength: 1 } } } }
const MIGRATION_VERDICT = { type: 'object', required: ['status', 'reason'], properties: {
  status: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] },
  reason: { type: 'string' } } }
const migrated = await pipeline(args.batches,   // finalize the work batches after estimating complexity by pre-investigation
  b => agent(`Migrate the following work batch, and return the absolute path of the isolated worktree and the list of actually changed files: ${b.files.join(', ')}`,
    { agentType: 'migrator', isolation: 'worktree', schema: MIGRATION_RESULT }),
  (r, b) => r && agent(
    `In the isolated worktree ${r.worktreePath}, cross-check the migration targets against the actually changed files to verify omissions and errors. Original targets: ${b.files.join(', ')}. Actual changes: ${r.changedFiles.join(', ')}`,
    { agentType: 'qa-inspector', schema: MIGRATION_VERDICT })
    .then(verdict => ({ ...r, verdict })))
const confirmed = migrated.filter(Boolean)
  .filter(r => r.verdict?.status === 'confirmed')
return { confirmed }
```

Always pass the adversarial verification agent the path of the isolated worktree that holds the migration result. When the workflow ends, the main agent checks the `worktreePath` of each `confirmed` result one by one and merges the changes into the base branch, or cherry-picks only the needed commits. If a conflict arises, resolve it before merging the next worktree, and apply the next change only after the integration tests pass. Don't merge `refuted` or `uncertain` results; report the reasons for their omission.

If the work must be re-divided according to progress, use persistent agents.

```
The leader registers work batches with TaskCreate (including depends_on)
→ run Agent(name: "migrator-1"), Agent(name: "migrator-2"), Agent(name: "migrator-3") in parallel
→ check the result each time a completion notification arrives
→ for failed tasks, check the cause with SendMessage, then reassign with TaskUpdate
→ integration tests when everything finishes
```

## Example 5: Webtoon production — a persistent generator and a one-off reviewer

**Composition:** generate and verify

**Reason for choice:** only one generator and one reviewer are needed. Review results only need to be sent back to the generator at most twice, so a light hybrid mode is enough.

```
Phase 1: Agent(name: "artist") → generate panels → _workspace/panels/
Phase 2: call Agent(subagent_type: "webtoon-reviewer", prompt: "Review the panels") once → PASS/FIX/REDO verdict
       → _workspace/review_report.md
Phase 3: instruct regeneration with SendMessage({to: "artist"}) only for panels that received a REDO verdict
       Repeat at most twice. Since artist remembers the earlier context,
       instructions can be narrowed in scope, such as "fix only the composition of panel 3".
Retry policy: if it doesn't pass after two revisions, inform the user of the unresolved status and the cause.
             If 50% or more of all panels are REDO, propose to the user that the prompt be revised.
```

---

## How outputs are stored

- **Agent definitions:** create them in `project/.claude/agents/{name}.md`. Always write the core role, working principles, input and output rules, how to be re-invoked, error handling, and collaboration method. Add communication rules for persistent agents, and a structured output format for agents to be used in workflows.
- **Skills:** create them in `project/.claude/skills/{name}/SKILL.md`, with `references/` and `scripts/` if needed.
- **Orchestrator:** always write the execution mode. Use the templates in `orchestrator-template.md`.
- **Intermediate outputs:** save them in the form `_workspace/{phase}_{agent}_{artifact}.{ext}`, and keep them even after verification is finished.
