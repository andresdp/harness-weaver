# Public release checklist

**Status: not ready for a public release.** This is a working review of the checkout on 2026-10-28, not a complete security, privacy, or rights audit. Resolve the release gates below before creating or publishing a public snapshot.

## Findings from this review

- A repository-level MIT `LICENSE` and `THIRD-PARTY-NOTICES.md` have been added. The MIT terms are scoped to original HarnessWeaver materials; they do not relicense Revfactory or other third-party content.
- The repository previously tracked substantial third-party and case-study material, including the ArchEval package, reference papers, and a human-evaluation spreadsheet. Ignore rules now exclude `papers/`, `case-studies/architecture-eval/`, and `case-studies/atam-evaluator/`, and the tracked files in those paths are staged for removal from the current index. Local copies are preserved. Their citations are in `docs/external-materials.md`.
- The current branch history still contains commits with those files. Ignore rules and index removals do not erase earlier commits. The selected clean-snapshot approach must create the public snapshot without inheriting those commits; do not merge this branch directly into a public `main`.
- There are 85 tracked files under `docs/cain-2027/evidence/`, including prompts, execution records, model outputs, and sandbox artifacts. Review these for local paths, personal or confidential case details, credentials, model/provider identifiers, and material that should remain research-internal.
- The repository has no top-level `SECURITY.md` or `CONTRIBUTING.md`. Decide whether to add them and specify a contact route before inviting public contributions or vulnerability reports.
- `.env` is ignored and `.env.example` contains empty credential placeholders. The local `.claude/settings.local.json` was not ignored; the repository `.gitignore` now excludes it. Recheck before staging or publishing.
- The local-path scan found workstation-specific path markers in ATAM DeepAgents run records under `pilots/atam/deepagents/runs/`. That directory is ignored and none of those run records are tracked; do not force-add them without sanitizing.
- A scoped token-pattern scan of selected Markdown, YAML, JSON, and source folders found no conventional credential-pattern matches. The scan excluded full run evidence, generated bundles, case-study sources, PDFs, and Git history, so it does **not** clear those areas.
- The current branch is `feat/cain-sources-sandbox-host` and the working tree already has user changes in progress, including SARA pilot files and manuscript drafts. Do not stage broadly or publish this working tree as a release snapshot without reconciling those changes.
- The CAIN paper files currently present in the working tree are not a reviewer-anonymous package: the ReArch citation names an author, and branch history, PDF metadata, logs, and copied source documents can identify authors too. Keep the manuscript/reviewer package on a separate clean branch and validate the final exported package with the chosen anonymization tool.

## Release gates

### 1. Verify repository licensing scope

- Confirm the repository-level MIT license and the copyright-holder wording with project contributors before release.
- Keep the scope statement in `README.md` and `THIRD-PARTY-NOTICES.md`; the MIT license cannot grant rights to third-party works or case-study material that the project does not own.
- Preserve and follow the separate licenses and attribution requirements for the pinned Revfactory baseline and any other imported code.

### 2. Establish provenance and redistribution rights

- Inventory the contents of `case-studies/`, `papers/`, `baselines/`, `legacy/`, benchmark datasets, spreadsheets, and generated bundles.
- For every external item, record its source, author, license or permission, required attribution, and whether redistribution is allowed.
- Remove full-text papers, datasets, and code that cannot be redistributed; replace them with citations or links where possible.
- Check that generated skills, prompts, schemas, and reports do not reproduce material beyond the rights of their source.

### 3. Review evidence and data

- Decide which run records are necessary for reproducibility. Keep the smallest complete evidence set and document how it was produced.
- Scrub workstation paths, usernames, session identifiers, local settings, provider details that should remain private, and any private case inputs from reports, transcripts, logs, and metadata.
- Confirm that all included inputs may be redistributed and that evaluation-only reference outputs are not mixed into generation bundles.
- Recompute checksums/manifests after sanitizing evidence so they describe the public artifacts actually shipped.

### 4. Audit secrets across files and Git history

- Run a maintained secret scanner over the complete staged tree and all reachable Git history, including ignored or formerly committed files.
- Inspect scanner findings manually. Revoke any exposed credential first; remove it from history before publishing if one was committed.
- Review `.env.example`, local agent settings, notebooks, runtime records, shell scripts, and generated bundles for copied credentials or private endpoints.
- Confirm local settings and environment files are ignored and that no broad `git add` will capture them.

### 5. Prepare the anonymous reviewer package separately

- Create a clean reviewer branch/package containing only the paper, the minimum reproducibility instructions, and the artifacts required to evaluate the claims.
- Do not derive anonymity from renaming the paper alone. Check author names in citations, acknowledgements, affiliations, repository URLs, commit history, PDF/DOCX metadata, file paths, comments, and output logs.
- Preserve the full scholarly citation in the public/non-anonymous manuscript source; create the reviewer-specific anonymized citation only in the separate copy where required by the venue.
- Run `anonymous4science` against that isolated package, then manually inspect its output and the final archive. Keep an untouched source copy for recovery.
- Verify that the reviewer branch does not contain unrelated project history or personal author metadata.

### 6. Stage a release snapshot

- Start from a clean, reviewed release commit; do not include unrelated SARA work, local paper drafts, or unreviewed generated outputs by accident.
- Review the complete staged diff and file list, including binary files and symlinks.
- Confirm docs link only to retained files and accurately describe prototype maturity and runtime limitations.
- Add contribution/security guidance if the project will accept external contributions or reports.
- Run the project’s documented validation and test commands on the exact release commit, then record their results.
- Make the repository public only after the rights, data, secrets, anonymization, and license gates have been resolved.

## Reviewer-branch separation

The public repository and anonymous submission artifact have different audiences and can contain different files. Keep the scholarly source and normal project history in the project checkout. Build the reviewer copy from a clean base, copy only the needed paper/reproduction material, sanitize that copy, and verify the exported archive. Do not use the public repository itself as the anonymous artifact without a separate identity and history review.

## Public-snapshot approach selected

Preserve the current feature branch and prepare a separate clean public snapshot after the release gates above are resolved. The snapshot must be based on a new root/clean history and include only the reviewed repository tree; do not merge this feature branch's existing history into the public `main`, because prior commits contain the excluded papers and third-party case-study package. Keep uncommitted SARA and manuscript work out unless it is reviewed and deliberately included. The ignored local source copies remain available in the working checkout for research use.
