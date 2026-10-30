# HarnessWeaver Python quickstart

HarnessWeaver's first Python component validates HarnessSpec documents. It does not execute workflows or initialize an agent runtime.

From the repository root, install the package in the project Conda environment and validate the ATAM example:

```bash
conda run -n harness python -m pip install -e .
conda run -n harness hw validate pilots/atam/harnessspec-v0.2.yaml
```

The validator checks the supported spec version, required fields and types, duplicate IDs, role/artifact references, and local file references. Local references are resolved relative to the spec file; URI references are left external. Runtime requirements are design labels: pass each supported requirement using `--capability` to check a target runtime. Without capability arguments, validation succeeds while reporting that runtime support was not assessed.

The example references only `evaluation_inputs` from the ArchEval banking case. Do not provide `ground_truth_outputs` to generation. The case-study repository remains the authority for its data and workflow.
