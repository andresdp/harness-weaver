#!/usr/bin/env python3
"""Build a clean, anonymized reviewer snapshot for the CAIN 2027 paper.

Run from any directory inside the source checkout:

    python tools/create_reviewer_snapshot.py --output /tmp/hw-reviewer-snapshot

The output must not exist. The builder copies only the curated paths below,
removes evaluator-only case data, scrubs source author/local-machine details,
checks the result, and creates a new anonymous root commit. It never changes
the source checkout or pushes anything. To add the resulting root commit as a
local branch in the source checkout, use the fetch command printed at the end.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import sys
import unicodedata
import zipfile
from pathlib import Path


EVIDENCE_IDS = (
    "run-atam-claude-banking-20261025T205340",
    "run-atam-claude-banking-20261026T021159",
    "run-atam-deepagents-banking-20261025T214917",
    "run-atam-deepagents-banking-20261025T225711",
    "run-sara-claude-campus-bike-20261029T164100",
    "run-sara-claude-campus-bike-20261029T185144",
    "run-sara-claude-campus-bike-20261030T010727",
    "run-sara-deepagents-campus-bike-20261029T145335",
)

COPY_PATHS = (
    "README.md",
    "architecture.md",
    "LICENSE",
    "THIRD-PARTY-NOTICES.md",
    "pyproject.toml",
    "src/harnessweaver",
    "specs/harnessspec",
    "tests/test_spec.py",
    "tests/test_sandbox.py",
    "tests/test_stage_host.py",
    "tests/test_deepagents_runtime.py",
    "baselines/revfactory-harness-v2.1.0-en",
    "benchmarks/atam",
    "docs/cain-2027/main.tex",
    "docs/cain-2027/references.bib",
    "docs/cain-2027/SANDBOX-RUNBOOK.md",
    "docs/cain-2027/PILOT-COMPARISON.md",
    "docs/README.md",
    "docs/quickstart.md",
    "docs/external-materials.md",
    "docs/PUBLIC-RELEASE-CHECKLIST.md",
    "docs/assets/harnessweaver-agentic-logo.png",
    "pilots/README.md",
    "pilots/atam/README.md",
    "pilots/atam/harness-answers.yaml",
    "pilots/atam/harnessspec-v0.2.yaml",
    "pilots/atam/pilot.yaml",
    "pilots/atam/prompts",
    "pilots/atam/sources",
    "pilots/atam/generated",
    "pilots/sara/README.md",
    "pilots/sara/harness-answers.yaml",
    "pilots/sara/pilot.yaml",
    "pilots/sara/prompts",
    "pilots/sara/sources",
    "pilots/sara/generated",
    "tools/create_reviewer_snapshot.py",
)

# Local-only source trees that must not enter the reviewer artifact, even if a
# future change adds one of their parent directories to COPY_PATHS.
EXCLUDED_DIRECTORIES = {".agents", "case-studies"}

TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".tex", ".bib",
    ".py", ".sh", ".toml", ".mmd", ".ini", ".cfg", ".xml", ".csv",
}


def git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def repo_root(start: Path) -> Path:
    return Path(git(start, "rev-parse", "--show-toplevel")).resolve()


def author_tokens(root: Path) -> tuple[list[str], list[str]]:
    """Collect author names/emails from source history without storing them here."""
    raw = git(root, "log", "--all", "--format=%an%x00%ae", check=False)
    names: set[str] = set()
    emails: set[str] = set()
    for line in raw.splitlines():
        name, sep, email = line.partition("\x00")
        if sep and name.strip() and name.strip().lower() not in {"anonymous reviewer", "anonymous"}:
            names.add(name.strip())
        if (
            sep and email.strip() and "@" in email
            and not email.strip().lower().startswith("anonymous@")
        ):
            emails.add(email.strip())
    # Include the checked-out tree's configured author when history is shallow.
    for key, bucket in (("user.name", names), ("user.email", emails)):
        value = git(root, "config", "--get", key, check=False).strip()
        if value and (key.endswith("name") or "@" in value):
            if key.endswith("name") and value.lower() not in {"anonymous reviewer", "anonymous"}:
                bucket.add(value)
            elif key.endswith("email") and not value.lower().startswith("anonymous@"):
                bucket.add(value)
    return sorted(names, key=len, reverse=True), sorted(emails, key=len, reverse=True)


def deidentification_tokens(names: list[str], emails: list[str]) -> list[tuple[str, str]]:
    """Build literal and TeX-escaped author tokens from repository metadata."""
    tokens: dict[str, str] = {}
    for email in emails:
        tokens[email] = "<redacted-email>"
    for name in names:
        words = name.split()
        candidates = {name}
        if words:
            candidates.add(words[-1])
            if len(words) > 1:
                candidates.add(" ".join(words[-2:]))
        for candidate in candidates:
            if candidate.lower() in {"anonymous", "anonymous reviewer"}:
                continue
            tokens[candidate] = "Anonymous author"
            ascii_candidate = "".join(
                char for char in unicodedata.normalize("NFKD", candidate)
                if not unicodedata.combining(char)
            )
            if ascii_candidate != candidate:
                tokens[ascii_candidate] = "Anonymous author"
            # BibTeX/LaTeX commonly encodes an accented vowel as \\'<letter>.
            tex_candidate = "".join(
                "\\'" + char.lower()
                if char.lower() in "aeiou" and char != unicodedata.normalize("NFKD", char)[0]
                else char
                for char in candidate
            )
            if tex_candidate != candidate:
                tokens[tex_candidate] = "Anonymous author"
    return sorted(tokens.items(), key=lambda pair: len(pair[0]), reverse=True)


def copy_tree(source: Path, target: Path) -> None:
    if source.name in EXCLUDED_DIRECTORIES:
        raise RuntimeError(f"refusing to copy excluded source tree: {source.name}")

    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {
            item for item in names
            if item == ".DS_Store"
            or item in EXCLUDED_DIRECTORIES
            or item == "__pycache__"
            or item == "settings.local.json"
            or item.endswith((".pyc", ".pyo"))
        }

    if source.is_dir():
        shutil.copytree(source, target, ignore=ignore)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def make_snapshot_writable(root: Path) -> None:
    """Keep generated source modes where useful but allow redaction and Git."""
    for path in root.rglob("*"):
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():
            path.chmod(mode | stat.S_IWUSR | stat.S_IXUSR)
        else:
            path.chmod(mode | stat.S_IWUSR)
    mode = stat.S_IMODE(root.stat().st_mode)
    root.chmod(mode | stat.S_IWUSR | stat.S_IXUSR)


def scrubber(root: Path, output: Path) -> tuple[callable, list[str]]:
    names, emails = author_tokens(root)
    # Generic locations are redacted even when they do not match this machine.
    replacements = deidentification_tokens(names, emails)
    local_account = Path.home().name
    if local_account and local_account.lower() not in {"anonymous", "user"}:
        replacements.append((local_account, "<redacted-user>"))
        replacements.sort(key=lambda pair: len(pair[0]), reverse=True)
    revision = git(root, "rev-parse", "HEAD", check=False)

    def scrub(value: str) -> str:
        value = re.sub(
            r"/Users/[^/\s\"']+/Documents/GitHub/harness-weaver-sandboxes",
            "$SANDBOX_ROOT", value,
        )
        value = re.sub(
            r"/Users/[^/\s\"']+/Documents/GitHub/harness-weaver",
            "$REPOSITORY_ROOT", value,
        )
        value = re.sub(r"/Users/[^/\s\"']+", "$HOME", value)
        value = re.sub(r"/private/tmp/claude-[^/\s\"']+", "$SCRATCH/claude", value)
        value = re.sub(r"/tmp/cc-socks/[^/\s\"']+", "$SCRATCH/socket", value)
        value = re.sub(
            r'(?i)("(?:session_id|sessionId)"\s*:\s*")[^\"]*(")',
            r"\1<redacted>\2", value,
        )
        value = re.sub(r"(?i)(session_id\s*:\s*)[0-9a-f-]{36}", r"\1<redacted>", value)
        value = re.sub(r"(?i)(session\s+id\s*[:=]?\s*)[0-9a-f-]{36}", r"\1<redacted>", value)
        value = re.sub(r"(?i)(--resume\s+)[0-9a-f-]{36}", r"\1<redacted>", value)
        value = re.sub(r"MacBook-Air-[0-9]+(?:\.[A-Za-z0-9.-]+)?", "<host>", value)
        value = re.sub(
            r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            "<redacted-uuid>", value,
        )
        if revision and len(revision) == 40:
            value = value.replace(revision, "<source-revision-redacted>")
        value = re.sub(
            r'(?i)("repository_commit"\s*:\s*")[0-9a-f]{40}(")',
            r"\1<redacted>\2", value,
        )
        # Hide the known self-citation by its stable BibTeX key, while keeping
        # unrelated citations intact. Author names are derived from Git above.
        for source, replacement in replacements:
            value = re.sub(re.escape(source), replacement, value, flags=re.IGNORECASE)
        value = re.sub(r"(?i)Anonymous author et al\.", "prior work", value)
        return value

    return scrub, [token for token, _replacement in replacements]


def load_case(source: Path, destination: Path, pilot: str) -> None:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required; run with the project harness environment") from exc
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    allowed = ("case", "description", "generation_inputs", "checks")
    if pilot == "sara":
        allowed = ("case", "description", "generation_inputs", "evaluator_only", "checks")
    clean = {key: data[key] for key in allowed if key in data}
    if pilot == "sara":
        clean["evaluator_only"] = []
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Avoid an additional YAML library in the output repo; preserve structure
    # and comments by filtering the original document to permitted top-level
    # sections is more error-prone, so use PyYAML's stable safe dumper here.
    destination.write_text(
        yaml.safe_dump(clean, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


def anonymize_paper(output: Path, scrub) -> None:
    tex = output / "docs/cain-2027/main.tex"
    tex_text = scrub(tex.read_text(encoding="utf-8"))
    # Replace the author attribution in the designated ReArch self-citation
    # sentence without embedding the author's name in this reusable script.
    tex_text = re.sub(
        r"[^.\n]*et al\. introduced ReArch",
        " Prior work introduced ReArch",
        tex_text,
    )
    tex.write_text(tex_text, encoding="utf-8")
    bib = output / "docs/cain-2027/references.bib"
    bib_text = scrub(bib.read_text(encoding="utf-8"))
    bib_text = re.sub(
        r"(?ms)^@inproceedings\{rearch,.*?^\}",
        "@inproceedings{rearch,\n  author = {{Anonymous}},\n"
        "  title = {Omitted for double-blind review},\n"
        "  booktitle = {Omitted for double-blind review},\n  year = {2025}\n}",
        bib_text,
    )
    bib.write_text(bib_text, encoding="utf-8")


def scrub_files(output: Path, scrub) -> int:
    count = 0
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        # This source file contains the scrubber's own path patterns. Keep it
        # intact; it contains no machine-specific identity data.
        if path.relative_to(output).as_posix() == "tools/create_reviewer_snapshot.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        cleaned = scrub(text)
        if cleaned != text:
            path.write_text(cleaned, encoding="utf-8")
            count += 1
    for path in sorted(output.rglob("*.zip")):
        if not zipfile.is_zipfile(path):
            continue
        entries: list[tuple[zipfile.ZipInfo, bytes]] = []
        changed = False
        with zipfile.ZipFile(path) as source:
            for item in source.infolist():
                if Path(item.filename).name == ".DS_Store":
                    changed = True
                    continue
                data = source.read(item.filename)
                if Path(item.filename).suffix.lower() in TEXT_SUFFIXES:
                    try:
                        text = data.decode("utf-8")
                    except UnicodeDecodeError:
                        text = None
                    if text is not None:
                        clean = scrub(text)
                        if clean != text:
                            data = clean.encode("utf-8")
                            changed = True
                entries.append((item, data))
        if changed:
            temp = path.with_suffix(path.suffix + ".tmp")
            with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as target:
                for item, data in entries:
                    target.writestr(item, data)
            temp.replace(path)
            count += 1
    return count


def add_evidence_copy_digests(output: Path) -> None:
    evidence = output / "docs/cain-2027/evidence"
    for manifest_path in evidence.glob("*/manifest.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        hashes = {}
        for item in sorted(manifest_path.parent.rglob("*")):
            if item.is_file() and item != manifest_path:
                hashes[str(item.relative_to(manifest_path.parent))] = hashlib.sha256(
                    item.read_bytes()
                ).hexdigest()
        manifest["redacted_copy"] = True
        manifest["published_evidence_sha256"] = hashes
        manifest["digest_note"] = (
            "Source-run digests preserve the original evidence record; "
            "published_evidence_sha256 indexes this sanitized reviewer copy."
        )
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def write_snapshot_gitignore(output: Path) -> None:
    if not (output / "README.md").is_file():
        raise RuntimeError("the project README.md was not copied into the snapshot")
    if not (output / "docs/assets/harnessweaver-agentic-logo.png").is_file():
        raise RuntimeError("the README logo asset was not copied into the snapshot")
    (output / ".gitignore").write_text(
        ".env\n.env.*\n!.env.example\n.claude/settings.local.json\n"
        ".DS_Store\n__pycache__/\n*.py[cod]\n*.egg-info/\n",
        encoding="utf-8",
    )


def validate(output: Path, identity_values: list[str]) -> None:
    atam = (output / "pilots/atam/cases/banking.yaml").read_text(encoding="utf-8")
    if "evaluator_only" in atam:
        raise RuntimeError("ATAM reviewer case unexpectedly contains evaluator-only data")
    sara = (output / "pilots/sara/cases/campus-bike.yaml").read_text(encoding="utf-8")
    if re.search(r"evaluator_only:\s*\n\s+-", sara):
        raise RuntimeError("SARA reviewer case unexpectedly contains evaluator-only entries")
    paper = (output / "docs/cain-2027/main.tex").read_text(encoding="utf-8")
    if re.search(r"\bet al\.\s+introduced ReArch", paper):
        raise RuntimeError("ReArch self-citation still identifies its author in the reviewer manuscript")
    if any(path.name == ".DS_Store" for path in output.rglob("*")):
        raise RuntimeError("Finder metadata remains in snapshot")
    patterns: list[tuple[str, str]] = [
        # Avoid matching documentation examples such as `/Users/` or
        # `/Users/<name>`; flag only a concrete path segment.
        ("home path", r"/Users/(?!<)[^/\s<>\"']+(?=/|$|[\"'])"),
        ("Claude scratch path", r"/private/tmp/claude-[^/\s]+"),
        ("machine hostname", r"MacBook-Air-[0-9]+"),
        ("session identifier", r"(?i)session_id\s*[:=]\s*[0-9a-f-]{36}"),
    ]
    for value in identity_values:
        if len(value) >= 5:
            patterns.append(("author identity", re.escape(value)))
    offenders: list[str] = []
    for path in output.rglob("*"):
        relative_parts = path.relative_to(output).parts
        if any(part in EXCLUDED_DIRECTORIES for part in relative_parts):
            raise RuntimeError(f"excluded directory was copied: {path.relative_to(output)}")
        if not path.is_file():
            continue
        # The builder's literal patterns intentionally mention identity-bearing
        # path shapes; exclude this generic source from residue scans.
        if path.relative_to(output).as_posix() == "tools/create_reviewer_snapshot.py":
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            found = [
                label for label, pattern in patterns
                if re.search(pattern, content, 0 if label == "home path" else re.IGNORECASE)
            ]
            if found:
                offenders.append(f"{path.relative_to(output)} ({', '.join(found)})")
        elif path.suffix.lower() == ".zip" and zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    if Path(member).suffix.lower() not in TEXT_SUFFIXES:
                        continue
                    try:
                        content = archive.read(member).decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                    found = [
                        label for label, pattern in patterns
                        if re.search(pattern, content, 0 if label == "home path" else re.IGNORECASE)
                    ]
                    if found:
                        offenders.append(f"{path.relative_to(output)}::{member} ({', '.join(found)})")
    if offenders:
        raise RuntimeError("Possible identity/path leakage remains:\n  " + "\n  ".join(offenders[:50]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="new snapshot repository directory")
    parser.add_argument("--branch", default="hw-artifact", help="neutral branch name inside output repo")
    args = parser.parse_args()
    root = repo_root(Path.cwd())
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"output already exists; choose a fresh path: {output}")
    if output == root or root in output.parents:
        parser.error("output must be outside the source checkout")
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        for relative in COPY_PATHS:
            source = root / relative
            if not source.exists():
                raise FileNotFoundError(f"required snapshot input missing: {source}")
            copy_tree(source, output / relative)
        for evidence_id in EVIDENCE_IDS:
            copy_tree(
                root / "docs/cain-2027/evidence" / evidence_id,
                output / "docs/cain-2027/evidence" / evidence_id,
            )

        make_snapshot_writable(output)
        load_case(root / "pilots/atam/cases/banking.yaml", output / "pilots/atam/cases/banking.yaml", "atam")
        load_case(root / "pilots/sara/cases/campus-bike.yaml", output / "pilots/sara/cases/campus-bike.yaml", "sara")
        write_snapshot_gitignore(output)
        scrub, identity_values = scrubber(root, output)
        anonymize_paper(output, scrub)
        redacted = scrub_files(output, scrub)
        add_evidence_copy_digests(output)
        for path in output.rglob(".DS_Store"):
            path.unlink()
        validate(output, identity_values)

        git(output, "init")
        git(output, "symbolic-ref", "HEAD", f"refs/heads/{args.branch}")
        git(output, "add", "--all")
        git(
            output,
            "-c", "user.name=Anonymous reviewer",
            "-c", "user.email=anonymous@users.noreply.github.com",
            "-c", "committer.name=Anonymous reviewer",
            "-c", "committer.email=anonymous@users.noreply.github.com",
            "commit", "-m", "Create anonymized CAIN reviewer artifact snapshot",
        )
        files = len([path for path in output.rglob("*") if path.is_file() and ".git" not in path.parts])
        commit = git(output, "rev-parse", "HEAD")
        print(f"Snapshot created: {output}")
        print(f"Sanitized text/archive files: {redacted}")
        print(f"Files in snapshot: {files}")
        print(f"Anonymous root commit: {commit}")
        print("No push was performed.")
        print("To add it as a local branch in the source checkout:")
        print(f"  git fetch {output} HEAD:refs/heads/{args.branch}")
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
