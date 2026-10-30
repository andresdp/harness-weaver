# ADR: Modular Monolith Core with Client-Specific BFFs and Event-Driven Side Effects for the Campus Bike Rental System

## Status

Accepted

## Context

The campus/city bike rental system must let bikers register, verify and log in (S1-S4), discover nearby available
bikes (S5), register a bike by scanning or entering a code and be guided to it (S6), see the bike disappear from
the available list as soon as it is registered (S7), pay via third-party payment platforms (S8), receive expiry and
overtime handling (S9-S10), view and download usage history (S11), and let administrators see fleet status and
hourly/daily usage (S12-S13). The project description additionally requires ISO 27001-aligned security, GDPR/Privacy
Directive compliance, availability on web and mobile, a user-friendly experience, and attention to carbon footprint.

Two high-priority drivers dominate the decision: "Security of user, biometric and payment data" and "GDPR and
regional regulatory compliance", together with "Timely bike availability and location tracking" (S5-S7, S12), which
requires that a registered bike be removed from the available list "as soon as" it is registered and that concurrent
registration of the same bike be prevented. Medium-priority drivers for "Web and mobile client accessibility",
"Rental lifecycle and time-based charging", "Usage history and administrative usage reporting" and "Ease of use for
all riders" also shaped the comparison of alternatives, as did the low-priority "Low carbon footprint" driver.

Three alternatives were evaluated: A1 (layered modular monolith behind a security gateway), A2 (event-driven
microservices on the provided platform infrastructure) and A3 (modular monolith core with client-specific BFFs and
event-driven side effects). A decision was required because the alternatives differ materially on consistency
guarantees for S7, support for client-specific needs (navigation, scanning, biometric login) in S6/S3, isolation of
reporting load from rider-facing transactions (S11/S13), and operational footprint, and no single alternative
dominates on every quality attribute.

## Decision

Alternative **A3 — "Modular monolith core with client-specific BFFs and event-driven side effects"** is selected.

The architecture keeps the same capability modules as A1 (Identity, Fleet & Availability, Rentals, Payments,
Notifications, Reporting) in one layered, deployable core sharing a single transactional database with per-module
schemas. Two Backends for Frontend front the core instead of a thin API Gateway: a mobile BFF (device-local
biometric login, code scanning, navigation, nearby bikes) and a web BFF (rider web access, history downloads,
administrator fleet status and usage views, server-side token storage for browsers). The BFFs validate tokens
issued by the Identity module (Federated Identity) and act as the security boundary. Bike registration and its
removal from the available list stay in one local transaction in the core. Side effects — verification and expiry
notifications, usage records, and the administrator status refresh — are published as events through a message
broker using a transactional outbox. A Reporting module maintains CQRS read models for three-month usage history and
hourly/daily aggregated usage, kept off the transactional path. External payment and SMS/email providers are reached
through adapters wrapped by circuit breakers.

Main patterns: Modular Monolith, Layered Architecture, Backend for Frontend (BFF), Publish-Subscribe, CQRS,
Federated Identity, Adapter (Integration Gateway), Circuit Breaker.

## Rationale

A3 satisfies 12 of the 13 functional requirements (S1 is only partially satisfied, as in every alternative). It
preserves A1's local-transaction guarantee for bike registration and removal from availability, which satisfies S7
("as soon as") and guards against two bikers registering the same bike at once — a guarantee A2 can only claim under
the unverified assumption that a short eventually-consistent delay is acceptable (A2/S7 is `unclear`). A3 is the only
alternative whose mobile BFF explicitly covers code scanning and navigation to the selected bike (S6 `satisfied`
versus `partially_satisfied` in A1 and A2), and the only alternative with an architectural element addressing the
driver "Ease of use for all riders" (`partially_satisfied`, versus `unclear` in A1 and A2).

Moving notifications, administrator status refresh and reporting to events and CQRS read models removes A1's
dependency on the unverified assumption that reporting queries will not overload rider-facing operations (S2-G5),
and serves S11/S13 without contention on the transactional store. The client-specific BFFs are the only
architectural support in any alternative for tailoring the web and mobile experience (QA Portability and Usability
rated positive for A3, versus neutral/mixed for A1 and A2), and the web BFF keeps browser tokens server-side,
reducing token exposure. Payment and messaging providers remain isolated behind adapters with circuit breakers,
supporting multiple payment platforms (S8) and future payment methods.

These advantages come at a qualitative cost: two BFFs plus a message broker and transactional outbox add components
and implementation complexity relative to A1, edge security must be duplicated consistently across the BFFs, the
CQRS read models widen the GDPR retention and erasure scope, and the core still scales and fails as one unit. A1
remains a close second and would become preferable if the broker or the two BFFs prove architecturally unjustified.
This recommendation is qualitative, based on the stated alternatives; no measured performance, load or footprint
data was available to any alternative.

## Alternatives Considered

### A1 — Layered modular monolith behind a security gateway

A single deployable backend behind a thin API Gateway, with the same capability modules sharing one database, no
BFFs, and in-process/synchronous handling of side effects. It matches A3 on strong consistency for S7 and has the
smallest footprint of the three (the only alternative rated `satisfied` on the driver "Low carbon footprint"). It
was not selected because it identifies no element for navigation to the selected bike (S6 `partially_satisfied`),
runs reporting queries against the transactional database under the unverified assumption S2-G5 (so Reporting can
affect bike search and rental), and offers no client-specific support for web/mobile tailoring or ease of use
(driver "Ease of use for all riders" rated `unclear`). The margin over A1 is narrow and qualitative (S3-G11); A1
becomes preferable if the message broker or two BFFs prove unjustified (S2-G10, S2-G11).

### A2 — Event-driven microservices on the provided platform infrastructure

Independently deployable services per capability, coordinated through a saga, publish-subscribe events and CQRS,
using the container orchestration, service registry, broker and tracing the project description lists as available.
It offers the best fault isolation and independent scaling (QA Availability positive; driver "Service availability
to riders" `satisfied`) but was not selected because S7 is `unclear`: removal from the available list is eventually
consistent and depends on the unverified assumption S2-G7 that a short delay satisfies "as soon as". The high-priority
driver "Timely bike availability and location tracking" and the driver "Rental lifecycle and time-based charging"
are only `partially_satisfied` (saga compensations depend on the undecided timing of payment, S2-G15). A2 does not
satisfy "Low carbon footprint" (`not_satisfied`, the worst of the three), and its value depends on the organization's
unverified ability to operate the required infrastructure and on unverified scale needs (S2-G6, S2-G9).

## Consequences

### Positive Consequences

- Strong consistency for bike registration and its removal from the available list (S6/S7), through a local
  transaction, with protection against concurrent registration of the same bike.
- Explicit architectural support for navigation, code scanning and nearby bikes in the mobile BFF (S5, S6), and
  device-local biometric login (S3).
- Usage history and administrative usage reporting (S11, S13) are served from CQRS read models, isolated from
  rider-facing transactions, and able to hold aggregated rather than per-biker data for administrators.
- Reliable, decoupled delivery of verification and expiry notifications through a transactional outbox (S2, S9).
- Client-specific BFFs support the web and mobile accessibility driver and are the only architectural contribution
  to ease of use; browser tokens are kept server-side (S4).
- Payment and messaging providers are isolated behind adapters with circuit breakers, supporting multiple payment
  platforms and future payment methods (S8).

### Negative Consequences

- S1 is only `partially_satisfied`: the BFFs are the security boundary, but encryption from the BFFs to the database
  or at rest is not described; the scope of "end-to-end" encryption remains undetermined.
- Edge security (token validation, rate limiting) must be implemented consistently across two BFFs instead of one
  gateway.
- CQRS read models replicate usage data, so GDPR retention and erasure rules must also cover them; the applicable
  jurisdiction and retention policy are open.
- The core still scales and fails as one unit; "Service availability to riders" is only `partially_satisfied`, and
  no uptime target exists against which to judge this.
- Two BFFs plus a message broker and outbox add components and implementation complexity compared with A1; "Low
  carbon footprint" is only `partially_satisfied`.
- Side effects (notifications, administrator status refresh, read models) lag by the event propagation delay, which
  is a risk if the 30-second verification-code expiry reading of S2 applies; this delay is unmeasured.
- Unlocking the physical bike relies on an assumed adapter-wrapped lock or telematics interface; "Physical bike
  unlock by code" is only `partially_satisfied`.
- The justification for two BFFs depends on web and mobile flows actually differing enough; mobile access to usage
  history downloads is not described by the alternative.

## Traceability

| Decision element | Requirement IDs | Quality attributes | Drivers |
|---|---|---|---|
| Modular monolith core, single local transaction for registration | S6, S7 | Performance (timeliness), Availability | Timely bike availability and location tracking, Rental lifecycle and time-based charging |
| Mobile BFF (biometric login, code scanning, navigation, nearby bikes) | S3, S5, S6 | Usability, Portability, Security | Ease of use for all riders, Web and mobile client accessibility, Security of user, biometric and payment data |
| Web BFF (rider web access, history downloads, admin views, server-side tokens) | S4, S11, S12 | Portability, Security | Web and mobile client accessibility, User authentication and session management |
| Federated Identity + BFF token validation | S1, S3, S4 | Security | Security of user, biometric and payment data, User authentication and session management |
| Event-driven notifications via transactional outbox | S2, S9 | Interoperability, Availability | SMS and email message delivery, Rental lifecycle and time-based charging |
| CQRS read models in Reporting module | S11, S13 | Performance, Privacy and Regulatory Compliance | Usage history and administrative usage reporting, GDPR and regional regulatory compliance |
| Adapters with circuit breakers (Payments, Notifications) | S2, S8, S9 | Interoperability, Modifiability | Third-party payment platform integration, Evolution of payment methods and jurisdictions |
| Single deployable core (shared fate) | S5, S6, S8 | Availability, Sustainability | Service availability to riders, Low carbon footprint |

## Assumptions and Unresolved Gaps

This decision relies on, and leaves open, the following register entries (see `stage1_assumptions_gaps.json`,
`stage2_assumptions_gaps.json`, `stage3_assumptions_gaps.json` for full detail):

- **S1-G1** (open) — Scope of "end-to-end encryption ... between user device and app database" is unclear; A3 does
  not describe encryption beyond the BFFs. Carried forward as S3-G1.
- **S1-G16 / S1-G44 / S2-G4 / S3-G3** (open/relied_upon) — The unlock of the physical bike depends on an assumed
  adapter-wrapped lock or telematics interface that is not confirmed by the inputs.
- **S1-G43 / S2-G16 / S2-G17 / S3-G2** (open) — The regulatory jurisdiction (EU or China), identity-provider data
  residency, and retention/erasure policy for rental records and A3's CQRS read models are undetermined.
- **S2-G10 / S3-G4 / S3-G9** (open/relied_upon) — Whether web and mobile flows differ enough to justify two BFFs is
  an assumption A3 relies on; mobile access to usage-history downloads is not described.
- **S2-G11** (relied_upon) — A3 assumes a message broker is an acceptable additional runtime component.
- **S2-G12 / S3-G8** (relied_upon) — Usage history and hourly/daily usage read models may lag the transactional
  data by the event propagation delay; no load or fleet-size data exists to bound this.
- **S1-G18 / S1-G4 / S3-G7** (open) — The maximum acceptable delay implied by "as soon as" (S7) and the
  verification-code validity (30 seconds vs. 30 minutes, S2) are unresolved; they bound how much event-propagation
  delay A3's asynchronous side effects can tolerate.
- **S1-G50 / S2-G2 / S3-G5** (open) — No uptime target exists against which to judge the core's shared-fate
  availability.
- **S1-G52 / S3-G6** (open) — No carbon-footprint metric exists; A3's footprint relative to A1 is a qualitative
  judgement only.
- **S3-G10** (relied_upon) — A3/S13 is rated `satisfied` only under the Stage 1 interpretation that administrators
  obtain hourly and daily usage information (the source requirement text is incomplete).
- **S3-G11** (noted) — The margin of A3 over A1 is narrow and qualitative; every evaluation in Stages 2-3 lacked
  measured evidence.
