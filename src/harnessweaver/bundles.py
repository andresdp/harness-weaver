"""Structural checks for generated runtime bundles (`hw check-bundle`).

These checks automate the target references' checklists. They prove structure only:
a bundle that passes still has to run, and its outputs still have to be evaluated.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from harnessweaver.spec import SpecLoadError, ValidationIssue, load_spec
from harnessweaver.wiring import WiringError, load_wiring

TARGETS = ("claude", "deepagents")
MAX_BODY_LINES = 500
REPORT_FILENAME = "materialization-report.md"
BUILTIN_CLAUDE_AGENT_TYPES = {"general-purpose", "Explore", "Plan", "statusline-setup", "claude-code-guide"}
V1_CLAUDE_TOKENS = ("TeamCreate", "TeamDelete", "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "team_name")
CLAUDE_ONLY_TOKENS = ("SendMessage", "subagent_type", "agentType", ".claude/", "TeamCreate", "Workflow(", "model: opus")
ARTIFACT_MENTION = re.compile(r"\b\d{2}_[A-Za-z0-9_.-]+\.json\b")


def _frontmatter(path: Path) -> tuple[dict[str, Any] | None, str]:
    """Return (frontmatter, body) of a Markdown file; frontmatter is None when absent or invalid."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not match:
        return None, text
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None, match.group(2)
    return (data if isinstance(data, dict) else None), match.group(2)


def _check_skill(path: Path, root: Path, issues: list[ValidationIssue]) -> dict[str, Any] | None:
    where = str(path.relative_to(root))
    meta, body = _frontmatter(path)
    if meta is None or not meta.get("name") or not meta.get("description"):
        issues.append(ValidationIssue(where, "frontmatter must define name and description"))
    if body.count("\n") > MAX_BODY_LINES:
        issues.append(ValidationIssue(where, f"body exceeds {MAX_BODY_LINES} lines; move detail into references/"))
    return meta


def _forbid_tokens(root: Path, tokens: tuple[str, ...], reason: str, issues: list[ValidationIssue]) -> None:
    for path in sorted(root.rglob("*.md")):
        if path.name == REPORT_FILENAME:
            continue  # the fidelity report may name constructs it did not carry over
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token in text:
                issues.append(ValidationIssue(str(path.relative_to(root)), f"contains {token!r} ({reason})"))


def _spec_element_ids(spec: dict[str, Any]) -> list[tuple[str, str]]:
    elements: list[tuple[str, str]] = []
    for section, kind in (("stages", "stage"), ("roles", "role"), ("artifacts", "artifact"),
                          ("verification", "verification"), ("human_gates", "human gate")):
        for entry in spec.get(section) or []:
            if isinstance(entry, dict) and entry.get("id"):
                elements.append((kind, str(entry["id"])))
    return elements


def _check_report(root: Path, spec_path: Path | None, issues: list[ValidationIssue]) -> None:
    report = root / REPORT_FILENAME
    if not report.is_file():
        issues.append(ValidationIssue(REPORT_FILENAME, "missing; every target must write its fidelity record"))
        return
    if spec_path is None:
        return
    try:
        spec = load_spec(spec_path)
    except SpecLoadError as exc:
        issues.append(ValidationIssue("--spec", str(exc)))
        return
    text = report.read_text(encoding="utf-8")
    for kind, element_id in _spec_element_ids(spec):
        if element_id not in text:
            issues.append(ValidationIssue(REPORT_FILENAME, f"does not account for {kind} {element_id!r} (a missing row counts as unsupported)"))


def _check_claude(root: Path, issues: list[ValidationIssue]) -> None:
    agents_dir, skills_dir = root / ".claude/agents", root / ".claude/skills"
    agent_names: set[str] = set()
    for path in sorted(agents_dir.glob("*.md")):
        meta = _check_skill(path, root, issues)
        if meta and meta.get("name"):
            agent_names.add(str(meta["name"]))
    skills = sorted(skills_dir.glob("*/SKILL.md"))
    if not skills:
        issues.append(ValidationIssue(".claude/skills", "no skills found; expected domain skills and an orchestrator skill"))
    for path in skills:
        _check_skill(path, root, issues)
    if not (root / "CLAUDE.md").is_file():
        issues.append(ValidationIssue("CLAUDE.md", "missing harness pointer (trigger conditions and change history)"))
    commands = root / ".claude/commands"
    if commands.is_dir() and any(commands.iterdir()):
        issues.append(ValidationIssue(".claude/commands", "command files must not be generated"))
    _forbid_tokens(root, V1_CLAUDE_TOKENS, "v1 artifact that the current runtime does not support", issues)
    reference = re.compile(r"""(?:subagent_type|agentType)\s*[:=]\s*["']([^"'{}]+)["']""")
    for path in sorted(root.rglob("*.md")):
        for name in reference.findall(path.read_text(encoding="utf-8")):
            if name not in agent_names and name not in BUILTIN_CLAUDE_AGENT_TYPES:
                issues.append(ValidationIssue(str(path.relative_to(root)), f"references undefined agent type {name!r}"))


def _check_deepagents(root: Path, issues: list[ValidationIssue]) -> None:
    try:
        wiring = load_wiring(root)
    except WiringError as exc:
        issues.extend(ValidationIssue(f"wiring.yaml: {issue.location}", issue.message) for issue in exc.issues)
        return
    known = {item.path.name for item in wiring.inputs}
    for stage in wiring.stages:
        stage_dir = root / stage.dir
        agents_md = stage_dir / "AGENTS.md"
        if not agents_md.is_file():
            issues.append(ValidationIssue(stage.dir, "missing AGENTS.md"))
            continue
        skills = sorted(stage_dir.glob("skills/*/SKILL.md"))
        if not skills:
            issues.append(ValidationIssue(stage.dir, "no skills/<task>/SKILL.md found"))
        for path in skills:
            _check_skill(path, root, issues)
        text = agents_md.read_text(encoding="utf-8")
        if text.count("\n") > MAX_BODY_LINES:
            issues.append(ValidationIssue(f"{stage.dir}/AGENTS.md", f"exceeds {MAX_BODY_LINES} lines"))
        for artifact in stage.artifacts:
            if artifact not in text:
                issues.append(ValidationIssue(f"{stage.dir}/AGENTS.md", f"completion protocol does not list {artifact}"))
        known.update(stage.artifacts)
        mentioned = set(ARTIFACT_MENTION.findall(text))
        for path in skills:
            mentioned.update(ARTIFACT_MENTION.findall(path.read_text(encoding="utf-8")))
        for name in sorted(mentioned - known):
            issues.append(ValidationIssue(stage.dir, f"refers to {name}, which no earlier stage or input produces"))
        if not re.search(r"scope|do not", text, re.IGNORECASE):
            issues.append(ValidationIssue(f"{stage.dir}/AGENTS.md", "missing a scope-boundary section"))
    schema_refs = {ref for stage in wiring.stages for ref in stage.schemas.values()}
    if wiring.output_schema:
        schema_refs.add(wiring.output_schema)
    for ref in sorted(schema_refs):
        path = root / ref
        if not path.is_file():
            issues.append(ValidationIssue(ref, "schema file not found in the bundle"))
            continue
        try:
            Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, SchemaError) as exc:
            issues.append(ValidationIssue(ref, f"not a valid JSON Schema: {exc}"))
    _forbid_tokens(root, CLAUDE_ONLY_TOKENS, "Claude Code construct with no DeepAgents equivalent", issues)


def check_bundle(target: str, bundle: str | Path, spec_path: str | Path | None = None) -> list[ValidationIssue]:
    """Return every structural problem in a generated bundle for the given target."""
    if target not in TARGETS:
        raise ValueError(f"unknown target {target!r}; expected one of {', '.join(TARGETS)}")
    root = Path(bundle)
    if not root.is_dir():
        return [ValidationIssue(str(root), "bundle directory not found")]
    issues: list[ValidationIssue] = []
    (_check_claude if target == "claude" else _check_deepagents)(root, issues)
    _check_report(root, Path(spec_path) if spec_path else None, issues)
    return issues
