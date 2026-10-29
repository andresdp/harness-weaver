Run the SARA four-stage architecture-design workflow in this project on the supplied case inputs.

The generation inputs are:

{inputs}

Use the `sara-architecture-orchestrator` skill and follow its four stages in order. Treat the listed files as the
complete project description and functional-requirements inputs. Do not ask the user to provide or clarify files;
record ambiguity or missing information as part of the workflow's analysis. Do not read evaluator-only data or
files outside this project and its `input/` directory.

Keep intermediate artifacts in `_workspace/artifacts/` and the run log in `_workspace/run_log.md`. Complete the
workflow's stage gates and produce the final architecture decision package only after Stage 4 passes. Write the
final JSON package to `{output}` so HarnessWeaver can validate and collect it. Preserve the package fields and
content required by the architecture-decision schema included in this project.
