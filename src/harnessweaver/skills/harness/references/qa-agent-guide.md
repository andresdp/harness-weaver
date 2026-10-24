# QA Agent Design Guide

Guidance to consult when including a QA agent in a build harness. Based on bugs actually found in real projects and their root causes, it explains how to find the defects a QA agent tends to miss.

---

## Table of contents

1. [Patterns of defects QA agents miss](#1-patterns-of-defects-qa-agents-miss)
2. [Integration coherence verification](#2-integration-coherence-verification)
3. [QA agent design principles](#3-qa-agent-design-principles)
4. [QA as a workflow (v2)](#4-qa-as-a-workflow-v2)
5. [Verification checklist template](#5-verification-checklist-template)
6. [QA agent definition template](#6-qa-agent-definition-template)

---

## 1. Patterns of defects QA agents miss

### 1-1. Contract mismatches at component boundaries (boundary mismatch)

The most frequent defect. Each component, viewed on its own, is implemented correctly, but at the connection point they follow different contracts.

| Connection point | Mismatch example | Why it gets missed |
|--------|-----------|-----------|
| API response → frontend hook | The API returns `{ projects: [...] }` but the hook expects `Project[]`. | Each component is verified in isolation and never compared with each other. |
| API response field names → type definitions | The API uses `thumbnailUrl` (camelCase) while the type uses `thumbnail_url` (snake_case). | When types are asserted via generics, the compiler cannot detect it. |
| File paths → link `href` | The page lives at `/dashboard/create` but the link points to `/create`. | The file structure and the `href` are never cross-checked. |
| State transition map → actual `status` updates | The map defines transitions, but the code that changes the state is missing. | Only the map's existence is checked; the actual update code is never traced. |
| API endpoint → frontend hook | The API exists, but no hook calls it. | The API list and the hook list are never matched one-to-one. |
| Immediate response → async processing result | The API returns `{ status }` immediately, but the frontend accesses the final result field. | Immediate and final responses are not distinguished; only types are checked. |

### 1-2. Why static code review alone cannot find them

- **Limits of generic types**: With something like `fetchJson<Project[]>()`, the code compiles even when the actual response is `{ projects: [...] }`.
- **Why a successful build does not guarantee correct behavior**: Code using type assertions, `any`, or generics can pass the build yet fail at runtime.
- **An API's existence and its response contract are different verification targets**: Checking "does the API exist?" and checking "does the API response match what the caller expects?" are entirely different jobs.

<a id="2-integration-coherence-verification"></a>

## 2. Integration coherence verification

A QA agent must include verification that **cross-checks components against each other**. The examples below assume Next.js, but the principle applies to any tech stack. Open the producer code and the consumer code together and compare the contracts on both sides.

### 2-1. Cross-check API responses against frontend hook types

```
1. Extract the response structure at the API route's serialization point (e.g., NextResponse.json()).
2. Check the type the corresponding hook or client expects (e.g., the T of fetchJson<T>).
3. Compare the response structure with T. If the API returns { data: [...] }, also confirm the hook unwraps .data.
```

Check in particular for responses wrapped in pagination being misread as arrays, missing conversions between snake_case and camelCase, and differing structures between the immediate response (202) and the final response.

### 2-2. Cross-check file paths against link and router paths

```
1. Extract URL patterns from the routing file structure. Drop (group) segments and treat [param] as a dynamic segment.
2. Collect every href=, router.push(, and redirect( value in the code.
3. Confirm each link matches a path that actually exists.
```

### 2-3. Trace that every state transition is implemented

```
1. Extract the list of allowed transitions from the state transition map.
2. Search for all code that updates status.
3. Confirm every transition occurring in the code is defined in the map. There must be no disallowed transitions.
4. Find transitions defined in the map but never exercised by the code. There must be no unused transitions.
5. Check especially whether the step from intermediate states to the final state is missing.
```

### 2-4. Match API endpoints against frontend hooks one-to-one

```
1. Extract the endpoint list per HTTP method.
2. Extract the client's fetch call URLs.
3. For each uncalled endpoint, judge whether it is an admin API called directly by the client or whether the calling code is missing.
```

## 3. QA agent design principles

### 3-1. Choose an agent type with access to all tools

If the QA agent is the `Explore` type, it can only read files. To do QA properly, it must be able to find patterns with `Grep`, run scripts to cross-check results automatically, and, when needed, fix code. Choose `general-purpose` or a custom type with access to all tools, and state the "verify → report → request fixes" procedure in the agent definition.

### 3-2. Put cross-check results in the checklist, not existence checks

| Simple checklist | Cross-check-driven checklist |
|---------------|---------------|
| Does the API endpoint exist? | Does the API response structure match the corresponding hook's type? |
| Is the state transition map defined? | Does every code path that updates `status` match the transition map? |
| Does the page file exist? | Does every link in the code point to a page that actually exists? |
| Is strict mode used? | Is there anywhere type safety is bypassed with generic type assertions? |

### 3-3. Read both sides of a connection together

To find bugs born at connection points, reading only one side is not enough. Read the API route together with its corresponding hook, the state transition map together with the actual update code, and the file structure together with the link paths. State this principle explicitly in the agent definition too.

### 3-4. Run QA each time a module is completed, not after all modules are built

If QA runs only after the entire implementation is finished, bugs pile up, fixing costs grow, and contract mismatches introduced early spread into subsequent modules. We recommend **incremental QA**: every time a single API endpoint is completed, immediately cross-check that API against its corresponding hook.

<a id="4-qa-as-a-workflow-v2"></a>

## 4. QA as a workflow (v2)

If the connection points to verify can be listed, the QA process can also be organized as a workflow.

```javascript
// Inspect each boundary separately → re-verify each finding from the opposite viewpoint
const FINDINGS = { type: 'object', required: ['findings'], properties: {
  findings: { type: 'array', items: { type: 'object',
    required: ['title', 'file', 'evidence'], properties: {
      title: { type: 'string' }, file: { type: 'string' }, evidence: { type: 'string' } } } } } }
const VERDICT = { type: 'object', required: ['status', 'reason'], properties: {
  status: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] },
  reason: { type: 'string' } } }
const boundaries = args.boundaries  // extracted by a preliminary survey: [{api: '...', consumer: '...'}, ...]
const found = await pipeline(
  boundaries,
  b => agent(`Read both sides together and find contract mismatches: ${b.api} ↔ ${b.consumer}`,
    { agentType: 'qa-inspector', phase: 'Inspect', schema: FINDINGS }),
  r => parallel((r?.findings ?? []).map(f => () =>
    agent(`Verify from the opposite viewpoint whether this mismatch actually causes a runtime error: ${JSON.stringify(f)}`,
      { phase: 'Re-verify', schema: VERDICT }).then(verdict => ({ ...f, verdict }))))
)
const confirmed = found.flat().filter(Boolean)
  .filter(f => f.verdict?.status === 'confirmed')
return { confirmed }
```

By re-verifying each finding from the opposite viewpoint and keeping only the `confirmed` verdicts, you filter out findings that look plausible but are not actually problems. The findings in the final QA report therefore become more trustworthy.

## 5. Verification checklist template

Include the integration coherence checklist below in the definition of a QA agent that inspects web applications.

```markdown
### Integration coherence verification (web app)

#### API and frontend connections
- [ ] Confirm every API route's response structure matches the corresponding hook's generic type.
- [ ] Confirm hooks unwrap the actual data from object-wrapped responses ({ items: [...] }).
- [ ] Confirm conversions between snake_case and camelCase are applied consistently.
- [ ] Confirm the frontend distinguishes the immediate response (202) from the final response structure.
- [ ] Confirm every API endpoint has a corresponding frontend hook that actually calls it.

#### Routing coherence
- [ ] Confirm every href/router.push value in the code matches an actual page file path.
- [ ] Validate paths accounting for the fact that (group) route groups do not appear in the URL.
- [ ] Confirm dynamic segments ([id]) receive the correct parameter values.

#### State machine coherence
- [ ] Confirm every defined state transition is exercised by the code (no unused transitions).
- [ ] Confirm every status update in the code is defined in the transition map (no disallowed transitions).
- [ ] Confirm the step from intermediate states to the final state is not missing.
- [ ] Confirm that X in frontend state branches (if status === "X") is a state that can actually be reached.

#### Data flow coherence
- [ ] Confirm the mapping between DB schema field names and API response field names is consistent.
- [ ] Confirm frontend type definitions match the API response field names.
- [ ] Confirm both sides handle null/undefined values of optional fields consistently.
```

## 6. QA agent definition template

```markdown
---
name: qa-inspector
description: "A QA agent that verifies spec compliance, integration coherence, and design quality."
---

# QA Agent

## Core role
Confirm the implementation matches the spec and verify **integration coherence between modules**.

## Verification priorities
1. **Integration coherence** (highest) — contract mismatches at connection points are a leading cause of runtime errors.
2. **Functional spec compliance** — check APIs, state machines, and data models.
3. **Design quality** — check colors, fonts, and responsive behavior.
4. **Code quality** — check for unused code and naming conventions.

## Verification method: read both sides of a connection together
| Verification target | Producer | Consumer |
|----------|-------|-------|
| API response structure | The response serialization point | The type the client expects |
| Routing | The routing file structure | href and router.push values |
| State transitions | The transition map | The status update code |
| DB → API → UI | The DB table column names | API response fields → type definitions |

## Reporting and fix-request procedure
- When you find a problem, immediately request a specific fix from the responsible agent (file:line number + how to fix).
- If the problem occurred at a connection point, notify both responsible agents.
- Send the leader a verification report separating passed, failed, and unverified items.
```

---

## Real cases: bugs found and their causes

| Bug | Connection point | Cause |
|------|----------|------|
| `projects?.filter is not a function` | API → hook | The API returns `{projects:[]}` but the hook expects an array. |
| Every link on the dashboard returns 404 | File path → `href` | The `/dashboard/` prefix is missing. |
| Thumbnail images do not appear | API → UI component | `thumbnailUrl` and `thumbnail_url` do not match. |
| The selected value is not saved | API → hook | The API exists but there is no corresponding hook. |
| The creation page stays in a waiting state forever | State transition → code | The code that moves to the final state is missing. |
| Crash when accessing `data.failedIndices` | Immediate response → frontend | The frontend accesses background processing results on the immediate response. |
| Opening the detail page after completion returns 404 | File path → `href` | The route prefix does not match. |
