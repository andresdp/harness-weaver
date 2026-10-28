# SARA pilot source packet

`harvest-input/` is a local-only directory containing read-only copies of the four SARA stage `AGENTS.md` files and their eleven `SKILL.md` files. It is ignored by Git because it contains verbatim third-party case-study material. Obtain the files from the upstream repository at the revision recorded in `PROVENANCE.md` before running the pilot. They are source material for the interactive HarnessWeaver harvest, not pre-authored HarnessWeaver `intent.yaml` or `methodology.yaml` files. The generation skill should produce those draft sources and a harvest report under its writable `generated/` directory.

`host-adaptation.md` records the selected standalone HarnessWeaver host and the output-format adaptation before generation. `domain/contracts/architecture-decision.schema.json` is a HarnessWeaver pilot contract for that adapter; it is not claimed to be an original SARA contract.

See `PROVENANCE.md` for source paths, revision, and hashes. The runtime case inputs under `../cases/` are also local-only and Git-ignored because they are copied from third-party case-study material.
