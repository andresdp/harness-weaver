# Baseline (English): revfactory/harness v2.1.0 skills, direct translation

The **English generation baseline** used for all Claude-runtime comparisons, so that every arm runs in English. It is a direct translation of the verbatim upstream skills in [`../revfactory-harness-v2.1.0/`](../revfactory-harness-v2.1.0/BASELINE.md) (upstream commit `928de2c`), and a derived artifact, not an upstream release.

## Provenance

- Source: `baselines/revfactory-harness-v2.1.0/` (Korean, verified by its `BASELINE.sha256`).
- Translator: Claude (model `claude-opus-5-5`) in a Claude Code session, 2026-10-24, file by file from the Korean source. Not reviewed by a native Korean speaker.
- Method: sentence-level translation that preserves structure. Every heading, list item, table row, code block, frontmatter field, file path, tool name, API identifier and JSON key is kept as is. Korean prose inside code blocks (comments, prompt strings, phase titles, log messages) is translated. Internal anchors are re-pointed to the English headings.
- Structural parity was checked against the source: per file, identical counts of headings, code fences, table rows and list items, and zero remaining Hangul characters.
- License: Apache-2.0 (`LICENSE`, copied from upstream). The translation is a modification under the license's section 4 and is marked as such here.
- **No file in this directory may be edited** except to correct a translation error. Any correction is listed below with its date, and `TRANSLATION.sha256` is regenerated.

## Translation notes (deliberate adaptations)

| Location | Source | English | Reason |
|---|---|---|---|
| `skills/harness/SKILL.md`, core principle 6 | "templates … are written in Korean, so do not write the artifacts in Korean" | "… written in English … do not write the artifacts in English" | The rule refers to the skill's own language; a literal rendering would refer to a language the translated skill no longer uses. |
| `skills/evolve/SKILL.md`, Phase 3 item 5 | "do not mix Korean sentences into a harness in another language because this document is Korean" | same with "English" | Same reason. |
| `skills/harness/references/skill-writing-guide.md` §2, "Write in the imperative" | Contrasts Korean verb endings (`~한다`/`~하라` vs `~합니다`) | "Write in the form of directives rather than descriptive or polite statements" | Korean-specific grammar; the rule's intent (imperative directives) is kept. |
| `skills/harness/SKILL.md`, step 4-3 "Write as directives" | Choose one of two Korean imperative endings | "Choose one imperative form … and use it consistently" | Same reason. |
| `.claude-plugin/plugin.json`, `description` | Bilingual English + Korean sentence | English sentence only | The Korean sentence duplicates the English one. |
| Example data (`'서울'`, `Q4_매출_최종_v2.xlsx`, Korean commit-message examples) | Korean strings | English equivalents (`'Seoul'`, `Q4_sales_final_v2.xlsx`, …) | Illustrative examples; their role in the text is unchanged. |

## Files (SHA-256)

See `TRANSLATION.sha256`; verify with `shasum -a 256 -c TRANSLATION.sha256`.

## Use

This copy is loaded as a Claude Code plugin named `harness` (skills `harness:harness`, `harness:evolve`), exactly like the Korean original. The comparison protocol is in `../revfactory-harness-v2.1.0/BASELINE.md`. Because of this English arm, baseline vs HarnessWeaver differs in HarnessWeaver's changes, not in language. The residual threat is translation fidelity, which these notes and the parity check address.
