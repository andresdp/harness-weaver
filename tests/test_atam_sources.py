import json
import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from pilots.atam.deepagents.atam_harness.schema_export import report_json_schema
from tests import test_atam_demo


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots/atam"
SOURCES = PILOT / "sources"
REPORT_SCHEMA = SOURCES / "domain/contracts/atam-report.schema.json"

# Runtime constructs that must stay out of authored sources (APPROACH §2).
RUNTIME_TOKENS = ("subagent_type", "SendMessage", "create_deep_agent", "TaskCreate", ".claude/", "agentType", "Workflow(")


class AtamSourcesTests(unittest.TestCase):
    def test_report_schema_file_matches_the_pydantic_contract(self):
        # The committed schema is generated from the report model; regenerate it when the model changes.
        committed = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(committed, report_json_schema())

    def test_report_schema_accepts_a_composed_report_and_rejects_ground_truth(self):
        # The exported contract must accept what the reference runner writes and forbid reference outputs.
        validator = Draft202012Validator(json.loads(REPORT_SCHEMA.read_text(encoding="utf-8")))
        report = test_atam_demo.AtamDemoTests()._compose_sample_report().model_dump(mode="json", by_alias=True)
        self.assertEqual(list(validator.iter_errors(report)), [])
        report["ATAM_Evaluation"]["ground_truth_outputs"] = {}
        self.assertTrue(list(validator.iter_errors(report)))

    def test_sources_have_the_authored_layout(self):
        for relative in (
            "intent.yaml",
            "methodology.yaml",
            "domain/sources.yaml",
            "domain/skills/evaluate-architecture/SKILL.md",
            "domain/skills/check-evaluation/SKILL.md",
            "domain/contracts/atam-report.schema.json",
            "domain/references/atam-report-template.json",
        ):
            self.assertTrue((SOURCES / relative).is_file(), relative)
        intent = yaml.safe_load((SOURCES / "intent.yaml").read_text(encoding="utf-8"))
        for field in ("goal", "scope", "exclusions", "intended_user", "decision_supported", "human_review", "target_runtimes"):
            self.assertIn(field, intent)

    def test_sources_contain_no_runtime_constructs_or_case_data(self):
        # Sources describe the work, not a runtime; case files are bound only at run time.
        for path in SOURCES.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for token in RUNTIME_TOKENS:
                self.assertNotIn(token, text, f"{path.relative_to(ROOT)} contains runtime construct {token!r}")
            self.assertIsNone(re.search(r"ATAM/data/[\w-]+\.json", text), f"{path.relative_to(ROOT)} references case data")

    def test_source_references_resolve(self):
        index = yaml.safe_load((SOURCES / "domain/sources.yaml").read_text(encoding="utf-8"))
        self.assertTrue(index["sources"])
        for entry in index["sources"]:
            for field in ("id", "ref", "kind", "authority"):
                self.assertIn(field, entry, entry.get("id"))
            target = (SOURCES / "domain" / entry["ref"]).resolve()
            self.assertTrue(target.exists(), f"{entry['id']}: {entry['ref']}")

    def test_reference_realizations_carry_the_authored_methodology(self):
        # Hand-written realizations keep copies of the single authored method; only relative paths may differ.
        def method_content(path: Path) -> dict:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            document.pop("sources")
            document["report_contract"].pop("ref")
            return document

        authored = method_content(SOURCES / "methodology.yaml")
        copies = sorted(PILOT.glob("*/skills/*/references/atam-methodology.yaml"))
        self.assertTrue(copies)
        for copy in copies:
            self.assertEqual(method_content(copy), authored, str(copy.relative_to(ROOT)))

    def test_banking_case_binding_separates_generation_and_evaluator_inputs(self):
        binding = yaml.safe_load((PILOT / "cases/banking.yaml").read_text(encoding="utf-8"))
        self.assertEqual(binding["case"], "banking")
        generation = binding["generation_inputs"]
        evaluator = binding["evaluator_only"]
        self.assertEqual([item["select"] for item in generation], ["ATAM_Evaluation.evaluation_inputs"])
        self.assertEqual([item["select"] for item in evaluator], ["ATAM_Evaluation.ground_truth_outputs"])
        for item in [*generation, *evaluator]:
            self.assertTrue((PILOT / "cases" / item["from"]).resolve().is_file(), item["from"])


if __name__ == "__main__":
    unittest.main()
