"""Create, collect and record generation and execution sandboxes (`hw sandbox ...`).

A sandbox is one directory per (pilot, arm or target, case, run). It holds only what the step
may use: read-only sources and skills for generation; a read-only bundle and generation-only
inputs for execution. Evaluator-only data is never copied in, and checks run from outside.
Sandboxes default to a sibling of the repository so a coding agent inside one cannot read
the repository (which holds reference outputs).
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from harnessweaver._integrity import sha256_file
from harnessweaver.bundles import TARGETS

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPOSITORY_ROOT / "src/harnessweaver/skills"
BASELINE_DIR = REPOSITORY_ROOT / "baselines/revfactory-harness-v2.1.0-en"
LANGCHAIN_SKILLS_DIR = REPOSITORY_ROOT / ".agents/skills"
LANGCHAIN_SKILLS = ("deep-agents-core", "deep-agents-orchestration", "deep-agents-memory", "langgraph-human-in-the-loop")
EVIDENCE_DIR = REPOSITORY_ROOT / "docs/cain-2027/evidence"
ARMS = ("harnessweaver", "revfactory-en")
SANDBOX_FILE = "sandbox.yaml"
MANIFEST_FILE = "manifest.json"
CLAUDE_REPORT_FILENAME = "report.json"   # where Claude execution runs are asked to write the report


class SandboxError(ValueError):
    """A sandbox cannot be created, collected or recorded as requested."""


def _new_sandbox_dir(root: Path | None, name: str) -> Path:
    """Create the sandbox directory, refusing locations inside the repository."""
    sandbox = ((root or default_root()) / name).resolve()
    if sandbox == REPOSITORY_ROOT or REPOSITORY_ROOT in sandbox.parents:
        # Its settings deny reads of the repository, which would also hide the sandbox itself.
        raise SandboxError(f"sandboxes must live outside the repository ({REPOSITORY_ROOT}); got {sandbox}")
    if sandbox.exists():
        raise SandboxError(f"sandbox already exists: {sandbox}")
    sandbox.mkdir(parents=True)
    return sandbox


def default_root() -> Path:
    """Sandboxes live outside the repository unless HW_SANDBOX_ROOT says otherwise."""
    configured = os.environ.get("HW_SANDBOX_ROOT")
    return Path(configured) if configured else REPOSITORY_ROOT.parent / f"{REPOSITORY_ROOT.name}-sandboxes"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y%m%dT%H%M%S")


def _git_commit() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(REPOSITORY_ROOT), "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _git_dirty(paths: list[Path]) -> bool | None:
    try:
        relative = [str(path.relative_to(REPOSITORY_ROOT)) for path in paths]
        output = subprocess.run(["git", "-C", str(REPOSITORY_ROOT), "status", "--porcelain", "--", *relative],
                                check=True, capture_output=True, text=True).stdout
        return bool(output.strip())
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def _digests(root: Path, subdirs: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for subdir in subdirs:
        base = root / subdir
        if base.is_file():
            result[subdir] = sha256_file(base)
            continue
        for path in sorted(base.rglob("*")) if base.is_dir() else []:
            if path.is_file():
                result[str(path.relative_to(root))] = sha256_file(path)
    return result


def _make_read_only(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def _write(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_yaml(path: Path, document: dict[str, Any]) -> None:
    _write(path, yaml.safe_dump(document, sort_keys=False, allow_unicode=True))


@dataclass(frozen=True)
class Pilot:
    """A pilot directory and its `pilot.yaml` sandbox configuration."""

    root: Path
    config: dict[str, Any]

    @classmethod
    def load(cls, pilot: str | Path) -> "Pilot":
        root = Path(pilot)
        if not (root / "pilot.yaml").is_file():
            candidate = REPOSITORY_ROOT / "pilots" / str(pilot)
            root = candidate if (candidate / "pilot.yaml").is_file() else root
        config_path = root / "pilot.yaml"
        if not config_path.is_file():
            raise SandboxError(f"no pilot.yaml found for pilot {pilot!r}")
        return cls(root.resolve(), yaml.safe_load(config_path.read_text(encoding="utf-8")))

    @property
    def name(self) -> str:
        return str(self.config["pilot"])

    def path(self, key: str) -> Path:
        return (self.root / self.config[key]).resolve()

    def prompt(self, *keys: str) -> str:
        node: Any = self.config["prompts"]
        for key in keys:
            node = node[key]
        return (self.root / node).read_text(encoding="utf-8")

    def case(self, name: str) -> tuple[Path, dict[str, Any]]:
        path = self.path("cases") / f"{name}.yaml"
        if not path.is_file():
            raise SandboxError(f"case binding not found: {path}")
        return path, yaml.safe_load(path.read_text(encoding="utf-8"))


def select(document: Any, pointer: str) -> Any:
    """Follow a dotted selector such as `ATAM_Evaluation.evaluation_inputs`."""
    node = document
    for part in pointer.split("."):
        if not isinstance(node, dict) or part not in node:
            raise SandboxError(f"selector {pointer!r} does not resolve (missing {part!r})")
        node = node[part]
    return node


def _envelope(pointer: str, value: Any) -> Any:
    """Re-wrap a selected value in its original key path so consumers see the familiar shape."""
    for part in reversed(pointer.split(".")):
        value = {part: value}
    return value


def _claude_settings(writable: list[Path], readable: list[Path], denied_reads: list[Path], allow_bash: list[str]) -> str:
    """Permission rules for a sandboxed Claude Code session (absolute `//` paths)."""
    def rule(tool: str, path: Path) -> str:
        return f"{tool}(/{path.as_posix()}/**)"

    settings = {
        "permissions": {
            "allow": [*(rule("Read", path) for path in readable), *(rule(tool, path) for path in writable for tool in ("Edit", "Write")),
                      *(f"Bash({command})" for command in allow_bash)],
            "deny": [*(rule("Read", path) for path in denied_reads), "WebFetch", "WebSearch"],
        }
    }
    return json.dumps(settings, indent=2) + "\n"


def _build_skills_plugin(arm: str, destination: Path, include_langchain: bool) -> dict[str, Any]:
    """Wrap an arm's skills as a Claude Code plugin so every arm is installed the same way."""
    notes: dict[str, Any] = {"arm": arm, "langchain_skills": []}
    if arm == "harnessweaver":
        _write(destination / ".claude-plugin/plugin.json", json.dumps({
            "name": "harnessweaver",
            "version": "0.1.0-dev",
            "description": "HarnessWeaver generation skills: harness (design and materialize) and evolve (revise).",
            "license": "Apache-2.0",
        }, indent=2) + "\n")
        for skill in ("harness", "evolve"):
            shutil.copytree(SKILLS_DIR / skill, destination / "skills" / skill)
        if include_langchain:
            for skill in LANGCHAIN_SKILLS:
                source = LANGCHAIN_SKILLS_DIR / skill
                if source.is_dir():
                    shutil.copytree(source, destination / "skills" / skill)
                    notes["langchain_skills"].append(skill)
            notes["langchain_skills_missing"] = sorted(set(LANGCHAIN_SKILLS) - set(notes["langchain_skills"]))
        notes["source"] = str(SKILLS_DIR.relative_to(REPOSITORY_ROOT))
        notes["source_dirty"] = _git_dirty([SKILLS_DIR])
    elif arm == "revfactory-en":
        _verify_baseline()
        shutil.copytree(BASELINE_DIR / ".claude-plugin", destination / ".claude-plugin")
        shutil.copytree(BASELINE_DIR / "skills", destination / "skills")
        notes["source"] = str(BASELINE_DIR.relative_to(REPOSITORY_ROOT))
    else:
        raise SandboxError(f"unknown arm {arm!r}; expected one of {', '.join(ARMS)}")
    return notes


def _verify_baseline() -> None:
    """The baseline must match its recorded digests; an edited baseline invalidates comparisons."""
    for line in (BASELINE_DIR / "TRANSLATION.sha256").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split(maxsplit=1)
        if sha256_file(BASELINE_DIR / relative) != expected:
            raise SandboxError(f"baseline file changed since translation was recorded: {relative}")


GENERATION_RUN_SH = """#!/usr/bin/env bash
# Launch the generation session for this sandbox. See RUNBOOK.md.
set -euo pipefail
cd "$(dirname "$0")"
SESSION_ID="{session_id}"
MODEL="${{MODEL:-{model}}}"
ISOLATION="${{ISOLATION:-bare}}"   # bare: skip user hooks/settings/CLAUDE.md (needs ANTHROPIC_API_KEY); settings: project settings only
args=(--plugin-dir ./skills-plugin --settings ./claude-settings.json --session-id "$SESSION_ID")
if [ -n "$MODEL" ]; then args+=(--model "$MODEL"); fi
if [ "$ISOLATION" = "bare" ]; then args=(--bare "${{args[@]}}"); else args+=(--setting-sources project); fi
mkdir -p record
claude --version > record/claude-version.txt 2>&1 || true
printf '%s\\n' "$ISOLATION" > record/isolation.txt
printf '%s\\n' "${{MODEL:-<claude default>}}" > record/model-requested.txt
date -u +%Y-%m-%dT%H:%M:%SZ > record/started-at.txt
claude "${{args[@]}}" "$(cat prompt.md)"
date -u +%Y-%m-%dT%H:%M:%SZ > record/finished-at.txt
"""

GENERATION_RUNBOOK = """# Generation sandbox: {name}

Arm: **{arm}**. Pilot: **{pilot}**. Created {created} from repository commit `{commit}`.

You run this session; Claude Code with the arm's skills generates the harness. Everything runs in English.

## Before you start

- `cd {root}`
- With the default `ISOLATION=bare`, export `ANTHROPIC_API_KEY` (bare mode ignores OAuth login). It keeps your global hooks, plugins and `CLAUDE.md` out of the session. Use `ISOLATION=settings` to keep OAuth; it loads only this sandbox's settings, but your user-level `CLAUDE.md` may still load. Note which you used.
- Optionally set `MODEL` (default: {model_label}). Use the same model for every arm you compare.

## Run

```shell
./run.sh
```

The session starts with the request in `prompt.md`{answers_note}. Answer the skill's questions as you normally would; for a comparison with another arm, give equivalent answers to equivalent questions. Writes are allowed only under `generated/`. Reads of the repository are denied.

When the skill has finished, ask it to confirm where it wrote each file, then exit the session.

## Afterwards

From the repository root:

```shell
conda run -n harness hw sandbox collect {root} --label <label>
```

`collect` copies `generated/` into `pilots/{pilot}/generated/<label>/`, copies the session transcript (`~/.claude/projects/*/{session_id}.jsonl`) into the sandbox `record/`, writes `generation-record.json`, and runs `hw check-bundle` on any `build/claude/` and `build/deepagents/` it finds. Send back the label and anything you noticed: questions you were asked, files you had to fix by hand, and whether the session hit errors.
"""


def create_generation_sandbox(pilot_name: str | Path, arm: str, *, root: Path | None = None, model: str = "",
                              answers: Path | None = None, include_langchain_skills: bool = True) -> Path:
    """Create a sandbox in which the user runs a Claude Code generation session for one arm."""
    if arm not in ARMS:
        raise SandboxError(f"unknown arm {arm!r}; expected one of {', '.join(ARMS)}")
    if answers is not None and arm != "harnessweaver":
        raise SandboxError("harness-answers.yaml is a HarnessWeaver-skill feature; the baseline arm must be answered live")
    pilot = Pilot.load(pilot_name)
    created = _now()
    name = f"gen-{pilot.name}-{arm}-{_stamp(created)}"
    sandbox = _new_sandbox_dir(root, name)

    shutil.copytree(pilot.path("sources"), sandbox / "sources")
    plugin_notes = _build_skills_plugin(arm, sandbox / "skills-plugin", include_langchain_skills)
    (sandbox / "generated").mkdir()
    (sandbox / "record").mkdir()
    _write(sandbox / "prompt.md", pilot.prompt("generation"))
    if answers is not None:
        shutil.copyfile(answers, sandbox / "harness-answers.yaml")
    _make_read_only(sandbox / "sources")
    _make_read_only(sandbox / "skills-plugin")

    session_id = str(uuid4())
    commit = _git_commit()
    _write(sandbox / "claude-settings.json", _claude_settings(
        writable=[sandbox / "generated"],
        readable=[sandbox],
        denied_reads=[REPOSITORY_ROOT],
        allow_bash=["hw validate:*", "conda run -n harness hw validate:*", "hw check-bundle:*",
                    "conda run -n harness hw check-bundle:*", "mkdir -p generated/*", "ls:*"],
    ))
    _write(sandbox / "run.sh", GENERATION_RUN_SH.format(session_id=session_id, model=model), executable=True)
    _write(sandbox / "RUNBOOK.md", GENERATION_RUNBOOK.format(
        name=name, arm=arm, pilot=pilot.name, created=created.isoformat(timespec="seconds"),
        commit=commit or "unknown", root=sandbox, model_label=model or "the Claude Code default",
        session_id=session_id,
        answers_note=" and `harness-answers.yaml` (pre-recorded gate answers; the skill asks only what it leaves open)" if answers else "",
    ))
    _write_yaml(sandbox / SANDBOX_FILE, {
        "kind": "generation",
        "name": name,
        "pilot": pilot.name,
        "pilot_dir": str(pilot.root),
        "arm": arm,
        "created_at": created.isoformat(timespec="seconds"),
        "repository_commit": commit,
        "sources_dirty": _git_dirty([pilot.path("sources")]),
        "session_id": session_id,
        "model_requested": model or None,
        "skills": plugin_notes,
        "answers_file": answers is not None,
    })
    _write(sandbox / MANIFEST_FILE, json.dumps(
        {"inputs": _digests(sandbox, ["sources", "skills-plugin", "prompt.md", "harness-answers.yaml", "claude-settings.json"])},
        indent=2) + "\n")
    return sandbox


EXECUTION_RUN_SH = {
    "claude": """#!/usr/bin/env bash
# Run the generated Claude Code harness headlessly on this sandbox's case. See RUNBOOK.md.
set -euo pipefail
cd "$(dirname "$0")"
SESSION_ID="{session_id}"
MODEL="${{MODEL:-{model}}}"
ISOLATION="${{ISOLATION:-bare}}"
args=(-p --session-id "$SESSION_ID" --settings ../claude-settings.json --add-dir ../input --add-dir ../output
      --output-format stream-json --verbose)
if [ -n "$MODEL" ]; then args+=(--model "$MODEL"); fi
if [ "$ISOLATION" = "bare" ]; then
  args=(--bare "${{args[@]}}")
  # Bare mode skips CLAUDE.md discovery; pass the harness pointer explicitly.
  if [ -f workspace/CLAUDE.md ]; then args+=(--append-system-prompt-file CLAUDE.md); fi
else
  args+=(--setting-sources project)
fi
mkdir -p record output
claude --version > record/claude-version.txt 2>&1 || true
printf '%s\\n' "$ISOLATION" > record/isolation.txt
date -u +%Y-%m-%dT%H:%M:%SZ > record/started-at.txt
(cd workspace && claude "${{args[@]}}" "$(cat ../prompt.md)") > output/transcript.jsonl
date -u +%Y-%m-%dT%H:%M:%SZ > record/finished-at.txt
""",
    "deepagents": """#!/usr/bin/env bash
# Run the generated DeepAgents stages with the HarnessWeaver stage host. See RUNBOOK.md.
set -euo pipefail
cd "$(dirname "$0")"
MODEL="${{MODEL:-{model}}}"
TIMEOUT="${{TIMEOUT:-180}}"
HW_PYTHON="${{HW_PYTHON:-conda run --no-capture-output -n harness python}}"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
mkdir -p record output
date -u +%Y-%m-%dT%H:%M:%SZ > record/started-at.txt
$HW_PYTHON -m harnessweaver.hosts.deepagents --bundle bundle --input input --workspace workspace --out output \\
  --model "$MODEL" --timeout "$TIMEOUT" "$@"
date -u +%Y-%m-%dT%H:%M:%SZ > record/finished-at.txt
""",
}

EXECUTION_RUNBOOK = """# Execution sandbox: {name}

Target: **{target}**. Pilot: **{pilot}**. Case: **{case}**. Bundle: `{bundle}`.

`input/` holds only the case's generation inputs ({inputs}). Evaluator-only data was not copied.

## Run

```shell
cd {root}
{run_hint}
```

## Afterwards

From the repository root:

```shell
conda run -n harness hw check {root}
conda run -n harness hw sandbox record {root}
```

`check` writes `check.json` next to this file; `record` copies the sandbox record, outputs and check result into `docs/cain-2027/evidence/{name}/`.
"""

RUN_HINTS = {
    "claude": ("./run.sh    # you run this one; export ANTHROPIC_API_KEY for the default ISOLATION=bare, "
               "or use ISOLATION=settings"),
    "deepagents": "./run.sh    # provider keys come from the environment or a .env file placed in this directory",
}


def create_execution_sandbox(pilot_name: str | Path, target: str, bundle: Path, case: str, *,
                             root: Path | None = None, model: str = "") -> Path:
    """Create a sandbox that runs one generated bundle on one case with generation inputs only."""
    if target not in TARGETS:
        raise SandboxError(f"unknown target {target!r}; expected one of {', '.join(TARGETS)}")
    if target == "deepagents" and not model:
        raise SandboxError("a DeepAgents execution needs --model (for example openai:gpt-5.4-mini)")
    pilot = Pilot.load(pilot_name)
    bundle = Path(bundle).resolve()
    if not bundle.is_dir():
        raise SandboxError(f"bundle not found: {bundle}")
    case_path, binding = pilot.case(case)
    created = _now()
    name = f"run-{pilot.name}-{target}-{case}-{_stamp(created)}"
    sandbox = _new_sandbox_dir(root, name)

    shutil.copytree(bundle, sandbox / "bundle")
    _make_read_only(sandbox / "bundle")
    input_dir = sandbox / "input"
    input_dir.mkdir()
    input_ids = []
    for item in binding.get("generation_inputs") or []:
        if "value" in item:
            value = item["value"]
            document = _envelope(item["envelope"], value) if item.get("envelope") else value
        else:
            source = (case_path.parent / item["from"]).resolve()
            value = select(json.loads(source.read_text(encoding="utf-8")), item["select"])
            document = _envelope(item["select"], value)
        _write(input_dir / f"{item['id']}.json", json.dumps(document, indent=2, ensure_ascii=False) + "\n")
        input_ids.append(item["id"])
    _make_read_only(input_dir)
    (sandbox / "output").mkdir()
    (sandbox / "record").mkdir()
    if target == "claude":
        # The generated project is the working directory; it may write its own _workspace/.
        shutil.copytree(bundle, sandbox / "workspace")
        first_input = f"../input/{input_ids[0]}.json" if input_ids else "../input/"
        _write(sandbox / "prompt.md", pilot.prompt("execution", "claude").format(
            input=first_input, output=f"../output/{CLAUDE_REPORT_FILENAME}"))
        _write(sandbox / "claude-settings.json", _claude_settings(
            writable=[sandbox / "workspace", sandbox / "output"],
            readable=[sandbox / "workspace", sandbox / "input"],
            denied_reads=[REPOSITORY_ROOT],
            allow_bash=[],
        ))
    else:
        (sandbox / "workspace").mkdir()

    session_id = str(uuid4()) if target == "claude" else None
    _write(sandbox / "run.sh", EXECUTION_RUN_SH[target].format(session_id=session_id, model=model), executable=True)
    _write(sandbox / "RUNBOOK.md", EXECUTION_RUNBOOK.format(
        name=name, target=target, pilot=pilot.name, case=case, bundle=bundle, inputs=", ".join(input_ids) or "none",
        root=sandbox, run_hint=RUN_HINTS[target]))
    _write_yaml(sandbox / SANDBOX_FILE, {
        "kind": "execution",
        "name": name,
        "pilot": pilot.name,
        "pilot_dir": str(pilot.root),
        "target": target,
        "case": case,
        "case_binding": str(case_path),
        "bundle_source": str(bundle),
        "created_at": created.isoformat(timespec="seconds"),
        "repository_commit": _git_commit(),
        "session_id": session_id,
        "model_requested": model or None,
    })
    _write(sandbox / MANIFEST_FILE, json.dumps({"inputs": _digests(sandbox, ["bundle", "input", "prompt.md"])}, indent=2) + "\n")
    return sandbox


def load_sandbox(sandbox: str | Path) -> tuple[Path, dict[str, Any]]:
    path = Path(sandbox).resolve()
    meta_path = path / SANDBOX_FILE
    if not meta_path.is_file():
        raise SandboxError(f"not a sandbox (no {SANDBOX_FILE}): {path}")
    return path, yaml.safe_load(meta_path.read_text(encoding="utf-8"))


def _find_transcript(session_id: str, projects_dir: Path | None = None) -> Path | None:
    base = projects_dir or Path.home() / ".claude/projects"
    matches = sorted(base.glob(f"*/{session_id}.jsonl")) if base.is_dir() else []
    return matches[0] if matches else None


def collect_generation(sandbox: str | Path, label: str, *, projects_dir: Path | None = None,
                       destination_root: Path | None = None) -> Path:
    """Copy a finished generation into the pilot and record how it was produced."""
    from harnessweaver.bundles import check_bundle

    path, meta = load_sandbox(sandbox)
    if meta.get("kind") != "generation":
        raise SandboxError(f"{path} is not a generation sandbox")
    generated = path / "generated"
    if not generated.is_dir() or not any(generated.iterdir()):
        raise SandboxError(f"nothing was generated in {generated}")
    destination = (destination_root or Path(meta["pilot_dir"]) / "generated") / label
    if destination.exists():
        raise SandboxError(f"label already used: {destination}")

    transcript = path / "record/transcript.jsonl"
    if not transcript.is_file():
        found = _find_transcript(meta["session_id"], projects_dir)
        if found:
            shutil.copyfile(found, transcript)
    shutil.copytree(generated, destination)
    if transcript.is_file():
        (destination / "record").mkdir(exist_ok=True)
        shutil.copyfile(transcript, destination / "record/transcript.jsonl")

    spec_candidates = sorted(destination.glob("**/harnessspec*.yaml"))
    bundle_checks: dict[str, Any] = {}
    for target in TARGETS:
        for bundle in sorted(destination.glob(f"**/build/{target}")):
            spec = spec_candidates[0] if spec_candidates else None
            issues = check_bundle(target, bundle, spec)
            bundle_checks[str(bundle.relative_to(destination))] = {
                "target": target, "spec": str(spec.relative_to(destination)) if spec else None,
                "passed": not issues, "issues": [str(issue) for issue in issues]}
    record_dir = path / "record"
    record = {
        "label": label,
        "collected_at": _now().isoformat(timespec="seconds"),
        "sandbox": meta,
        "record_files": {name.name: name.read_text(encoding="utf-8").strip() for name in sorted(record_dir.glob("*.txt"))},
        "transcript": "record/transcript.jsonl" if transcript.is_file() else None,
        "inputs": json.loads((path / MANIFEST_FILE).read_text(encoding="utf-8"))["inputs"],
        "outputs": _digests(path, ["generated"]),
        "specs": [str(spec.relative_to(destination)) for spec in spec_candidates],
        "bundle_checks": bundle_checks,
    }
    _write(destination / "generation-record.json", json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return destination


def record_execution(sandbox: str | Path, *, evidence_root: Path | None = None) -> Path:
    """Copy an execution sandbox's record, outputs, intermediate artifacts and check into the evidence package."""
    path, meta = load_sandbox(sandbox)
    if meta.get("kind") != "execution":
        raise SandboxError(f"{path} is not an execution sandbox")
    destination = (evidence_root or EVIDENCE_DIR) / meta["name"]
    if destination.exists():
        raise SandboxError(f"already recorded: {destination}")
    destination.mkdir(parents=True)
    for name in (SANDBOX_FILE, "check.json", "prompt.md", "RUNBOOK.md"):
        if (path / name).is_file():
            shutil.copyfile(path / name, destination / name)
    for subdir in ("output", "record"):
        if (path / subdir).is_dir():
            shutil.copytree(path / subdir, destination / subdir)
    for intermediate in ("workspace/artifacts", "workspace/_workspace"):
        if (path / intermediate).is_dir():
            shutil.copytree(path / intermediate, destination / intermediate)
    manifest = json.loads((path / MANIFEST_FILE).read_text(encoding="utf-8"))
    manifest["outputs"] = _digests(path, ["output", "workspace/artifacts", "workspace/_workspace"])
    manifest["recorded_at"] = _now().isoformat(timespec="seconds")
    _write(destination / MANIFEST_FILE, json.dumps(manifest, indent=2) + "\n")
    return destination
