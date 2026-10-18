# ArchEval ATAM pilot

This HarnessWeaver-owned protocol uses the ArchEval banking case. The case-study source and its ground truth remain unchanged. `pilot.py prepare` copies only `evaluation_inputs` into a new run directory; `ground_truth_outputs` is never copied into generator inputs. `pilot.py check` performs deterministic output checks without loading the evaluator or a model client.

Each run is created once under `runs/<run-id>/`. Its input and manifest are write-once; do not reuse a run ID. After execution, `pilot.py record` writes a single write-once `execution.json` with the arm, runtime/model settings, prediction hash, latency, and cost when available. Keep predictions and logs within that run directory. Store blind review records separately from ground truth; evaluation-only access to reference data belongs in a separate reviewer/evaluator process.

The existing Claude Sonnet banking output is a historical baseline candidate, not a matched baseline: its exact prompt, runtime settings, and execution provenance have not been established by this protocol. A valid comparison still requires new baseline and spec-guided runs under matched settings, deterministic checks, and blinded independent review. The legacy evaluator includes an LLM judge and may download NLTK data; it is not part of the deterministic check command.

Use project Python only through the `harness` Conda environment. For example:

```sh
conda run -n harness python benchmarks/atam/pilot.py prepare --run-id baseline-001
conda run -n harness python benchmarks/atam/pilot.py check benchmarks/atam/runs/baseline-001/prediction.json
```

Preparation writes `evaluation_input.json` and `manifest.json`; the create command fails if the run directory already exists. After producing a prediction within the run directory, record execution details with:

```sh
conda run -n harness python benchmarks/atam/pilot.py record benchmarks/atam/runs/<run-id> \
  --arm spec-guided --runtime claude-code --model <model-version> \
  --settings-json '{"temperature":0.2}' \
  --prediction benchmarks/atam/runs/<run-id>/prediction.json \
  --latency-seconds <seconds> --cost <usd>
```

Omit cost if unavailable. The command refuses to overwrite an existing execution record.
