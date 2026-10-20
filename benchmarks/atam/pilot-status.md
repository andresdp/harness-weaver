# ArchEval ATAM banking pilot status

**Protocol:** `pilot.json` and `pilot.py` in this directory. **Status:** one provider-backed execution per declared DeepAgents orchestration profile completed and passed the deterministic structural checker.

## Matched orchestration profile trial

The three successful trials used the same prepared banking evaluation input, HarnessSpec v0.2, model (`openai:gpt-5.4-mini`), non-streaming/non-verbose settings, and frozen harness asset digest (`6e4db7bc46801eb989906e0d2198b2ef05c3d39a733e0c068267e1faf9e13375`). Each prediction passed `pilot.py check`, including required ATAM sections and exact scenario references.

| Workflow strategy | Interaction style | Run record | Latency |
| --- | --- | --- | ---: |
| `supervisor` | `one_shot_specialist_delegation` | `runs/u7-compare2-supervisor-retry-20261019/execution.json` | 41.44 s |
| `sequential_pipeline` | `typed_artifact_handoffs` | `runs/u7-compare2-sequential-20261019/execution.json` | 77.68 s |
| `fan_out_fan_in` | `parallel_specialist_delegation` | `runs/u7-compare2-fanout-20261019/execution.json` | 46.72 s |

These are single observations on one case. They show that each declared orchestration profile can produce a structurally valid ATAM report; they do not establish relative quality, accuracy, completeness, or reliable latency differences. Model cost was unavailable. An earlier supervisor attempt against the same frozen assets stalled and is retained as a failed record; the successful retry above completed.

## Other evidence and limitations

- The ATAM HarnessSpec validates as v0.2, and the DeepAgents runtime capability check passes for file-based artifact input and output.
- The historical Claude Sonnet banking output at `case-studies/architecture-eval/ATAM/outputs/claude-sonnet-4-5@20250929/banking_output.json` passes deterministic section and scenario-reference checks. This structural check is not a matched baseline: its exact prompt, runtime settings, and execution provenance have not been established by this protocol.
- No blind domain review has been completed for the three new predictions. A matched baseline and two independent reviewers are still needed for paired quality or accuracy claims.
- The ArchEval runner sends model requests through Google Vertex AI or Anthropic Vertex. The existing evaluator also includes an LLM judge and attempts an NLTK data download. Neither is part of the deterministic check command.

Keep `ground_truth_outputs` out of generator inputs and run storage. Store blind review records separately from ground truth; reviewer/evaluator access to reference data belongs in a separate process. The legacy LLM-judge/lexical evaluator is supplementary and must not substitute for blind domain review.

Until matched baseline runs and independent blind reviews are completed, there are no paired quality, speed, completeness, accuracy, or cost claims. A single banking case demonstrates the protocol only and does not generalize to other architecture evaluation tasks.
