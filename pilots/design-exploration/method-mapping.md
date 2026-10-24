# ADD method mapping for the design-exploration profile

## Source and scope

The declared method source is *Better Together: An LLM-assisted Approach to Designing Software Architectures using Attribute-Driven Design*, especially its ADD process description and overall design workflow. The paper describes ADD as an iterative process that begins by reviewing architectural drivers, establishes an iteration goal, selects elements for refinement, chooses design concepts, instantiates elements and relationships, records design decisions and preliminary views, and evaluates whether the iteration goal was met. The paper's implementation sketches views during element instantiation, an explicit adjustment to the original step placement.

This document maps that source method to the HarnessWeaver case profile. It does not claim that HarnessWeaver's five workflow stages are a canonical ADD decomposition, nor that a generated alternative is a validated architecture. The paper's case results motivate a prototype and human review; they are not ground truth for a future project brief.

## Source-to-profile mapping

| ADD activity in the paper | HarnessWeaver artifact or stage | Profile treatment and review evidence |
| --- | --- | --- |
| Review and prioritize architectural drivers: purpose, primary functional requirements, quality attributes, constraints, and concerns. | `frame-design-task` produces `design-context` from `design-brief`. | Preserve supplied drivers and their priority. Record missing drivers as questions; do not fill them with assumptions. Reviewer checks that each driver in the output traces to the brief or is labeled as an assumption. |
| Establish the goal for the current design iteration by selecting key drivers. | `set-iteration-goal` produces an explicit `iteration-goal` from the `design-context`; `develop-alternatives` addresses that goal. | The profile requires an explicit, bounded goal for each iteration before candidate design begins. If no iteration can be justified from the brief, record the gap and ask the architect. |
| Select architectural elements to refine or decompose. | `develop-alternatives` records the selected boundary and elements in `architecture-alternatives`. | State which system boundary or elements are being considered. Preserve unresolved boundaries instead of implying a complete decomposition. |
| Select design concepts, such as patterns, tactics, reference architectures, frameworks, or other components, to address the iteration goal. | `develop-alternatives` records selected concepts and rationale in each `architecture-alternative`. | Tie each concept to an iteration driver and evidence. Identify discarded alternatives where the brief or exploration supports them; do not imply exhaustive search. |
| Instantiate elements, relationships, responsibilities, and interfaces. | `develop-alternatives` produces `architecture-alternatives` and `architecture-views`. | Describe components, responsibilities, connections, and interfaces at the level needed to compare the candidates. Mark unsupported details as assumptions or open questions. |
| Sketch preliminary architecture views and record design decisions. | `develop-alternatives` produces `architecture-views`; `compare-decisions` records decisions in `decision-record`. | The paper's implementation creates view sketches during instantiation (its step 5) rather than waiting until the original step 6. The profile follows that practical placement and keeps the decision and rationale visible. |
| Analyze whether the iteration goal was achieved and decide whether another iteration is needed. | `compare-decisions` evaluates the `iteration-goal`; the `architect-design-review` gate records the human decision. | Compare consequences against the same drivers, state unresolved tradeoffs, and record whether the architect accepts, rejects, revises, or defers each candidate. The profile does not claim an optimal design. |

## Human interaction and fidelity

The paper's process is stepwise: a human can review and guide each ADD step. Its reported experiments deliberately did not provide feedback during the design steps, while the authors still identify human feedback as important for critical and nuanced decisions. HarnessWeaver's current profile preserves architect review and bounded iteration but does not require approval after every intermediate step. That is a prototype adaptation. A case brief may add intermediate review gates when its risk or decision process requires them.

The profile's validation and review stages check source traceability, assumption labeling, alternative comparison, and usefulness to an accountable architect. They do not implement the ReArch search/reflection/ranking procedure. ReArch is a contrasting design-exploration direction documented in `review-criteria.md`; its generated rankings are not used as ADD outputs or as case-specific ground truth.

## Review questions

Qualified reviewers should check whether:

- the design task and iteration goals reflect the brief's actual drivers and constraints;
- candidate selection and decomposition are justified, with search limits disclosed;
- component responsibilities, relationships, interfaces, views, and decisions are clear enough to inspect;
- each material rationale traces to a driver or is explicitly labeled as an assumption;
- consequences and tradeoffs are compared against the same drivers;
- the architect's decision and unresolved questions are recorded without claiming optimality;
- the chosen human-feedback cadence is adequate for this case, including whether intermediate ADD outputs need review.

