Evaluate this architecture using ATAM. Populate every field in the structured
response. Use null or an empty list when metadata is unavailable; do not invent
values. For every analysis record, set `scenario_reference.id` to the exact ID
of one supplied `raw_candidate_scenarios` item and copy its `description`
verbatim into `scenario_reference.text`. If the case supplies no raw candidate
scenarios, use the exact text of a generated scenario instead. Never paraphrase
or create a scenario reference that cannot be traced to the supplied case or the
report's generated scenarios.
