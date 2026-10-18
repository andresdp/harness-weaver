# Regenerating harness-100 Examples with Harness v2 — Prompt Cookbook

[harness-100](https://github.com/revfactory/harness-100) is the author's collection of 100 ready-to-use harnesses (Korean + English) across 10 domains. Analysis of sampled artifacts (`01-youtube-production`, `28-security-audit`, `44-market-research`, `96-real-estate-analyst`) shows they were **generated with the v1-generation factory** — before the v2 rebuild in this repo: lowercase `skill.md` files, agent-team-only execution, no `Workflow` scripts, no model tiering, and verbose CLAUDE.md files (all conventions v2 replaced).

This cookbook speculates what the equivalent **v2** generation prompts would look like: same domains, but producing v2-shaped artifacts (uppercase `SKILL.md`, per-phase execution modes, tiered models, adversarial verification where it fits, minimal-pointer CLAUDE.md). Use them as starting points and adjust the domain details to your project.

---

## How to prompt the v2 factory

The harness skill triggers on requests like **"build a harness for …"** or **"design an agent team for …"**. Three knobs are worth knowing:

- **Mode hint** — say *"the steps are fixed and repeatable"* to steer toward workflow orchestration (`Workflow` + `pipeline()` + schemas); say *"the agents need to negotiate and iterate*" for persistent named agents; results-only work becomes sub-agent delegation.
- **Methodology variation** — when the domain has an established method (ATAM, Diátaxis, OWASP, IMRaD…), say which *variant* you want up front: where the pipeline starts (which inputs are assumed vs. elicited from raw material), which step derives which artifact, and any reordering. Named methods have standard and alternative formulations; fixing the variant in the prompt prevents the factory from silently picking one. (Worked case: the ATAM appendix below.)
- **Scale & budget** — default output is deliberately small (2–5 agents). Add *"thorough"* or *"exhaustive"* for large fan-outs, or an explicit budget directive like `+500k` for workflow runs.
- **Language** — generated artifacts are written in the language you use in the conversation, regardless of edition.

Minimal form:

```
claude "build a harness for <domain team>"
```

Rich form (what most entries below use):

```
claude "build a harness for <domain>. <shape of the work: fixed pipeline vs. iterative negotiation>.
<key roles if you care>. <scale/budget if relevant>. <final deliverable>."
```

> **Verification gates:** the v2 factory validates trigger conditions (should-trigger + near-miss), runs dry runs, and adds adversarial verification to accuracy-critical phases — expect those to appear in the generated orchestrator without being asked.

## Prompt examples by category

Two per category from harness-100, mapped to v2 equivalents. "Expected v2 shape" reflects what the factory would generate per the current skill's mode-selection and pattern rules.

### 1. Content Creation (harness-100 #01–15)

**01 · YouTube production** — v1: 5-agent pipeline (strategist → scriptwriter → thumbnail → SEO → reviewer).

```
build a harness for a YouTube video production team. The pipeline is fixed for every
video: strategy brief → script → thumbnail concept → SEO package → cross-review,
so use a deterministic workflow. Include a completeness critic before final delivery.
```

*Expected v2 shape:* workflow orchestration, Pipeline pattern, schema-conforming briefs between stages, reviewer as adversarial verifier; thumbnail image generation delegated as a one-shot sub-agent call to the external image tool.

**14 · Translation & localization**

```
design an agent team for translating and localizing documentation into 5 languages.
The workflow is repeatable (extract → translate → back-check glossary → review),
so coordinate it as a workflow with per-language parallel fan-out. +300k budget.
```

*Expected v2 shape:* workflow with `pipeline()` over the language list, glossary consistency checks as an intermediate schema-validated stage.

### 2. Software Dev & DevOps (harness-100 #16–30)

**20 · CI/CD pipeline**

```
build a harness that designs and sets up a CI/CD pipeline for our monorepo.
Work is mostly one-shot analysis + generated config, so sub-agent delegation is fine;
include a QA agent that validates the pipeline definition end to end.
```

*Expected v2 shape:* sub-agent delegation with a verification pass; config generation on opus, static validation on sonnet.

**28 · Security audit** — v1: scanner ∥ code-analyst → pentest → consultant → reviewer.

```
build a harness for security audits: vulnerability scan and code analysis run in
parallel, then penetration-test reporting, remediation planning, and a final review.
The stages are fixed and every run needs the same checks — use workflow
orchestration, and verify each Critical/High finding with adversarial verification.
```

*Expected v2 shape:* workflow with `pipeline()` + parallel scan branches, OWASP coverage as schema assertions, adversarial verification on findings before they enter the report (v1 had a single reviewer; v2 would fan out N verifiers per finding).

### 3. Data & AI/ML (harness-100 #31–42)

**31 · ML experiment**

```
build a harness for ML experimentation: hypothesis → feature/data prep → training
runs → evaluation → write-up. Runs are repeatable and metric-driven, so use a
workflow with structured results per experiment; loop-until-dry when searching
hyperparameter combinations.
```

*Expected v2 shape:* workflow orchestration, experiment matrix as a fan-out, evaluation-analyst comparing structured results, judge-panel selection of the best candidate.

**41 · LLM app builder**

```
design an agent team for building RAG applications: chunking strategy, retrieval
eval, prompt drafting, and hallucination checks. Retrieval quality is measurable —
make eval loops a workflow; keep prompt iteration as a persistent collaborator.
```

*Expected v2 shape:* hybrid mode — workflow for eval fan-outs, persistent agent for prompt/negotiation loops.

### 4. Business & Strategy (harness-100 #43–55)

**44 · Market research** — v1: 5 agents (competitor / consumer / industry / trend analysts + reviewer).

```
build a harness for market research. Research perspectives are enumerable up front
(competitors, consumers, industry, trends), so fan them out in a workflow and
adversarially verify every claimed data point before synthesis. Exhaustive sweep.
```

*Expected v2 shape:* workflow, Fan-out/Fan-in + adversarial verification; only majority-`confirmed` claims reach the final report.

**50 · Pricing strategy**

```
design an agent team for pricing strategy: willingness-to-pay research (Van
Westendorp), competitor price mapping, tier design, and financial modeling.
Numbers must cross-check, so add adversarial verification between the model
and the final recommendation.
```

*Expected v2 shape:* workflow for the survey/mapping fan-out; Producer-Reviewer pair for tier design; DCF/model consistency verified before sign-off.

### 5. Education & Learning (harness-100 #56–65)

**56 · Language tutor**

```
build a harness for a language-tutoring workflow: level diagnosis → lesson
generation → practice drills → error analysis. Lessons are iterative and the
tutor must remember the learner's weak points, so use persistent agents
with a shared progress task list.
```

*Expected v2 shape:* persistent agent collaboration, Supervisor pattern, learner state tracked as shared tasks/files.

**60 · Debate simulator** — the natural v2 showcase: named opponents negotiating.

```
design an agent team that simulates structured debates: a proposition side, an
opposition side, and a judge. The whole point is live back-and-forth argument,
so use persistent named agents communicating via messages, with the judge
adjudicating rounds.
```

*Expected v2 shape:* persistent agents (proposition / opposition / judge), SendMessage rounds, judge as final arbiter — a mode v1 couldn't express deterministically.

### 6. Legal & Compliance (harness-100 #66–72)

**66 · Contract analyzer**

```
build a harness for contract analysis: clause extraction, risk flagging, benchmark
comparison against standard positions, and a summary memo. Every flagged risk
must cite the exact clause, and findings should be adversarially verified —
false alarms are costly. Workflow mode.
```

*Expected v2 shape:* workflow with citation-schema outputs, adversarial verification on each flagged risk (majority-confirmed only).

**68 · Patent drafter**

```
design an agent team for drafting patent applications: invention analysis, prior-art
framing, claim drafting, and claim-scope review. Claims need iterative refinement
between the drafter and the reviewer — persistent agents — while prior-art
search is a fan-out sub-agent task.
```

*Expected v2 shape:* hybrid — sub-agents for prior-art sweep, persistent Producer-Reviewer loop for claim refinement.

### 7. Health & Lifestyle (harness-100 #73–80)

**74 · Fitness program**

```
build a harness that creates training programs: intake assessment (goals, history,
equipment), program design against ACSM guidelines, progression planning, and a
safety review. The intake structure is fixed — workflow — and the safety review
must check every exercise against contraindications.
```

*Expected v2 shape:* workflow pipeline; safety review as schema-gated verification stage.

**76 · Travel planner**

```
design an agent team for travel planning: destination research, day-by-day
itinerary with route optimization, budget tracking, and a final feasibility
check. Fixed stages, repeatable per trip — workflow with a completeness critic.
```

*Expected v2 shape:* workflow, Pipeline + completeness critic verifying nothing (bookings, transfers, meal windows) is missing.

### 8. Communication & Docs (harness-100 #81–88)

**81 · Technical writer**

```
build a harness for producing technical documentation on a Diátaxis basis:
tutorials, how-to guides, reference, and explanation as separate tracks.
The tracks are enumerable and each has a fixed rubric — workflow mode with
per-track schema validation.
```

*Expected v2 shape:* workflow fan-out over doc types, per-type rubric as assertions, style consistency checked by a reviewer stage.

**87 · Crisis communication**

```
design an agent team for crisis communication: fact gathering, stakeholder
mapping, message drafting, and legal/tone review. Messaging needs rapid
iteration with feedback between drafter and reviewer — persistent agents —
and every factual claim must cite a source, verified adversarially.
```

*Expected v2 shape:* hybrid — persistent drafting loop + workflow-based claim verification.

### 9. Operations & Process (harness-100 #89–95)

**90 · Hiring pipeline**

```
build a harness for a hiring pipeline: role definition, structured interview
design with BARS anchored rating scales, candidate evidence summaries, and
bias/compliance review. Stages are fixed per requisition — workflow — with
the compliance review verifying every scored criterion has evidence.
```

*Expected v2 shape:* workflow with rubric-schema outputs; compliance stage as verification gate.

**94 · Audit report**

```
design an agent team that produces audit reports: evidence collection across
systems, finding classification, remediation tracking, and final report
assembly. Evidence gathering fans out per system — workflow — and every
finding must pass adversarial verification with cited evidence.
```

*Expected v2 shape:* workflow fan-out per evidence source, adversarial verification on findings, structured remediation ledger.

### 10. Specialized Domains (harness-100 #96–100)

**96 · Real estate analyst** — v1 shipped `cap-rate-calculator` and `location-scoring` skills.

```
build a harness for real-estate investment analysis: property data intake,
location scoring, cap-rate/IRR modeling, and an investment memo. Calculations
are strictly repeatable — workflow with numeric schema validation — and the
final memo must cite every number it uses.
```

*Expected v2 shape:* workflow with hard schema assertions on financial outputs (v2 numeric verification instead of v1's prose-only review).

**98 · Academic paper**

```
design an agent team for supporting academic paper writing on IMRaD structure:
literature synthesis, methods drafting, results interpretation, and a
methodology critique. Literature review is a large enumerable fan-out —
workflow, loop-until-dry — while methods and interpretation need iterative
feedback — persistent agents.
```

*Expected v2 shape:* hybrid — workflow literature sweep with loop-until-dry and citation schemas; persistent Producer-Reviewer pair for methods.

## Appendix A: portability-aware example — architecture decision pipeline (DeepAgents target)

A worked example of the **two-phase workflow** (generate with harness → test in Claude Code → port with `deepagents-port`), reconstructing a real production DeepAgents pipeline: software-architecture decision support, where a team takes a project from requirements to a documented architecture decision.

The prompt is **contract-first**: it states the artifact sequence and ID-linkage rules up front, because those are the parts of the design that must survive the port unchanged (see the [mapping table's fidelity ladder](../packages/harness-en/skills/deepagents-port/references/mapping-table.md) — artifact contracts are the strongest-surviving tier). Field-level details are left to the factory.

```
claude "build a harness for software architecture decision-making: given a project
description and its functional requirements, the team identifies architectural
drivers, designs solution alternatives, evaluates them, and documents the final
architecture decision. The work is a fixed sequential pipeline of four stages —
(1) requirements & drivers analysis, (2) solution design, (3) alternative
evaluation, (4) architecture decision — and it must be portable to another
runtime, so: pass ALL data between steps as JSON files in _workspace/ named
{NN}_{step}.json, producing in order: requirements_analysis, quality_attributes,
drivers, pattern_candidates, pattern_compatibility, alternatives,
alternative_evaluation, trade_off_analysis, alternative_selection — then adr.md
and architecture_diagram.mmd as the final stage deliverables. Link cross-stage
entities by ID fields (e.g. source_requirement_ids), never by prose. Every step's
skill must document its input artifacts, its output JSON structure, and a
read-back verification rule; keep verification as explicit skill steps, not
messaging loops. Use one orchestrator plus one-shot sub-agents. Enforce scope
boundaries per stage: stage 1 is analysis only — no styles, patterns, tactics, or
technologies; stage 2 must explore multiple alternatives rather than committing
to one; stage 3 must ground every trade-off in named quality attributes; stage 4
must cite the selected alternative by ID in the ADR."
```

**Expected v2 shape:** four stage-shaped agents (or orchestrator phases) each running 2–3 skills in pinned order; file-based JSON data passing with documented structures per artifact; per-stage scope-boundary sections (the pattern's main defense against scope drift); intra-step read-back verification; minimal-pointer CLAUDE.md. Test in Claude Code by asserting every `_workspace/*.json` parses and required keys exist — the same assertions the DeepAgents port will run.

**How much schema to put in the prompt.** The prompt above fixes what must survive the port — pipeline shape, artifact filenames, ID-linkage rule, scope boundaries — and leaves field-level schemas to the factory, which derives them from the domain analysis. Two situations, two options:

- **Option 1 — new domain (this example as written):** say nothing about fields. Review and iterate on the generated JSON structures in the `SKILL.md`s before testing and porting; the prompt isn't your last chance to shape them. Dictating fields up front degrades the factory to a typist.
- **Option 2 — regenerating an existing pipeline (round-trip):** when a downstream consumer already pins the schemas (a frontend, a database, an API), the schemas are not a design choice but an external API. Add one clause making them hard constraints, and inline only the truly load-bearing fields:

```
# Option 2 clause — schemas are fixed by the existing application:
… the output schemas are fixed by the existing application — reproduce the JSON
structures documented in the current pipeline's skills exactly. Every entity
must carry source_requirement_ids referencing the requirements it derives from.
```

Rule of thumb: **the prompt fixes what must survive; the factory designs what can vary.** When an existing consumer exists, its schemas move from "can vary" to "must survive" — and only then do they belong in the prompt.

**Porting it:** after testing, invoke `deepagents-port` Phase B (see [packages/harness-en](../packages/harness-en); prerequisite: the official [langchain-skills](https://github.com/langchain-ai/langchain-skills) installed alongside it — `npx skills add langchain-ai/langchain-skills --skill '*' --yes`). The stages map 1:1 (each becomes `stage{N}-{name}/AGENTS.md` + its skills), the JSON contracts transfer nearly verbatim into each skill's Expected Output section, and the port emits a `port-manifest.md` with the Python wiring (`STAGES`, `STAGE_ARTIFACTS`, factory mounts). What changes: verification flattens from any multi-verifier fan-out to single-pass read-back + completion protocol, and model tiers collapse to one env-driven model with rationale preserved as comments.

## Appendix B: portability-aware example — ATAM architecture evaluation (two modes to compare)

A second worked example of the **two-phase workflow**, based on a validated research case: evaluating a software architecture with the **Architecture Tradeoff Analysis Method (ATAM)** — given an architecture report plus a utility tree of prioritized quality-attribute scenarios, the team identifies risks, sensitivity points, and tradeoff points, then recommends the critical scenarios the architecture fails to satisfy.

Source material (paper *"Towards Supporting Quality Architecture Evaluation with LLM Tools"*, ICSA 2026, + reproducibility kit): a stepwise 4-prompt sequence (risks → sensitivity → tradeoffs → scenario selection) validated against 8 anonymized architecture reports and an expert-refined **ground truth**, with a Likert 0–3 severity variant. Two findings from the paper shape this example directly:

- *LLMs "always return something"* — abundant findings without judgment. The harness answer: **evidence-grounded findings + adversarial verification + anchored severity** instead of raw Likert.
- The kit's own prompts ran phases in *different orders across iterations* — so phase order here is **soft**, not hard (see Phase-order flexibility below).

The prompt fixes what must survive: artifact sequence, scenario-ID linkage, evidence rule, verification intent, HITL gates. Field-level schemas (severity anchors, tradeoff tuple shape) are left to the factory.

### Methodology variants: scenario elicitation (upstream variations)

The paper's kit assumes the utility tree is given. A production evaluator often has only informal requirements and must elicit it first — and the ATAM literature offers two standard routes. Both are **front-end variants**: they prepend different elicitation stages to the same evaluation core (findings + selection), so pick one per run and name it in the prompt; don't let the factory mix them silently.

**Variant 1 — scenario-first:** brainstorm quality scenarios directly from informal requirements, then map each to ISO/IEC 25010 quality attributes.

```
claude "build a harness for ATAM-style architecture evaluation where the utility
tree is NOT given. Front end (variant: scenario-first): the team brainstorms
concrete quality-attribute scenarios directly from the informal requirements —
each scenario with stimulus, environment, response, and response measure — then
maps every scenario to its ISO/IEC 25010 quality characteristics (and
sub-characteristics) with the mapping rationale recorded per scenario. The mapped
scenarios become the prioritized utility tree. Back end: the standard evaluation
core — risks, sensitivity points (tradeoffs derived from sensitivity
combinations), adversarial verification of scenario-ID and component citations,
anchored severity, critical-scenario selection with architect gates. Same JSON
contract discipline: {NN}_{step}.json artifacts, ID linkage everywhere, evidence
rule for all findings. Two front-end gates: the architect reviews the raw
scenario list before ISO 25010 mapping, and confirms the prioritized utility
tree before evaluation starts."
```

*Expected v2 shape:* `0a-scenario-brainstorm` → `0b-iso25010-mapping` (scenario → characteristic/sub-characteristic + rationale) → the 6-skill core unchanged. The mapping step outputs the tree plus a `mappings` array linking each scenario ID to its 25010 nodes; downstream findings inherit the linkage, so tradeoff analysis can name the competing ISO characteristics (e.g. "performance efficiency vs. security"), not just scenario IDs. Gate placement gives the architect cheap early pruning.

**Variant 2 — attribute-first (standard ATAM):** elicit the implicit quality attributes from the informal requirements, then derive scenarios from those attributes.

```
claude "build a harness for ATAM-style architecture evaluation where the utility
tree is NOT given. Front end (variant: attribute-first, standard ATAM): the team
first identifies the quality attributes implicit in the informal requirements —
each with evidence quotes and rationale — organized per ISO/IEC 25010, then
derives concrete scenarios per attribute (stimulus/environment/response/measure)
that operationalize them. The derived scenarios become the prioritized utility
tree. Back end: identical to the scenario-first variant — risks, sensitivity,
tradeoffs, verification, anchored severity, selection, gates. Identical JSON
contracts and ID-linkage rules."
```

*Expected v2 shape:* `0a-attribute-elicitation` (attribute + evidence + rationale, 25010-aligned) → `0b-scenario-derivation` (attribute → N concrete scenarios, each carrying `derived_from_attribute`) → the same 6-skill core. Scenarios carry their parent attribute ID, so the final selection can report both "which scenarios are critical" and "which quality attributes are most at risk".

**Choosing between them:** variant 1 keeps scenarios concrete from the start (nothing abstract to misplace) but risks attribute blind spots — attributes nobody scenario-ized; mitigate with a completeness critic at mapping time ("which 25010 characteristics have zero scenarios, and is that justified?"). Variant 2 gives systematic coverage by construction (attributes enumerated first) but risks bookshelf scenarios — derived to fill the taxonomy rather than the system; mitigate with an evidence rule ("every derived scenario must trace to a requirement quote or documented stakeholder concern"). Both front ends compose with Option 1 and Option 2 orchestration below.

### Phase-order flexibility

The taxonomy has one **hard** dependency — *tradeoff points arise from combining sensitivity points* (a two-or-more relation; the kit's tradeoff prompt says so explicitly) — so sensitivity MUST precede tradeoffs. Everything else is **soft** and may be reordered or interleaved per run: risks can be identified before, after, or interleaved with sensitivity points (both consume only the architecture + scenarios); the architect's review gate can prune findings before or after tradeoff derivation; scenario selection always runs last (it consumes all three finding sets). Express this in the generated orchestrator as: `tradeoffs.depends_on = [sensitivity_points]` (hard), the rest declared orderable, and instruct the orchestrator to ask the user when a reordering would change findings materially.

### Option 1 — single-report evaluator (SARA-shaped)

The domain tool: one orchestrator, one run per architecture report. Structure maps to the DeepAgents stage pattern for later porting.

```
claude "build a harness for ATAM architecture evaluation. Input: an architecture
report (document) plus a utility tree of prioritized quality-attribute scenarios
referenced by ID (e.g. SC1.1). The team ingests the report into scenarios.json,
then identifies risks, sensitivity points, and tradeoff points, and finally
recommends the critical scenarios the architecture fails to satisfy, ordered most
to least critical. It must be portable to another runtime, so: pass ALL data
between steps as JSON files in _workspace/ named {NN}_{step}.json, producing in
order: scenarios, risks, sensitivity_points, tradeoffs, scenario_selection. Link
every finding to scenario IDs and architectural elements — a finding is only
valid if it cites the specific scenario and the specific architecture component
it derives from; never by prose alone. Phase order is flexible EXCEPT tradeoffs
must derive from sensitivity points (they combine two or more). Include an
adversarial verification step that checks each finding's scenario ID and
architectural element actually exist in the input, dropping unverifiable ones.
Severity is a schema field with anchored levels (e.g. critical/important/minor)
with one-line criteria each — not a bare 0–3 number. Two human gates: the
architect reviews and prunes the risk/sensitivity inventory before tradeoff
derivation, and confirms the final scenario selection. Every step's skill must
document its input artifacts, its output JSON structure, and a read-back
verification rule. Use one orchestrator plus one-shot sub-agents."
```

**Expected v2 shape:** an `atam-evaluator` orchestrator skill with 6 ordered skills — `0-ingest` (report + utility tree → `scenarios.json` with canonical IDs; the document input makes this step necessary, unlike pipelines with structured inputs), `1-risks`, `2-sensitivity`, `3-tradeoffs` (consumes `sensitivity_points.json`), `verify-findings` (adversarial: existence-check on every cited ID and component; majority-confirmed findings only), `4-selection` (consumes all three verified sets; outputs the ordered critical-scenario list with associated tradeoffs) — with the architect gates placed before `3-tradeoffs` and after `verify-findings`. File-based JSON passing, scenario-ID linkage everywhere, anchored severity per finding, scope boundaries per skill mirroring the kit's discipline (e.g. the risks skill must not propose solutions — only findings). Test against the paper's 8 anonymized reports + ground truth as ready-made Phase 6 fixtures.

### Option 2 — multi-report research mode (workflow fan-out)

The replication/benchmark wrapper: the same per-report pipeline, fanned out across a corpus of architecture reports, with a synthesis stage reproducing the paper's cross-group comparison tables.

```
claude "build a harness for ATAM architecture evaluation across a corpus of
architecture reports. Per report, run the same pipeline as the single-report
case: ingest scenarios, identify risks, sensitivity points, and tradeoffs (the
latter derived from sensitivity combinations), adversarially verify every
finding's scenario-ID and component citations, and select critical scenarios —
all as JSON artifacts linked by scenario ID. Then a synthesis stage aggregates
across reports: finding frequency by scenario ID and by architectural element,
consensus sensitivity points and tradeoffs appearing in multiple reports, and a
corpus-level summary of the most consistently problematic scenarios. The corpus
processing is deterministic and enumerable — use workflow orchestration with
per-report fan-out and a final fan-in. Keep the per-report pipeline portable
(identical JSON contracts) so it can run standalone as the single-report case.
Human gate at the synthesis: the architect reviews the cross-report aggregation
before it is finalized."
```

**Expected v2 shape:** workflow orchestration — `pipeline(reports, ingest, risks+sensitivity (parallel per report), tradeoffs, verify, select)` then a `synthesize` fan-in stage emitting `corpus_findings.json` (frequency tables, consensus sets) and a summary report; per-report outputs land in `_workspace/{report_id}/…` so the per-report contracts stay byte-identical to Option 1 (that's what makes A/B testing the two options meaningful: same artifacts, different orchestration). The architect gate sits at synthesis. Reuses the paper's ground truth as the eval corpus.

### Testing Option 1 vs. Option 2

The two options share per-report artifact contracts by construction, so compare them empirically on the same inputs: run both over the 8 anonymized reports, score per-report findings against the ground truth (precision/recall of risk and sensitivity identification, agreement of the selected-scenario lists), and measure cost/time. Expected trade-off: Option 1 wins on per-report depth and gate responsiveness (the architect prunes before tradeoffs, cutting hallucinated combinations); Option 2 wins on cross-report signal (consensus findings no single run surfaces) and cost efficiency at corpus scale. Decide per use case: practitioner tool → Option 1; research replication or benchmark → Option 2.

## Reusing the v1 collection alongside v2

The harness-100 artifacts are still usable as-is (copy any `ko/` or `en/` harness's `.claude/` into your project), with two caveats under the current runtime:

1. **They predate v2 conventions.** If you ask this repo's harness skill to *"check my harness"* in a project containing one, Phase 0 won't flag them as v1 artifacts (no `TeamCreate`/flag references — those were already gone), but you can still request a v2-style refactor: team loops → `Workflow` scripts where the flow is deterministic, lowercase `skill.md` → `SKILL.md`, model tiering with rationale.
2. **The English edition is machine-translated** from Korean and reads garbled in places ("security auditof vulnerability…"). The Korean edition is the source of truth; or regenerate the harness with v2 in English using the prompts above.

To link a copied harness into a project, follow the CLAUDE.md conventions in [manual-setup_EN.md](manual-setup_EN.md).
