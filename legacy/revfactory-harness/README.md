# Legacy: revfactory/harness documentation

These files come from the upstream [revfactory/harness](https://github.com/revfactory/harness) project (Apache-2.0, harness v2.1.0), from which HarnessWeaver's generation skills were derived. They describe the upstream Claude Code plugin, not HarnessWeaver. They are kept for provenance and reference and are not maintained as HarnessWeaver documentation.

| File | Origin | Local changes |
|---|---|---|
| `migration-v1-to-v2.md` | Upstream `docs/migration-v1-to-v2.md` (Korean) | None (identical at upstream commit `928de2c`) |
| `migration-v1-to-v2_EN.md` | English translation of the above | Translation |
| `quickstart_EN.md` | English translation of upstream `docs/quickstart.md` | Translation; links updated |
| `README_EN.md` | English translation of upstream `README.md` | Translation; a HarnessWeaver preface and install paths pointing at `src/harnessweaver/skills/` |
| `manual-setup_EN.md` | Manual-install guide for the translated skills | Install paths changed to `src/harnessweaver/skills/`; the `deepagents-port` skill removed |
| `harness-100-prompts_EN.md` | Prompt cookbook for regenerating [harness-100](https://github.com/revfactory/harness-100) examples | Includes HarnessWeaver-written appendices (four-stage architecture decision pipeline, ATAM evaluation), which the DeepAgents target reference cites |

HarnessWeaver documentation is indexed in [docs/README.md](../../docs/README.md). The verbatim upstream skills used as a generation baseline are in [baselines/revfactory-harness-v2.1.0/](../../baselines/revfactory-harness-v2.1.0/BASELINE.md).
