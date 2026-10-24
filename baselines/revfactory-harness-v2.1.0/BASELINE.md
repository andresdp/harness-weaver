# Baseline: revfactory/harness v2.1.0 skills (verbatim)

The upstream skills that HarnessWeaver's `harness` and `evolve` skills were derived from, unmodified (Korean). **Runs use the English translation** in [`../revfactory-harness-v2.1.0-en/`](../revfactory-harness-v2.1.0-en/TRANSLATION.md), so that every arm runs in English. This directory is the authority that translation is checked against.

## Provenance

- Source: <https://github.com/revfactory/harness>, commit `928de2c5d233f02c95e68ead22eee034e2ca3d9c` (2026-09-26, "하네스 v2 전면 재구축 및 v2.1.0 릴리스 (#51)"), plugin version 2.1.0.
- The later upstream commit `92d9f1b` (2026-09-28) only adds `docs/harness-animation.mp4`; `skills/`, `LICENSE` and `.claude-plugin/plugin.json` are identical.
- Exported with `git archive 928de2c skills LICENSE .claude-plugin/plugin.json` on 2026-10-24. **No file in this directory may be edited.** A changed digest invalidates baseline runs.
- License: Apache-2.0 (`LICENSE`), © the upstream author. Redistributed unmodified with attribution.
- Language: Korean (upstream original). See "Language" below.

## Files (SHA-256)

```text
bae1caa988a742c5a756faa45e33b6c72f21f9873b8e7f1e0ce87fcf0a4c747b  LICENSE
c7873546dec075d3b94341567314692c2959bb4ce69dde0084d12dae2f02a02c  skills/evolve/SKILL.md
2d941632cc3cceedc33317334fc43e4c2f8c5c834a35b8e745fe0f2368ddf039  skills/harness/SKILL.md
839100f48e3196ff14c61e82e089eb6fc706622d9b9318b642373faafc8c415c  skills/harness/references/execution-modes.md
04a68043ea3ff2100445faf05ccb2fd1eca490f0a95913e750b1a6d66d3d0f79  skills/harness/references/model-selection-guide.md
b0e97c937c8a218176931aa79bc8ddc1e7b4dcc584ccc0cb89a01bbbf1ca602b  skills/harness/references/orchestrator-template.md
cd45d7f937a886aa62db13ad28495efd9b7e851f2b6140229643fbf27d23b5b2  skills/harness/references/qa-agent-guide.md
9017c01a908dab03297b41ef8b1fafc20cdeaf1d100a92f1c9934ed0515c1f6a  skills/harness/references/skill-testing-guide.md
7007ef5827610dad3a2ee8d3ec6dc0a6d5652d84e7bfa60c2b80b8b91e7ebd69  skills/harness/references/skill-writing-guide.md
a88bc2b56dd08eafa92e2a3f5e2e2f585b6d24e6bf367f3485e4db42198632a6  skills/harness/references/team-examples.md
427ef080d16dd2b204739ec9d6c24eded987c2ac62bc82ea4ef8f75b65a78d0d  skills/harness/references/team-patterns.md
877f87ced47a0ef776d26b806548ff55797f925f12718a8c5d2681203607c56c  skills/harness/references/workflow-recipes.md
38dca6e26daae13779656a42566bd779a7e4537aed66fe6c1b565a95ef104f60  .claude-plugin/plugin.json
```

Verify with `cd baselines/revfactory-harness-v2.1.0 && shasum -a 256 -c BASELINE.sha256`.

## How it is loaded

As upstream distributes it: as a Claude Code plugin named `harness`, whose skills are `harness:harness` and `harness:evolve`. In a generation sandbox:

```shell
claude --plugin-dir <sandbox>/skills-plugin     # a read-only copy of ../revfactory-harness-v2.1.0-en
```

The HarnessWeaver arm is loaded the same way, from a plugin wrapper that `hw sandbox create` builds around `src/harnessweaver/skills/{harness,evolve}`. Both arms then differ only in skill content, not in installation method.

## Comparison protocol (Claude runtime only)

| | Baseline arm (B) | HarnessWeaver arm (HW) |
|---|---|---|
| Skills | `baselines/revfactory-harness-v2.1.0-en/` (English translation of this directory) | `src/harnessweaver/skills/` at a recorded commit |
| Inputs | the pilot's `sources/` (intent, methodology, domain) | the same `sources/` |
| Request | the same opening prompt, verbatim (runtime-neutral: build an ATAM evaluation harness from `sources/`, output in `generated/`) | same |
| Target | Claude Code project (the only form the upstream skill emits) | Claude Code project (gate G4 = claude) |
| Gate answers | given live by the user; recorded from the transcript | live or from `harness-answers.yaml`; recorded in `design-notes.md` |
| Coding agent / model | same Claude Code version and model | same |
| Execution | the generated project runs in an execution sandbox on the same case (banking, inputs only) | same |

Where the two skills ask equivalent questions, the user gives equivalent answers. Questions that only one arm asks are recorded as a difference, not answered for the other arm.

**Observed, descriptively (no superiority claim from single runs):**

1. Questions asked (count, topics) and the user's answers.
2. Generated file inventory and size; time to generate; tokens or cost when available.
3. Bundle structural checks (`hw check-bundle --target claude`).
4. Methodology coverage: for each activity, semantic-state field, verification and human gate in `sources/methodology.yaml`, whether the generated project represents it and where. Scored by inspection with a fixed checklist, by two people where possible.
5. Fidelity record: present in HW (`materialization-report.md`); absent in B, so the same checklist is applied directly to B's files.
6. Execution on the case: ATAM checker result (`benchmarks/atam/pilot.py check`), presence of semantic state with evidence, report status.
7. Manual interventions needed before execution, with reasons.

**Threats to record:**

- Single run per arm and LLM nondeterminism.
- Translation fidelity of the English baseline (see `../revfactory-harness-v2.1.0-en/TRANSLATION.md`).
- Live answers by one person.
- The HW skills were developed by the same team that runs the comparison.
- The upstream skill does not read a HarnessSpec, so the HW arm's design phase is part of the treatment, not a confound to remove.

## Language

All runs are in English: the opening prompt, live answers, and both arms' skills. The baseline arm uses the direct English translation ([`../revfactory-harness-v2.1.0-en/`](../revfactory-harness-v2.1.0-en/TRANSLATION.md)), so baseline vs HarnessWeaver isolates HarnessWeaver's changes rather than the language of the skills. This Korean original is kept as the authority for the translation and is not run.
