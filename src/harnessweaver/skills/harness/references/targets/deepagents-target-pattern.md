# DeepAgents Target Pattern — Stage Directories, AGENTS.md, Skills, JSON Artifacts

This document defines the target conventions for a ported harness, distilled from a production DeepAgents application (a software-architecture pipeline: 4 stages, 11 skills, JSON artifacts in Firestore via a custom backend). `deepagents.md` (the DeepAgents target of the `harness` skill) emits artifacts that follow this pattern. When Claude Code is also selected, `runtime-parity.md` governs which semantic boundaries must stay separate.

## Runtime model

```
Python pipeline (deterministic)
  for stage_number in 1..N:
      agent = create_deep_agent(
          model=<one env-driven chat model>,
          memory=["/agent/AGENTS.md"],          # the stage's AGENTS.md
          skills=["/agent/skills/"],            # the stage's skills/ tree
          backend=CompositeBackend(
              default=<project artifact store>,  # e.g. Firestore, per user/project
              routes={"/agent/": FilesystemBackend(stage_dir, read-only-ish)}
          )
      )
      result = agent.invoke({"messages": [{"role": "user", "content": handoff_prompt}]})
      # completion asserted afterwards by checking expected artifact files
```

- **One deep agent per stage.** Each stage directory is self-contained: an `AGENTS.md` orchestrator memory plus its `skills/` tree. Use a separate ordered stage when the spec requires a distinct reviewer, revision step, validation gate, or human handoff; distinct stages do not require subagents.
- **Determinism lives in Python**: stage order, the hand-off prompt per stage, and the completion check (expected artifact filenames) are code, not prompts.
- **Within a stage**, the agent executes tasks in the order `AGENTS.md` pins; the only LLM discretion is *how* to perform each task, not *what order* or *whether* to verify.
- **The virtual filesystem is the data plane.** All artifacts are files on the composite backend: `/artifacts/*.json` for data, `/agent/**` for definitions.

## Directory layout

```
backend/app/agents/                     (or wherever the application keeps them)
├── stage1-<name>/
│   ├── AGENTS.md                       # orchestrator memory (see below)
│   └── skills/
│       ├── <task-1>/SKILL.md
│       └── <task-2>/SKILL.md
├── stage2-<name>/
│   ├── AGENTS.md
│   └── skills/…
└── …
```

- Stage directory names: `stage{N}-{snake_case_name}` (e.g. `stage1-requirements_drivers`).
- One directory per skill, named for the task it performs; `SKILL.md` inside (uppercase, Agent Skills convention).

## AGENTS.md — the stage orchestrator memory

Sections, in this order:

1. **Title + role line.** `# <Role> Agent` / `You are the Stage N <role> orchestrator.` + a responsibility sentence.
2. **Ordered task list.** `The workflow MUST be executed in exactly this order:` followed by the numbered tasks. "Each task is represented by a skill."
3. **Input** (stage 1) or **Input Artifacts** (later stages): the artifact paths this stage consumes.
4. **Rules.** The execution discipline, verbatim pattern:
   - Execute only ONE task at a time.
   - Before executing a task, read its SKILL.md.
   - Complete that task; write its artifact to `/artifacts/`.
   - Read the artifact back and verify it exists and contains valid JSON.
   - Only after verification continue to the next task.
   - Never skip a task. Never execute two tasks simultaneously.
   - Intermediate artifacts are the official communication mechanism between tasks.
5. **Scope boundaries.** An explicit "Do not propose / do not do" list appropriate to the stage's position (e.g. stage 1 of the architecture pipeline forbids styles/patterns/tactics/technologies — analysis only).
6. **Mandatory Completion Protocol.** "Before ending the workflow, verify that ALL of the following files exist:" + the artifact filenames; "The agent MUST NOT produce a final answer if any of these files is missing."
7. **Post-task protocol.** Numbered steps to run after each task: verify artifact → update workflow status → determine next incomplete task → continue.

## SKILL.md — a task skill

Frontmatter (Agent Skills convention): `name`, `description` (one sentence; what it identifies/produces).

Body sections, in this order:

1. **Objective** — one paragraph.
2. **Input Artifacts** — `Read:` + artifact paths consumed.
3. **Procedure** — numbered determinations the task must make (the design intelligence: what to extract, judge, or compute).
4. **Rules** — bulleted constraints, including a Correct/Incorrect example pair demonstrating the judgment boundary (e.g. attribute-vs-solution).
5. **Expected Output** — the artifact path, a fenced JSON structure block (snake_case keys, ID references to prior artifacts such as `source_requirement_ids`), the read-back verification sentence, and the boundary line "Do not perform <the next task>."

## JSON artifact contract

- Filenames: `{NN}_{step}.json` in execution order (e.g. `00_input.json` if the stage writes its input, then `01_…`, `02_…`).
- Cross-stage linkage by ID fields, never prose: an entity in stage N lists the IDs of the stage-(N−1) entities it derives from.
- Every JSON structure block documents required keys and their types inline (`"priority": "high"` as an enum example).
- The application's completion check (Python) asserts existence of every expected artifact after each stage run; per-skill read-back verification asserts validity within the run.

## Application wiring (`wiring.yaml` for any host; `port-manifest.md` for an existing application, not edited in place)

- `STAGES` registry: `{N: [stage_dir_name, handoff_prompt]}` — the prompt is one sentence stating the stage's responsibility and what it consumes.
- `STAGE_ARTIFACTS`: `{N: [artifact filenames]}` — drives the completion check and the result API.
- Factory: memory/skills mount paths and backend routing as shown in the runtime model above.
- Stage 1's hand-off prompt is built from project data (e.g. name, description, requirements list) in code.

## Code-side practices (langchain-skills alignment)

The Python side of a ported application follows the official [langchain-skills](https://github.com/langchain-ai/langchain-skills) guidance — notably `deep-agents-core`, `deep-agents-orchestration`, and `langgraph-human-in-the-loop`. The practices below are the ones that matter when turning a `port-manifest.md` into code; when this document and langchain-skills disagree, **langchain-skills wins on all code-side questions**.

- **Middleware selection is configuration, not implementation.** Deep Agents ship the capabilities as middleware — TodoListMiddleware (default), FilesystemMiddleware (configure the backend), SubAgentMiddleware (add ported specialists), HumanInTheLoopMiddleware (requires a checkpointer), SkillsMiddleware (provide skill directories), MemoryMiddleware (requires a Store). Don't hand-roll what a middleware provides.
- **Interrupts need a checkpointer.** Any pause-for-approval flow (`interrupt()` / `Command(resume=...)`) requires `create_deep_agent(..., checkpointer=...)`; tool-level approval can be enabled declaratively via `interrupt_on={"write_file": True}`. Surface as a manifest decision whenever the harness design had user confirmation points that should survive the port.
- **Node restart semantics make pre-interrupt side effects re-run.** On resume, the node executes from the beginning; use idempotent operations (upsert, check-before-create) before any interrupt, or place side effects after it. This constrains where the manifest may place approval gates relative to artifact writes.
- **Skills vs. memory division of labor:** SKILL.md directories are for on-demand, task-specific instructions; `AGENTS.md` is always-loaded general context. The port's split (procedures in skills, orchestration discipline in AGENTS.md) matches this intentionally — keep large reference material in skills, keep the memory file compact.
- **Progressive disclosure applies to skill bodies too:** frontmatter (`name`, `description`) is what gets surfaced; keep descriptions self-contained and specific so the agent loads the right skill without reading bodies.
- **User-fixable errors → interrupt, not retry.** Per the langchain-skills error strategy, missing user input should pause and collect data (`interrupt()`), while transient failures go to retry policies — when porting a harness error-handling policy, classify each error into the right lane rather than translating the policy verbatim.

## Style and length discipline

- AGENTS.md and SKILL.md bodies stay lean; the reference application's files run 60–120 lines each. Anything beyond ~500 lines is a smell that the task should be split.
- Imperative, declarative sentences; no hedging. The pattern relies on unambiguous MUST/NEVER statements.
- Write artifacts in the language the harness skill's language rule selects: the user's language, or the existing application's language when extending one.

## Known limitations of this pattern (port decisions, not defects)

- No inter-agent messaging: everything crosses boundaries as artifacts. Iterative negotiation between specialists doesn't fit; serialize it or extend with DeepAgents subagents.
- No per-agent model tiers in the reference application (single env-driven model). Tier rationale from the harness design survives as comments.
- No parallel verifier fan-out in the base pattern. Separate sequential reviewer stages preserve reviewer independence; N-verifier majority voting requires subagents or additional verification stages and must be reported as approximated if not implemented.
