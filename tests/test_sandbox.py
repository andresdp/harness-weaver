import json
import stat
import tempfile
import unittest
from pathlib import Path

import yaml

from harnessweaver.bundles import check_bundle
from harnessweaver.checks import run_checks
from harnessweaver.cli import main
from harnessweaver.hosts.deepagents import run_stages
from harnessweaver.sandbox import (
    SandboxError,
    collect_generation,
    create_execution_sandbox,
    create_generation_sandbox,
    record_execution,
)
from tests import test_atam_demo
from tests.test_stage_host import write_bundle

ROOT = Path(__file__).resolve().parents[1]
BANKING = ROOT / "case-studies/architecture-eval/ATAM/data/banking.json"
SPEC = {
    "spec_version": "0.2",
    "id": "demo",
    "stages": [{"id": "establish-context"}, {"id": "synthesize-report"}],
    "roles": [{"id": "facilitator"}],
    "artifacts": [{"id": "atam-report"}],
    "verification": [{"id": "output-shape"}],
    "human_gates": [{"id": "expert-review"}],
}


def write_report(bundle: Path, ids: list[str]) -> None:
    rows = "".join(f"| {element} | ... | ... | mapped | |\n" for element in ids)
    (bundle / "materialization-report.md").write_text("# Materialization report\n\n| Spec element |\n|---|\n" + rows)


def write_claude_bundle(root: Path) -> Path:
    bundle = root / "claude"
    (bundle / ".claude/agents").mkdir(parents=True)
    (bundle / ".claude/skills/atam-orchestrator").mkdir(parents=True)
    (bundle / ".claude/agents/qa-analyst.md").write_text("---\nname: qa-analyst\ndescription: Analyze scenarios.\n---\nBody\n")
    (bundle / ".claude/skills/atam-orchestrator/SKILL.md").write_text(
        '---\nname: atam-orchestrator\ndescription: Run the ATAM harness.\n---\nCall Agent with subagent_type: "qa-analyst".\n')
    (bundle / "CLAUDE.md").write_text("## Harness: ATAM\n")
    return bundle


class BundleCheckTests(unittest.TestCase):
    def test_well_formed_bundles_pass_for_both_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "harnessspec.yaml"
            spec_path.write_text(yaml.safe_dump(SPEC))
            ids = ["establish-context", "synthesize-report", "facilitator", "atam-report", "output-shape", "expert-review"]
            claude = write_claude_bundle(root)
            write_report(claude, ids)
            deepagents = write_bundle(root)
            write_report(deepagents, ids)
            self.assertEqual(check_bundle("claude", claude, spec_path), [])
            self.assertEqual(check_bundle("deepagents", deepagents, spec_path), [])

    def test_claude_rules_each_reject_a_broken_bundle(self):
        breakages = {
            "frontmatter must define name": lambda b: (b / ".claude/agents/qa-analyst.md").write_text("no frontmatter\n"),
            "command files must not be generated": lambda b: ((b / ".claude/commands").mkdir(), (b / ".claude/commands/x.md").write_text("x")),
            "'TeamCreate'": lambda b: (b / "CLAUDE.md").write_text("Use TeamCreate here.\n"),
            "undefined agent type 'ghost'": lambda b: (b / "CLAUDE.md").write_text('subagent_type: "ghost"\n'),
            "missing harness pointer": lambda b: (b / "CLAUDE.md").unlink(),
            "materialization-report.md: missing": lambda b: (b / "materialization-report.md").unlink(),
        }
        for expected, breakage in breakages.items():
            with self.subTest(expected), tempfile.TemporaryDirectory() as tmp:
                bundle = write_claude_bundle(Path(tmp))
                write_report(bundle, [])
                breakage(bundle)
                self.assertIn(expected, " ".join(str(issue) for issue in check_bundle("claude", bundle)))

    def test_deepagents_rules_each_reject_a_broken_bundle(self):
        breakages = {
            "completion protocol does not list 01_context.json":
                lambda b: (b / "stage1-context/AGENTS.md").write_text("# Agent\nDo not continue.\n"),
            "refers to 07_ghost.json":
                lambda b: (b / "stage1-context/AGENTS.md").write_text("# Agent\nDo not continue. Write 01_context.json, read 07_ghost.json.\n"),
            "'SendMessage'":
                lambda b: (b / "stage2-report/skills/report-task/SKILL.md").write_text("---\nname: r\ndescription: d\n---\nSendMessage to peer.\n"),
            "not a valid JSON Schema":
                lambda b: (b / "contracts/report.schema.json").write_text(json.dumps({"type": 7})),
            "missing a scope-boundary section":
                lambda b: (b / "stage2-report/AGENTS.md").write_text("# Agent\n- /artifacts/02_report.json\n"),
            "wiring.yaml":
                lambda b: (b / "wiring.yaml").write_text("wiring_version: '0.1'\n"),
        }
        for expected, breakage in breakages.items():
            with self.subTest(expected), tempfile.TemporaryDirectory() as tmp:
                bundle = write_bundle(Path(tmp))
                write_report(bundle, [])
                breakage(bundle)
                self.assertIn(expected, " ".join(str(issue) for issue in check_bundle("deepagents", bundle)))

    def test_report_must_account_for_every_spec_element(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "harnessspec.yaml"
            spec_path.write_text(yaml.safe_dump(SPEC))
            bundle = write_claude_bundle(root)
            write_report(bundle, ["establish-context"])
            text = " ".join(str(issue) for issue in check_bundle("claude", bundle, spec_path))
            for missing in ("synthesize-report", "facilitator", "atam-report", "output-shape", "expert-review"):
                self.assertIn(missing, text)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = write_claude_bundle(Path(tmp))
            write_report(bundle, [])
            self.assertEqual(main(["check-bundle", str(bundle), "--target", "claude"]), 0)
            (bundle / "CLAUDE.md").unlink()
            self.assertEqual(main(["check-bundle", str(bundle), "--target", "claude"]), 1)
        self.assertEqual(main(["validate", str(ROOT / "pilots/atam/harnessspec-v0.2.yaml")]), 0)


class GenerationSandboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_harnessweaver_arm_has_read_only_sources_skills_plugin_and_locked_settings(self):
        box = create_generation_sandbox("atam", "harnessweaver", root=self.root, model="claude-test")
        for relative in ("sources/intent.yaml", "skills-plugin/.claude-plugin/plugin.json", "skills-plugin/skills/harness/SKILL.md",
                         "skills-plugin/skills/evolve/SKILL.md", "prompt.md", "run.sh", "RUNBOOK.md", "sandbox.yaml", "manifest.json"):
            self.assertTrue((box / relative).is_file(), relative)
        self.assertFalse((box / "sources/intent.yaml").stat().st_mode & stat.S_IWUSR)
        self.assertTrue((box / "generated").is_dir())
        settings = json.loads((box / "claude-settings.json").read_text())
        self.assertIn(f"Read(/{ROOT.as_posix()}/**)", settings["permissions"]["deny"])
        self.assertIn(f"Write(/{(box / 'generated').as_posix()}/**)", settings["permissions"]["allow"])
        meta = yaml.safe_load((box / "sandbox.yaml").read_text())
        run_sh = (box / "run.sh").read_text()
        self.assertIn(meta["session_id"], run_sh)
        self.assertIn("--plugin-dir ./skills-plugin", run_sh)
        self.assertIn('MODEL="${MODEL:-claude-test}"', run_sh)
        # Sources are copied verbatim, so the sandbox reflects exactly what the pilot authored.
        self.assertEqual((box / "prompt.md").read_text(), (ROOT / "pilots/atam/prompts/generation.md").read_text())

    def test_baseline_arm_uses_the_verified_english_translation_and_refuses_answer_files(self):
        box = create_generation_sandbox("atam", "revfactory-en", root=self.root)
        plugin = json.loads((box / "skills-plugin/.claude-plugin/plugin.json").read_text())
        self.assertEqual(plugin["name"], "harness")
        self.assertIn("Designs a harness suited to the project", (box / "skills-plugin/skills/harness/SKILL.md").read_text())
        answers = self.root / "answers.yaml"
        answers.write_text("answers_version: '0.1'\n")
        with self.assertRaises(SandboxError):
            create_generation_sandbox("atam", "revfactory-en", root=self.root / "other", answers=answers)

    def test_sandboxes_inside_the_repository_are_refused(self):
        with self.assertRaises(SandboxError):
            create_generation_sandbox("atam", "harnessweaver", root=ROOT / "tmp-sandboxes")
        self.assertFalse((ROOT / "tmp-sandboxes").exists())

    def test_collect_copies_generated_files_transcript_and_bundle_checks(self):
        box = create_generation_sandbox("atam", "harnessweaver", root=self.root)
        generated = box / "generated"
        (generated / "harnessspec.yaml").write_text(yaml.safe_dump(SPEC))
        (generated / "build").mkdir()
        bundle = write_bundle(generated / "build")
        bundle.rename(generated / "build/deepagents")
        write_report(generated / "build/deepagents", ["establish-context"])
        projects = self.root / "projects/some-project"
        projects.mkdir(parents=True)
        session_id = yaml.safe_load((box / "sandbox.yaml").read_text())["session_id"]
        (projects / f"{session_id}.jsonl").write_text('{"type": "user"}\n')

        destination = collect_generation(box, "hw-1", projects_dir=self.root / "projects", destination_root=self.root / "collected")
        record = json.loads((destination / "generation-record.json").read_text())
        self.assertEqual(record["transcript"], "record/transcript.jsonl")
        self.assertTrue((destination / "record/transcript.jsonl").is_file())
        check = record["bundle_checks"]["build/deepagents"]
        self.assertFalse(check["passed"])  # the report does not cover every spec element
        self.assertIn("facilitator", " ".join(check["issues"]))
        with self.assertRaises(SandboxError):
            collect_generation(box, "hw-1", projects_dir=self.root / "projects", destination_root=self.root / "collected")


class ExecutionSandboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def deepagents_bundle(self) -> Path:
        bundle = write_bundle(self.root / "gen")
        # Use the real ATAM report contract for the final artifact.
        schema = ROOT / "pilots/atam/sources/domain/contracts/atam-report.schema.json"
        (bundle / "contracts/report.schema.json").write_text(schema.read_text())
        return bundle

    def test_inputs_hold_only_generation_data_and_checks_run_from_outside(self):
        box = create_execution_sandbox("atam", "deepagents", self.deepagents_bundle(), "banking",
                                       root=self.root, model="openai:test")
        payload = json.loads((box / "input/architecture-context.json").read_text())
        self.assertEqual(list(payload), ["ATAM_Evaluation"])
        self.assertEqual(list(payload["ATAM_Evaluation"]), ["evaluation_inputs"])
        self.assertNotIn("ground_truth_outputs", (box / "input/architecture-context.json").read_text())
        self.assertIn("--model \"$MODEL\"", (box / "run.sh").read_text())

        report = test_atam_demo.AtamDemoTests()._compose_sample_report().model_dump(mode="json", by_alias=True)
        outputs = {
            "stage1-context": {"artifacts/01_context.json": "{}"},
            "stage2-report": {"artifacts/02_report.json": json.dumps(report)},
        }
        from tests.test_stage_host import fake_factory
        result = run_stages(box / "bundle", box / "input", box / "workspace", box / "output", fake_factory(outputs, []))
        self.assertEqual(result.status, "awaiting_review")

        summary = run_checks(box)
        self.assertTrue(summary["checks"]["no-reference-leakage"]["passed"], summary)
        self.assertTrue(summary["checks"]["schema"]["passed"], summary)
        # The ATAM checker requires analysis records that cite banking scenarios; the sample does not.
        self.assertFalse(summary["checks"]["atam-pilot"]["passed"])
        self.assertEqual(summary["report"], "output/02_report.json")
        self.assertTrue((box / "check.json").is_file())

        evidence = record_execution(box, evidence_root=self.root / "evidence")
        for relative in ("sandbox.yaml", "check.json", "manifest.json", "output/host-record.json", "workspace/artifacts/02_report.json"):
            self.assertTrue((evidence / relative).is_file(), relative)

    def test_leakage_check_detects_evaluator_only_passages(self):
        box = create_execution_sandbox("atam", "deepagents", self.deepagents_bundle(), "banking",
                                       root=self.root, model="openai:test")
        reference = json.loads(BANKING.read_text())["ATAM_Evaluation"]["ground_truth_outputs"]
        from harnessweaver.checks import _strings
        passage = next(text for text in _strings(reference) if len(text) >= 80)
        (box / "workspace/notes.txt").write_text(f"copied: {passage}")
        summary = run_checks(box)
        self.assertFalse(summary["checks"]["no-reference-leakage"]["passed"])
        self.assertIn("workspace/notes.txt", summary["checks"]["no-reference-leakage"]["problems"][0])

    def test_claude_target_copies_the_project_into_a_writable_workspace(self):
        claude = write_claude_bundle(self.root)
        box = create_execution_sandbox("atam", "claude", claude, "banking", root=self.root)
        self.assertTrue((box / "workspace/CLAUDE.md").is_file())
        self.assertFalse((box / "bundle/CLAUDE.md").stat().st_mode & stat.S_IWUSR)
        prompt = (box / "prompt.md").read_text()
        self.assertIn("../input/architecture-context.json", prompt)
        self.assertIn("../output/report.json", prompt)
        settings = json.loads((box / "claude-settings.json").read_text())
        self.assertIn(f"Write(/{(box / 'output').as_posix()}/**)", settings["permissions"]["allow"])
        self.assertIn("--output-format stream-json", (box / "run.sh").read_text())

    def test_deepagents_execution_requires_a_model(self):
        with self.assertRaises(SandboxError):
            create_execution_sandbox("atam", "deepagents", self.deepagents_bundle(), "banking", root=self.root)


if __name__ == "__main__":
    unittest.main()
