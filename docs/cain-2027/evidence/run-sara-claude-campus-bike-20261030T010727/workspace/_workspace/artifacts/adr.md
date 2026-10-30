# ADR: Layered Modular Monolith with a Shared Transactional Database for the Campus Bike Rental System

## Status

Accepted

## Context

The campus/city bike rental system must let bikers register accounts, authenticate, locate and register (unlock)
bikes, run time-boxed rentals with expiry notification and overtime charging, pay through multiple third-party
payment platforms, and let administrators see fleet-wide status and usage reporting, all while meeting GDPR and
ISO 27001-aligned security expectations (drivers "Security of user and payment data" and "GDPR and regional
regulatory compliance", both high priority).

Two architectural concerns dominate the decision. First, bike availability and rental state must stay correct: a
bike must disappear from the available list as soon as it is registered (S7), and administrators must see state
consistent with what bikers see (S12, driver "Consistent bike and rental state"). Second, personal, payment and
usage data must be protected and governed under a single compliance regime (S1, S8, S11, driver "GDPR and regional
regulatory compliance"). A secondary conflict exists between the 15-minute inactivity logout (S4) and the need to
notify bikers of rental expiry and overtime independent of their session (S9, driver "Rental lifecycle timing").
The inputs state no load, scalability, uptime or independent-release requirements (S1-G67) that would call for
distributed or eventually-consistent designs, and a "Changeability of payment options and regulations" driver
(medium priority) exists but without a stated rate of change.

Three alternatives were evaluated in Stage 3: A1, a layered modular monolith with a shared transactional database;
A2, the same monolith extended with an API gateway, domain events and CQRS read models; and A3, event-driven
microservices with sagas, a gateway and client-specific backends (backends for frontend). The decision below
documents the already-made selection; it does not re-run that evaluation.

## Decision

The selected architecture is **Alternative A1: Layered modular monolith with a shared transactional
database**. The system is a single deployable back end serving the web app, the mobile app and the administrator
console. It is organized into modules by capability — identity and session, bike fleet, rental, payment,
notification, and usage and reporting — each internally layered (API, application, data access). All modules share
one transactional database with a schema per module, so bike registration, availability removal and rental
creation execute in one local ACID transaction. Modules call each other synchronously through public interfaces.
Dependencies on external systems (payment platforms, SMS/email providers, the bike/lock interface, persistence)
sit behind ports with replaceable adapters. Rental expiry notification and overtime detection run as time-based
jobs inside the rental module, independent of user sessions. Clients authenticate with email/password or biometric
credentials and receive an access token carrying identity and role; logout and the 15-minute inactivity timeout are
enforced on the server.

Main patterns: Modular Monolith, Layered Architecture, Ports and Adapters, Shared Database, Access Token.

## Rationale

A1 satisfies the most functional requirements of the three alternatives (10 of 13, against 9 for A2 and 8 for A3;
`alternative_evaluation.json`). It is the only alternative rated `satisfied` (not `partially_satisfied`) on S7,
because registration, availability removal and rental creation happen in one local transaction, and on the drivers
"Consistent bike and rental state" and "Bike location and availability tracking", because biker and administrator
views read the same transactional state with no read-model lag. A2 and A3 only partially satisfy these, since their
availability views are eventually consistent (A2 read models; A3 saga-based fleet updates).

A1 is also the only alternative rated `satisfied` on the "GDPR and regional regulatory compliance" driver: personal,
payment and usage data remain in one store, with no replication into read models or event records, so retention,
erasure, encryption at rest and access control are applied in one place. A2 replicates personal data into read
models and event records (GDPR driver only `partially_satisfied`), and A3 must coordinate erasure and retention
across several service-private stores.

Time-based jobs inside the rental module resolve the S4/S9 tension architecturally: expiry notification and
overtime detection run independently of the 15-minute session, satisfying S9 and the "Rental lifecycle timing"
driver in all three alternatives, but A1 achieves it with the least additional infrastructure. Ports and adapters
isolate payment platform and SMS/email provider variety (driver "Third-party payment platform integration",
satisfied; quality attribute Interoperability, positive).

The trade-off analysis frames the choice as trading independent deployability and fault isolation for transactional
consistency and low operational complexity (`trade_off_analysis.json`, A1 `arch_tradeoff`). A2's read-model
separation and A3's independent deployability and client-tailored backends would be preferable if measured
reporting load, stated freshness tolerances, or a confirmed need for independent release of payment/regional logic
existed, but no such evidence is present in the inputs (S1-G67, S2-G2, S2-G4, S2-G6).

## Alternatives Considered

### A2 — Event-driven modular monolith with API gateway and CQRS read models

A2 keeps A1's transactional core for atomic operations but adds a message broker, domain events and CQRS read
models for availability, fleet status, usage history and usage aggregation, plus an API gateway for edge security.
It was not selected because its displayed availability and fleet status are eventually consistent, so S7 and the
consistency/availability-tracking drivers are only `partially_satisfied`; it replicates personal data into read
models and event records, so the GDPR driver is only `partially_satisfied`; and it still deploys as a single unit,
gaining no changeability advantage over A1 despite its added broker, gateway and event infrastructure. It would
become preferable if measured reporting load or a stated freshness tolerance showed A1's shared-database reporting
inadequate, but no such evidence exists (S1-G67, S2-G2, S2-G4).

### A3 — Event-driven microservices with API gateway, backends for frontend and sagas

A3 splits the back end into independently deployable services with private data stores, sagas for cross-service
rental-start/rental-end transactions, a gateway, and client-specific backends for mobile, web and administrator
clients. It is the only alternative that fully satisfies the "Changeability of payment options and regulations"
driver and explicitly handles device-specific client differences through BFFs. It was not selected because it has
the fewest requirements rated satisfied of the three (S1, S3, S4, S6 and S7 only `partially_satisfied`); its
consistency depends on sagas whose compensation behaviour for failed unlock or payment is unstated (S2-G10); it
must coordinate GDPR erasure across several service-private stores; and it carries the highest operational and
development complexity (orchestration, service discovery, distributed tracing, saga compensation) with no stated
scalability, load, team-size or release-independence need to justify it (S1-G67, S2-G6, S2-G8).

## Consequences

### Positive Consequences

- Strong, immediate consistency of bike availability and rental state through local ACID transactions; a
  registered bike cannot be shown as available or registered twice (S7).
- Biker and administrator views read the same authoritative state with no read-model lag (S5, S12).
- A single store for personal, payment and usage data simplifies GDPR retention, erasure, encryption at rest and
  access control, and avoids replicating sensitive data into secondary stores.
- Rental expiry notification and overtime detection run independently of the 15-minute session timeout (S4/S9).
- Replaceable adapters isolate the variety of payment platforms, SMS/email providers and the bike/lock interface,
  supporting change without touching core module logic.
- Fewest runtime components and lowest operational complexity among the three alternatives (qualitative).

### Negative Consequences

- Every change, including a single payment adapter or regional compliance logic, requires redeploying the whole
  application; the "Changeability of payment options and regulations" driver is only `partially_satisfied`, and
  the decision relies on the assumption that independent release is not required (S2-G3).
- Reporting queries (S12, S13) share the transactional database with rental operations; that this load is
  acceptable is an unmeasured assumption (S2-G2).
- Fault isolation is weak: a failure or slowness in one module (for example reporting or notification) can affect
  rental operations through synchronous in-process calls.
- No edge security component exists, and protection in transit along the device-to-database path is not specified
  (S1 and the Security driver remain `partially_satisfied`).
- Biometric matching and flushing (S3), navigation to the bike (S6), and the physical unlock mechanism and its
  failure handling remain unresolved; this limitation is common to all three alternatives.
- The external payment step occurs outside the local transaction and relies on adapter-level retry and
  reconciliation, whose adequacy depends on unstated payment timing (S2-G12).
- Scaling a single deployable is assumed sufficient, but no load, user, fleet-size or uptime targets exist
  (S1-G67, S2-G1).
- Module boundaries in code and database rely on discipline and tooling and may erode over time without
  governance.

## Traceability

| Decision element | Requirement IDs | Quality attributes | Drivers |
|---|---|---|---|
| Local ACID transaction for registration, availability removal, rental creation | S6, S7 | Reliability (correctness of rental and bike state) | Consistent bike and rental state; Bike location and availability tracking; Bike registration and unlocking |
| Single shared data store for personal/payment/usage data | S1, S8, S11 | Privacy and Regulatory Compliance; Security | GDPR and regional regulatory compliance; Security of user and payment data |
| Ports and adapters for payment, SMS/email, bike/lock | S2, S8 | Interoperability | Third-party payment platform integration; External SMS and email delivery |
| Time-based jobs for expiry/overtime, independent of session | S4, S9, S10 | Performance (timeliness); Reliability | Rental lifecycle timing; Biker authentication and session management |
| Single deployable back end for web/mobile/administrator | S3, S5, S12 | Portability (multi-platform access) | Web and mobile client access |
| Module boundaries without independent deployment | S8 | Modifiability | Changeability of payment options and regulations |
| Usage and reporting module reading shared database | S11, S12, S13 | Performance (timeliness) (mixed) | Usage history and administrative reporting |

## Assumptions and Unresolved Gaps

This decision relies on, and leaves open, the following register entries (see
`stage1_assumptions_gaps.json`, `stage2_assumptions_gaps.json`, `stage3_assumptions_gaps.json` for full detail):

- **S2-G1, S2-G3, S3-G7** (relied upon): the expected number of users, fleet size and concurrent rentals can be
  served by scaling a single deployable application, and no part of the system needs independent release
  schedules. No load or scale targets exist to confirm this (S1-G67).
- **S2-G2, S3-G7** (relied upon): reporting queries (S12, S13) can run against the transactional database without
  unacceptable impact on rental operations; this is unmeasured.
- **S2-G12, S3-G9** (relied upon): the external payment step, handled outside the local transaction via
  adapter-level retry and reconciliation, works correctly; this depends on unstated payment timing and platform
  capabilities (S1-G27, S1-G28, S1-G30).
- **S3-G1 / S1-G1** (open): whether "end-to-end encryption between user device and app database" requires
  protection on every internal hop or only transport encryption plus encryption at rest is unresolved; A1 does not
  describe in-transit protection beyond the device-to-backend hop.
- **S3-G2 / S1-G9, S1-G10, S1-G11** (open): where biometric thumb-impression matching occurs, how it is flushed,
  and whether biometric login is required on web clients remain unresolved for all alternatives, including A1.
- **S3-G3 / S1-G22** (open): navigation help to a selected bike (S6) is not described by any alternative.
- **S3-G4 / S1-G23, S1-G55** (open): the bike/lock communication mechanism and the required behaviour when a
  physical unlock fails, after registration has already committed, are unresolved.
- **S3-G5 / S2-G3, S2-G6** (relied upon): the decision assumes payment-platform and regional-compliance changes do
  not need to be released independently of the rest of the application; if this changes, A1's whole-redeploy
  limitation becomes significant.
- **S3-G6 / S1-G65** (open): the meaning and measurement of the "Sustainable mobility goal" driver (software
  resource efficiency vs. promoting cycling) is unresolved; A1's claimed advantage here is weak and qualitative.
- **S3-G8 / S1-G67** (open): no uptime target exists, so the severity of A1's weak fault isolation (a reporting or
  notification fault affecting rentals) cannot be assessed against a stated requirement.
- **S1-G66** (open): the applicable jurisdiction (EU or China) for GDPR/regional compliance is not stated, which
  affects what the single-store compliance approach must actually implement.
