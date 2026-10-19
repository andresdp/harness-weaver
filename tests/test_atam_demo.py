import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from examples.atam.deepagents.atam_harness.agents import load_subagents
from examples.atam.deepagents.atam_harness.config import (
    ResolvedRunConfig,
    build_parser,
    format_resolved_settings,
    resolve_config,
)
from examples.atam.deepagents.atam_harness.execution import execute_agent
from examples.atam.deepagents.atam_harness.models import (
    AtamCaseInputs,
    AtamEvaluationResults,
    AtamMetadata,
    AtamReportContent,
    AtamReportDocument,
    AtamReportPayload,
)
from examples.atam.deepagents.atam_harness.prompts import build_task_prompt
from examples.atam.deepagents.atam_harness.progress import format_tool_args
from examples.atam.deepagents.atam_harness.reports import (
    compose_report,
    load_case,
    session_output_path,
    validate_report,
    write_report,
)


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "case-studies/architecture-eval/ATAM/data/banking.json"
REPORT_TEMPLATE = ROOT / "examples/atam/report-template.json"


class AtamDemoTests(unittest.TestCase):
    def test_generation_prompt_contains_only_evaluation_inputs(self):
        # Reference outputs are held back to avoid leaking expected answers into generation.
        case = load_case(CASE)
        source_case = json.loads(CASE.read_text(encoding="utf-8"))
        reference_outputs = source_case["ATAM_Evaluation"]["ground_truth_outputs"]
        prompt = build_task_prompt(case.evaluation_inputs)

        self.assertIn(case.evaluation_inputs["system_description"], prompt)
        self.assertNotIn("ground_truth_outputs", prompt)
        self.assertNotIn(json.dumps(reference_outputs, indent=2), prompt)

    def test_report_validator_uses_typed_report_contract(self):
        # Required sections and forbidden reference fields are enforced by Pydantic.
        report = self._compose_sample_report()
        self.assertIsInstance(validate_report(report), AtamReportDocument)
        malformed = report.model_copy(
            update={
                "atam_evaluation": report.atam_evaluation.model_copy(
                    update={"ground_truth_outputs": {"expected": "hidden"}}
                )
            }
        )
        with self.assertRaises(ValidationError):
            validate_report(malformed)

    def test_pydantic_contract_matches_shared_template_sections(self):
        # The schema model and readable JSON template should retain the same section keys.
        template = json.loads(REPORT_TEMPLATE.read_text(encoding="utf-8"))["ATAM_Evaluation"]
        self.assertEqual(set(template), set(AtamReportContent.model_fields))
        self.assertEqual(set(template["metadata"]), set(AtamMetadata.model_fields))
        self.assertEqual(set(template["evaluation_results"]), set(AtamEvaluationResults.model_fields))

    def test_pydantic_response_is_composed_with_original_inputs(self):
        # The model owns generated sections; the runner preserves the source inputs verbatim.
        payload = self._sample_payload()
        case = AtamCaseInputs(evaluation_inputs={"system_description": "An event framework"})
        report = compose_report(case, payload, "test-session")

        self.assertEqual(report.atam_evaluation.evaluation_inputs, case.evaluation_inputs)
        self.assertEqual(report.atam_evaluation.metadata.system_name, "Event framework")
        self.assertEqual(report.atam_evaluation.title, "ATAM Evaluation — Session test-session")
        self.assertIsNotNone(report.atam_evaluation.evaluation_results.analysis_records)

    def test_report_serializes_with_legacy_json_key(self):
        # Pydantic models cross into dictionaries only at the final JSON serialization edge.
        report = self._compose_sample_report()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = write_report(report, Path(temporary_directory) / "report.json", "session-x")
            written = json.loads(output.read_text(encoding="utf-8"))
        self.assertIn("ATAM_Evaluation", written)
        self.assertEqual(written["ATAM_Evaluation"]["title"], "ATAM Evaluation — Session test-session")

    def test_agent_roles_load_from_yaml(self):
        # Runtime specialist definitions are loaded from the editable external YAML.
        subagents = load_subagents()
        self.assertEqual([agent.name for agent in subagents], ["quality-attribute-analyst", "evidence-reviewer"])
        self.assertTrue(all(agent.skills for agent in subagents))

    def test_settings_yaml_defaults_are_overridden_by_cli(self):
        # YAML paths are rooted at the case study, while explicit CLI paths use the CWD.
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "settings.yaml").write_text(
                "case: data/from-yaml.json\noutput: runs/from-yaml.json\nmodel: openai:test\nstreaming: false\nverbose: false\n",
                encoding="utf-8",
            )
            parser = build_parser()
            defaults = resolve_config(parser.parse_args(["--case-study", str(root)]), environ={})
            self.assertEqual(defaults.case, (root / "data/from-yaml.json").resolve())
            self.assertEqual(defaults.output, (root / "runs/from-yaml.json").resolve())
            self.assertEqual(defaults.model, "openai:test")
            self.assertFalse(defaults.streaming)
            self.assertFalse(defaults.verbose)

            overrides = resolve_config(
                parser.parse_args(
                    [
                        "--case-study", str(root),
                        "--case", str(root / "data/cli.json"),
                        "--output", str(root / "runs/cli.json"),
                        "--model", "anthropic:test",
                        "--streaming",
                        "--verbose",
                    ]
                ),
                environ={"HW_ATAM_MODEL": "openai:environment"},
            )
            self.assertEqual(overrides.case, (root / "data/cli.json").resolve())
            self.assertEqual(overrides.output, (root / "runs/cli.json").resolve())
            self.assertEqual(overrides.model, "anthropic:test")
            self.assertTrue(overrides.streaming)
            self.assertTrue(overrides.verbose)

    def test_environment_model_overrides_yaml(self):
        # Provider credentials stay in the environment; a model-name override can too.
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "settings.yaml").write_text("model: openai:yaml\n", encoding="utf-8")
            args = build_parser().parse_args(["--case-study", str(root)])
            resolved = resolve_config(args, environ={"HW_ATAM_MODEL": "anthropic:env"})
            self.assertEqual(resolved.model, "anthropic:env")

    def test_effective_settings_render_as_yaml_without_internal_fields(self):
        # Startup output should show resolved values while omitting path-discovery internals.
        config = ResolvedRunConfig(
            case=Path("/case-study/data/example.json"),
            output=Path("/case-study/runs/example.json"),
            model="anthropic:override",
            streaming=False,
            verbose=True,
            case_study_root=Path("/case-study"),
        )
        rendered = format_resolved_settings(config)
        self.assertIn("model: anthropic:override", rendered)
        self.assertIn("streaming: false", rendered)
        self.assertIn("verbose: true", rendered)
        self.assertNotIn("case_study_root", rendered)

    def test_case_path_discovers_case_study_settings(self):
        # Supplying only the case automatically discovers its root settings.yaml.
        args = build_parser().parse_args([str(CASE)])
        resolved = resolve_config(args, environ={})
        case_study_root = ROOT / "case-studies/architecture-eval/ATAM"
        self.assertEqual(resolved.case_study_root, case_study_root.resolve())
        self.assertEqual(resolved.case, CASE.resolve())
        self.assertEqual(
            resolved.output,
            (ROOT / "examples/atam/deepagents/runs/banking-report.json").resolve(),
        )

    def test_streaming_and_non_streaming_share_final_state_contract(self):
        # The report path receives the same shape regardless of how execution is collected.
        final_state = {"messages": ["done"], "structured_response": "payload"}

        class FakeAgent:
            def stream(self, *args, **kwargs):
                yield {"type": "values", "data": final_state}

            def invoke(self, *args, **kwargs):
                return final_state

        agent = FakeAgent()
        for streaming in (True, False):
            result = execute_agent(
                agent,
                {"system_description": "test"},
                run_id=uuid4(),
                streaming=streaming,
                verbose=False,
            )
            self.assertEqual(result, final_state)

    def test_session_filename_and_tool_argument_truncation(self):
        # Session IDs distinguish report files and long arguments remain bounded.
        output = session_output_path(Path("runs/architecture.json"), "session-123")
        self.assertEqual(output, Path("runs/architecture-session-123.json"))
        rendered = format_tool_args({"args": {"instruction": "x" * 500}})
        self.assertLessEqual(len(rendered), 303)
        self.assertTrue(rendered.endswith("..."))

    def _sample_payload(self) -> AtamReportPayload:
        """Build a minimal Pydantic payload for report tests."""
        return AtamReportPayload.model_validate(
            {
                "metadata": {
                    "system_name": "Event framework",
                    "date": None,
                    "ref": None,
                    "evaluator_organization": None,
                    "phase_1_attendees": [],
                    "phase_2_attendees": [],
                },
                "evaluation_results": {
                    "utility_tree": {"root": "Utility", "quality_attribute_nodes": []},
                    "architectural_approaches": [],
                    "analysis_records": [],
                    "scenarios": [],
                },
            }
        )

    def _compose_sample_report(self) -> AtamReportDocument:
        """Build a minimal typed report used by serialization and validation tests."""
        case = AtamCaseInputs(evaluation_inputs={"system_description": "Test"})
        return compose_report(case, self._sample_payload(), "test-session")


if __name__ == "__main__":
    unittest.main()
