# SARA source provenance

The SARA workflow source packet used by this pilot is third-party material. The copied `AGENTS.md` and `SKILL.md` files are kept locally under the Git-ignored `harvest-input/` directory and are not distributed in this repository.

- Upstream repository: `NicolasMP51/software-architecture-agent`.
- Inspected revision: `528ae7ce0b054ee1631bd091fe6b759208bbbb6c`.
- Copied sources: four stage `AGENTS.md` files and eleven stage `SKILL.md` files.
- Copy policy: read-only copies; application code, database content, model setup, API/auth code, case examples, and prior outputs are excluded from the source packet.

| Source path | SHA-256 |
|---|---|
| `backend/app/agents/stage1-requirements_drivers/AGENTS.md` | `10e1383389426e0166c3ff60cd10977438fcf936cbb10bf0f68d1cffe0ccf498` |
| `backend/app/agents/stage1-requirements_drivers/skills/driver-identification/SKILL.md` | `1d1f710a9d7b695f60e6ac6c3788e8cf72b86515d5123b32c946adf72274c6f1` |
| `backend/app/agents/stage1-requirements_drivers/skills/quality-attribute-identification/SKILL.md` | `db5c1c8dfed5a6a9b5b459b6e828ced628bed6d191db9163c6adaacf65b1b0a9` |
| `backend/app/agents/stage1-requirements_drivers/skills/requirements-cross-analysis/SKILL.md` | `1a05c0776a81cb63d0216ed4b73627384917300a31bdca8c81cbf135bf95d983` |
| `backend/app/agents/stage2-solution_design/AGENTS.md` | `ed9e866cd6ffe71206faba204da1571e50e3d92daba34a614ae99feb637b4de5` |
| `backend/app/agents/stage2-solution_design/skills/alternative-generation/SKILL.md` | `bb462603a08b5f70002672c68fcf245295ca700379f3988fe355f1cf3fda65e3` |
| `backend/app/agents/stage2-solution_design/skills/pattern-candidate-identification/SKILL.md` | `0a57b8daf9591a69e870ca3687227cce6dd2b828505483fb6529a05c214d1d58` |
| `backend/app/agents/stage2-solution_design/skills/patterns-compatibility/SKILL.md` | `8e68b3f2b7cb0638300f4476fe47f310fd97024ac88bf112cafe5b64c19fefe2` |
| `backend/app/agents/stage3-alternative_evaluation/AGENTS.md` | `3b1fc7baa2ede0ed41c6b55ee2a86ea1391a54b6832cf331b52065264d242a23` |
| `backend/app/agents/stage3-alternative_evaluation/skills/alternative-evaluation/SKILL.md` | `9602b37866aae2263f60bf03c1e5b43910ec0f3191a1dc46d83771dabc0a8d16` |
| `backend/app/agents/stage3-alternative_evaluation/skills/alternative-selection/SKILL.md` | `65f9996eb602bd1bbc160f30489cdf598f9a43e286c61b91fd02f30e6f0b78c8` |
| `backend/app/agents/stage3-alternative_evaluation/skills/trade-off-analysis/SKILL.md` | `d26d4ab57e55f8c8b01723edf5ed9dd41758b65cf1d66ce73ebb73b572255b80` |
| `backend/app/agents/stage4-architecture_decision/AGENTS.md` | `a24a763a1d1ac024923d5ea77381d6839ba93f0b4a8fba9ca92f2089b45dcee2` |
| `backend/app/agents/stage4-architecture_decision/skills/adr-generation/SKILL.md` | `6a9c1e45a78b9585f659cd7bd774b98ac198f2e9f9d0f2ff309b0b765468d47a` |
| `backend/app/agents/stage4-architecture_decision/skills/architecture-diagram/SKILL.md` | `1d967396a7efe4176fb5ffd0e5f5bddac2e00fb64affff3453f014d840476df5` |

The CampusBike source example is separate and also kept local-only under `pilots/sara/cases/`; its provenance and input boundary are described in `pilots/sara/README.md`.
