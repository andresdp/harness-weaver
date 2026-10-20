# SAAM spec-guided prompt (WRCS adaptation)

Follow the baseline SAAM task and evidence restrictions in `baseline_prompt.md`, together with the supplied v0.2 HarnessSpec. The HarnessSpec is the treatment guidance for this arm. Its methodology, stages, artifacts, semantic state, verification rules, and human gate define the intended work and completion conditions. Do not treat runtime activity as method completion.

Apply the stages proportionately: establish context and disclose the partial extraction; analyze the six supplied scenarios; record classifications, supported impacts, and evidence-supported interactions; then review the report for traceability, unknowns, and partialness. Keep classifications and all evaluator reference results unknown to yourself; the input contains source scenarios only. Do not infer the nine absent scenarios or convert extraction-level inferences into source-paper facts. Return the same structured report contract as the baseline arm.
