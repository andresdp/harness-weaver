# QA Agent Design Guide

Guidance to consult when including a QA agent in a build harness. Based on bugs found in real projects and their causes, it explains how to find defects that QA agents tend to miss.

---

## Contents

1. [Patterns of defects QA agents miss](#1-patterns-of-defects-qa-agents-miss)
2. [Integration coherence verification](#2-integration-coherence-verification)
3. [QA agent design principles](#3-qa-agent-design-principles)
4. [QA performed with a workflow (v2)](#4-qa-performed-with-a-workflow-v2)
5. [Verification checklist template](#5-verification-checklist-template)
6. [QA agent definition template](#6-qa-agent-definition-template)

---

## 1. Patterns of defects QA agents miss

### 1-1. Contract mismatches at component boundaries (Boundary Mismatch)

This is the most frequent defect. Looked at separately, both components are implemented correctly, but they follow different contracts at the point where they connect.

| Connection point | Mismatch example | Why it is missed |
|--------|-----------|-----------|
| API response → frontend hook | The API returns `{ projects: [...] }` but the hook expects `Project[]`. | Each component is verified separately and they are not compared with each other. |
| API response field names → type definitions | The API uses `thumbnailUrl` (camelCase), the type uses `thumbnail_url` (snake_case). | When the type is asserted with a generic, the compiler doesn't detect it. |
| File path → link `href` | The page is at `/dashboard/create`, but the link points to `/create`. | The file structure and `href` are not compared with each other. |
| State transition map → actual `status` updates | The transition is defined in the map, but the code lacks the handling that changes the state. | Only whether the map exists is checked; the actual update code is not traced. |
| API endpoint → frontend hook | The API exists, but there is no hook that calls it. | The API list and hook list are not cross-checked one to one. |
| Immediate response → asynchronous processing result | The API immediately returns `{ status }`, but the frontend accesses the final result fields. | Only types are checked, without distinguishing the immediate response from the final response. |

### 1-2. Why static code review alone has difficulty finding them

- **Limits of generic types**: written as `fetchJson<Project[]>()`, it compiles even if the actual response is `{ projects: [...] }`.
- **Why a successful build cannot guarantee correct behavior**: code that uses type assertions, `any`, or generics can build successfully and still fail at runtime.
- **Whether an API exists and its response contract are different verification targets**: checking "does the API exist?" and checking "does the API response match what the calling side expects?" are entirely different things.

<a id="2-integration-coherence-verification"></a>

## 2. Integration coherence verification (Integration Coherence Verification)

A QA agent must always include **verification that cross-checks components against each other**. The examples below are based on Next.js, but the principle applies to any tech stack. Open the producer code and the consumer code together and compare the contracts on both sides.

### 2-1. Cross-checking API responses against frontend hook types

```
1. Extract the response structure from the API route's response serialization point (NextResponse.json(), etc.).
2. Check the type expected by the corresponding hook or client (the T of fetchJson<T>, etc.).
3. Compare the response structure with T. If the API returns { data: [...] }, check even whether the hook takes out .data.
```

In particular, check cases where a paginated wrapped response is mistakenly received as an array, where conversion between snake_case and camelCase is missing, and where the immediate response (202) and the final response have different structures.

### 2-2. Cross-checking file paths against link and router paths

```
1. Extract URL patterns from the routing file structure. Remove (group), and treat [param] as a dynamic segment.
2. Collect all href=, router.push(, and redirect( values in the code.
3. Check that each link matches a path that actually exists.
```

### 2-3. Tracing whether state transitions are fully implemented

```
1. Extract the list of allowed transitions from the state transition map.
2. Search for all code that updates status.
3. Check that the transitions occurring in the code are defined in the map. There must be no disallowed transitions.
4. Find transitions that are in the map but never executed in the code. There must be no unused transitions.
5. In particular, check whether the handling that moves from an intermediate state to the final state is missing.
```

### 2-4. Cross-checking API endpoints and frontend hooks one to one

```
1. Extract the list of endpoints per HTTP method.
2. Extract the list of the client's fetch call URLs.
3. For endpoints that aren't called, judge whether they are admin APIs the client doesn't call directly, or whether the calling code is missing.
```

## 3. QA agent design principles

### 3-1. Choose an agent type that can use all tools

If the QA agent is of type `Explore`, it can only read files. To do QA properly, it must be able to find patterns with `Grep`, run scripts to cross-check results automatically, and modify code if needed. Choose `general-purpose` or a custom type that can use all tools, and specify the "verify → report → request fixes" procedure in the agent definition.

### 3-2. Put cross-check results, not existence, in the checklist

| Simple checklist | Cross-check-centered checklist |
|---------------|---------------|
| Does the API endpoint exist? | Does the API response structure match the type of the corresponding hook? |
| Is the state transition map defined? | Does all code that updates `status` match the transition map? |
| Does the page file exist? | Do all links in the code point to pages that actually exist? |
| Is strict mode used? | Is there no place where type safety is bypassed with a generic type assertion? |

### 3-3. Read the code on both connected sides together

To find bugs that arise at connection points, reading code on only one side is not enough. Read the API route and the corresponding hook, the state transition map and the actual update code, and the file structure and link paths together, respectively. State this principle clearly in the agent definition as well.

### 3-4. Run QA each time a module is completed, not after all modules are built

If QA runs only after the whole implementation is finished, bugs pile up and fixing costs rise, and contract mismatches that arose early spread to subsequent modules. **Incremental QA** is recommended: each time one API endpoint is completed, immediately cross-check that API against the corresponding hook.

<a id="4-qa-performed-with-a-workflow-v2"></a>

## 4. QA performed with a workflow (v2)

If the connection points to verify can be made into a list, the QA process can also be composed as a workflow.

```javascript
// Inspect connection points in divided batches → re-verify each found item from the opposite perspective
const FINDINGS = { type: 'object', required: ['findings'], properties: {
  findings: { type: 'array', items: { type: 'object',
    required: ['title', 'file', 'evidence'], properties: {
      title: { type: 'string' }, file: { type: 'string' }, evidence: { type: 'string' } } } } } }
const VERDICT = { type: 'object', required: ['status', 'reason'], properties: {
  status: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] },
  reason: { type: 'string' } } }
const boundaries = args.boundaries  // extracted by pre-investigation: [{api: '...', consumer: '...'}, ...]
const found = await pipeline(
  boundaries,
  b => agent(`Read both sides together and find contract mismatches: ${b.api} ↔ ${b.consumer}`,
    { agentType: 'qa-inspector', phase: 'inspect', schema: FINDINGS }),
  r => parallel((r?.findings ?? []).map(f => () =>
    agent(`Verify from the opposite perspective whether this mismatch causes an actual runtime error: ${JSON.stringify(f)}`,
      { phase: 're-verify', schema: VERDICT }).then(verdict => ({ ...f, verdict }))))
)
const confirmed = found.flat().filter(Boolean)
  .filter(f => f.verdict?.status === 'confirmed')
return { confirmed }
```

Re-verifying found items from the opposite perspective and keeping only `confirmed` verdicts filters out findings that look plausible but are not actually problems. The findings in the final QA report can therefore be trusted more.

## 5. Verification checklist template

Include the integration coherence checklist below in the definition of a QA agent that inspects web applications.

```markdown
### Integration coherence verification (web app)

#### API and frontend connection
- [ ] Check that the response structure of every API route matches the generic type of the corresponding hook.
- [ ] Check that hooks take the actual data values out of responses wrapped in an object ({ items: [...] }).
- [ ] Check that conversion between snake_case and camelCase is applied consistently.
- [ ] Check that the frontend distinguishes the structures of the immediate response (202) and the final response.
- [ ] Check that every API endpoint has a corresponding frontend hook and that it is actually called.

#### Routing coherence
- [ ] Check that every href/router.push value in the code matches an actual page file path.
- [ ] Verify paths reflecting that (group) used in route groups is dropped from the URL.
- [ ] Check that dynamic segments ([id]) receive the correct parameter values.

#### State machine coherence
- [ ] Check that every defined state transition is executed in the code (there must be no unused transitions).
- [ ] Check that every status update in the code is defined in the transition map (there must be no disallowed transitions).
- [ ] Check that the handling that moves from an intermediate state to the final state is not missing.
- [ ] Check that the X in the frontend's state-based branches (if status === "X") is a state that can actually be reached.

#### Data flow coherence
- [ ] Check that the correspondence between DB schema field names and API response field names is consistent.
- [ ] Check that the field names of the frontend type definitions and the API response match.
- [ ] Check that both sides handle null/undefined values of optional fields consistently.
```

## 6. QA agent definition template

```markdown
---
name: qa-inspector
description: "A QA agent that verifies specification compliance, integration coherence, and design quality."
---

# QA Agent

## Main role
Check that the implementation follows the specification and verify **integration coherence between modules**.

## Verification priorities
1. **Integration coherence** (highest) — contract mismatches at connection points are the main cause of runtime errors.
2. **Functional specification compliance** — check the API, state machine, and data model.
3. **Design quality** — check colors, fonts, and responsive behavior.
4. **Code quality** — check unused code and naming conventions.

## Verification method: read the code on both connected sides together
| Verification target | Producer | Consumer |
|----------|-------|-------|
| API response structure | Response serialization point | Type the client expects |
| Routing | Routing file structure | href, router.push values |
| State transitions | Transition map | status update code |
| DB → API → UI | DB table column names | API response fields → type definitions |

## Reporting and fix-request procedure
- When a problem is found, immediately request concrete fixes from the responsible agent (file:line number + how to fix).
- If a problem arose at a connection point, notify the responsible agents on both sides.
- Send the leader a verification report that distinguishes passed, failed, and unverified items.
```

---

## Real cases: bugs found and their causes

| Bug | Connection point | Cause |
|------|----------|------|
| `projects?.filter is not a function` | API → hook | The API returns `{projects:[]}` but the hook expects an array. |
| 404 on every dashboard link | File path → `href` | The `/dashboard/` prefix is missing. |
| Thumbnail images don't show | API → UI component | `thumbnailUrl` and `thumbnail_url` don't match. |
| Selected values aren't saved | API → hook | The API exists but there is no corresponding hook. |
| The creation page stays in a waiting state | State transition → code | The code that changes to the final state is missing. |
| Crash when accessing `data.failedIndices` | Immediate response → frontend | The frontend accesses background processing results from the immediate response. |
| 404 when opening the detail page after completion | File path → `href` | The route prefix doesn't match. |
