# HarnessWeaver architecture

HarnessWeaver turns a task and its domain method into runtime-specific agentic workflows. The overview below shows the main inputs, activities, outputs, and feedback loop.

```mermaid
flowchart TB
  subgraph inputs["Inputs · blue"]
    intent["Intent<br/>goal and constraints"]
    domain["DomainSpec<br/>knowledge and contracts"]
    method["Methodology<br/>activities, artifacts and checks"]
    case["Case inputs<br/>information for a run"]
  end

  subgraph design["Design and generation · green"]
    hw["HarnessWeaver<br/>design the workflow"]
    spec["HarnessSpec<br/>shared workflow design"]
    materialize["Materialize<br/>adapt to selected runtimes"]
  end

  subgraph runtime["Run workflows · purple"]
    claude["Claude Code workflow"]
    deep["DeepAgents workflow"]
  end

  subgraph results["Results and feedback · orange"]
    artifacts["Reports and artifacts"]
    checks["Automated checks and evaluation"]
    review["Human review"]
    evolve["Evidence-led evolution"]
  end

  intent --> hw
  domain --> hw
  method --> hw
  hw --> spec --> materialize
  materialize --> claude
  materialize --> deep
  case --> claude
  case --> deep
  claude --> artifacts
  deep --> artifacts
  artifacts --> checks --> review --> evolve
  evolve -. "updates inform the next design" .-> hw

  classDef input fill:#E7F1FF,stroke:#3973B9,color:#17365D,stroke-width:1.5px
  classDef design fill:#E7F5EC,stroke:#398254,color:#17472A,stroke-width:1.5px
  classDef runtime fill:#F0EAFE,stroke:#7957B5,color:#39245F,stroke-width:1.5px
  classDef result fill:#FFF1DF,stroke:#C37A22,color:#603A0B,stroke-width:1.5px
  class intent,domain,method,case input
  class hw,spec,materialize design
  class claude,deep runtime
  class artifacts,checks,review,evolve result
```

## Reading the diagram

- **Blue inputs** describe the goal, domain, method, and case-specific information. The case input is supplied when running a workflow.
- **Green activities** turn those descriptions into a runtime-neutral `HarnessSpec`, then materialize it for the selected runtimes.
- **Purple workflows** execute the generated design using the native mechanisms of Claude Code or DeepAgents.
- **Orange results and feedback** collect artifacts, check them, involve a human reviewer, and use evidence to guide future changes.

The `HarnessSpec` is a shared design point; each runtime may realize parts of it differently. Evaluation-only reference data can be kept outside the run and made available only to the evaluator. A shared specification does not guarantee behavioral parity or prove that a workflow is complete or high quality.

HarnessWeaver is a research prototype. It does not automatically search for an optimal workflow. See the [ATAM pilot](pilots/atam/README.md) for a concrete example of the sources, case boundary, runtime forms, and validation steps.
