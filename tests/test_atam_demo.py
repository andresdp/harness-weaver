import json
import os
import stat
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from pydantic import ValidationError

from pilots.atam.deepagents.atam_harness.agents import load_subagents
from pilots.atam.deepagents.atam_harness.config import (
    ResolvedRunConfig,
    build_parser,
    format_resolved_settings,
    resolve_config,
)
from pilots.atam.deepagents.atam_harness.models import (
    AtamCaseInputs,
    AtamEvaluationResults,
    AtamMetadata,
    AtamReportContent,
    AtamReportDocument,
    AtamReportPayload,
    AtamSemanticState,
)
from pilots.atam.deepagents.atam_harness.prompts import build_task_prompt
from pilots.atam.deepagents.atam_harness.progress import format_tool_args
from pilots.atam.deepagents.atam_harness.reports import (
    compose_report,
    load_case,
    session_output_path,
    validate_report,
    write_report,
)
from harnessweaver.runtime import RunResult


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "case-studies/architecture-eval/ATAM/data/banking.json"
REPORT_TEMPLATE = ROOT / "pilots/atam/sources/domain/references/atam-report-template.json"


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
        # The schema model and runtime-specific template mirrors should retain matching keys.
        template = json.loads(REPORT_TEMPLATE.read_text(encoding="utf-8"))["ATAM_Evaluation"]
        self.assertEqual(set(template), set(AtamReportContent.model_fields))
        self.assertEqual(set(template["metadata"]), set(AtamMetadata.model_fields))
        self.assertEqual(set(template["evaluation_results"]), set(AtamEvaluationResults.model_fields))
        template_paths = [
            *ROOT.joinpath("pilots/atam/claude-plugin").glob("**/atam-report-template.json"),
            *ROOT.joinpath("pilots/atam/deepagents/skills").glob("**/atam-report-template.json"),
        ]
        for path in template_paths:
            mirrored = json.loads(path.read_text(encoding="utf-8"))["ATAM_Evaluation"]["evaluation_results"]
            self.assertEqual(set(mirrored), set(AtamEvaluationResults.model_fields), str(path))
            self.assertEqual(set(mirrored["semantic_state"]), set(AtamSemanticState.model_fields), str(path))

        # Evaluation and checker skills must use the same ATAM method and output contract.
        for skill_root in (
            ROOT / "pilots/atam/claude-plugin/skills",
            ROOT / "pilots/atam/deepagents/skills",
        ):
            for filename in ("atam-methodology.yaml", "atam-report-template.json"):
                evaluation_copy = skill_root / "evaluate-architecture/references" / filename
                checker_copy = skill_root / "check-evaluation/references" / filename
                self.assertEqual(evaluation_copy.read_bytes(), checker_copy.read_bytes(), filename)

    def test_semantic_state_requires_allowed_statuses_and_evidence(self):
        # Status values map to methodology enums and cannot be asserted without a basis.
        payload = self._sample_payload().model_dump(mode="json")
        payload["evaluation_results"]["semantic_state"]["context_status"]["value"] = "reviewed"
        with self.assertRaises(ValidationError):
            AtamReportPayload.model_validate(payload)

        payload = self._sample_payload().model_dump(mode="json")
        payload["evaluation_results"]["semantic_state"]["context_status"]["evidence"] = []
        with self.assertRaises(ValidationError):
            AtamReportPayload.model_validate(payload)

        for field, value in (("scenario_analysis_status", "complete"), ("report_status", "published")):
            with self.subTest(field=field):
                payload = self._sample_payload().model_dump(mode="json")
                payload["evaluation_results"]["semantic_state"][field]["value"] = value
                with self.assertRaises(ValidationError):
                    AtamReportPayload.model_validate(payload)

        for field in ("driver_status", "scenario_analysis_status", "report_status"):
            with self.subTest(empty_evidence_field=field):
                payload = self._sample_payload().model_dump(mode="json")
                payload["evaluation_results"]["semantic_state"][field]["evidence"] = ["   "]
                with self.assertRaises(ValidationError):
                    AtamReportPayload.model_validate(payload)

        payload = self._sample_payload().model_dump(mode="json")
        payload["evaluation_results"]["semantic_state"]["gaps"] = [
            {
                "description": "",
                "affected_activity": "build-utility-tree",
                "missing_evidence": "Priority tuples",
                "resolution_question": "What is the priority?",
            }
        ]
        with self.assertRaises(ValidationError):
            AtamReportPayload.model_validate(payload)

        for field in ("description", "affected_activity", "missing_evidence", "resolution_question"):
            with self.subTest(empty_gap_field=field):
                payload = self._sample_payload().model_dump(mode="json")
                payload["evaluation_results"]["semantic_state"]["gaps"] = [{
                    "description": "A gap", "affected_activity": "analysis",
                    "missing_evidence": "Evidence", "resolution_question": "What is missing?",
                }]
                payload["evaluation_results"]["semantic_state"]["gaps"][0][field] = "  "
                with self.assertRaises(ValidationError):
                    AtamReportPayload.model_validate(payload)

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
                "case: data/from-yaml.json\noutput: runs/from-yaml.json\nmodel: openai:test\nrequest_timeout_seconds: 42\nstreaming: false\nverbose: false\n",
                encoding="utf-8",
            )
            parser = build_parser()
            defaults = resolve_config(parser.parse_args(["--case-study", str(root)]), environ={})
            self.assertEqual(defaults.case, (root / "data/from-yaml.json").resolve())
            self.assertEqual(defaults.output, (root / "runs/from-yaml.json").resolve())
            self.assertEqual(defaults.model, "openai:test")
            self.assertEqual(defaults.request_timeout_seconds, 42)
            self.assertEqual(defaults.workflow_strategy, "supervisor")
            self.assertEqual(defaults.agent_interaction, "one_shot_specialist_delegation")
            self.assertFalse(defaults.streaming)
            self.assertFalse(defaults.verbose)

            fan_out = resolve_config(
                parser.parse_args([
                    "--case-study", str(root),
                    "--workflow-strategy", "fan_out_fan_in",
                    "--agent-interaction", "parallel_specialist_delegation",
                ]),
                environ={},
            )
            self.assertEqual(fan_out.workflow_strategy, "fan_out_fan_in")
            self.assertEqual(fan_out.agent_interaction, "parallel_specialist_delegation")

            overrides = resolve_config(
                parser.parse_args(
                    [
                        "--case-study", str(root),
                        "--case", str(root / "data/cli.json"),
                        "--output", str(root / "runs/cli.json"),
                        "--model", "anthropic:test",
                        "--workflow-strategy", "sequential_pipeline",
                        "--agent-interaction", "typed_artifact_handoffs",
                        "--streaming",
                        "--verbose",
                    ]
                ),
                environ={"HW_ATAM_MODEL": "openai:environment"},
            )
            self.assertEqual(overrides.case, (root / "data/cli.json").resolve())
            self.assertEqual(overrides.output, (root / "runs/cli.json").resolve())
            self.assertEqual(overrides.model, "anthropic:test")
            self.assertEqual(overrides.workflow_strategy, "sequential_pipeline")
            self.assertEqual(overrides.agent_interaction, "typed_artifact_handoffs")
            self.assertTrue(overrides.streaming)
            self.assertTrue(overrides.verbose)

            (root / "settings.yaml").write_text("request_timeout_seconds: 0\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid .*settings.yaml"):
                resolve_config(parser.parse_args(["--case-study", str(root)]), environ={})

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
            request_timeout_seconds=120,
            harness_spec=ROOT / "pilots/atam/harnessspec-v0.2.yaml",
            workflow_strategy="fan_out_fan_in",
            agent_interaction="parallel_specialist_delegation",
            streaming=False,
            verbose=True,
            case_study_root=Path("/case-study"),
        )
        rendered = format_resolved_settings(config)
        self.assertIn("model: anthropic:override", rendered)
        self.assertIn("request_timeout_seconds: 120", rendered)
        self.assertIn("streaming: false", rendered)
        self.assertIn("verbose: true", rendered)
        self.assertIn("workflow_strategy: fan_out_fan_in", rendered)
        self.assertIn("agent_interaction: parallel_specialist_delegation", rendered)
        self.assertIn("harness_spec:", rendered)
        self.assertNotIn("case_study_root", rendered)

    def test_strategy_override_requires_a_supported_interaction_pair(self):
        with self.assertRaisesRegex(ValueError, "unsupported workflow_strategy/agent_interaction combination"):
            resolve_config(
                build_parser().parse_args(["--workflow-strategy", "sequential_pipeline"]),
                environ={},
            )

    def test_case_path_discovers_case_study_settings(self):
        # Supplying only the case automatically discovers its root settings.yaml.
        args = build_parser().parse_args([str(CASE)])
        resolved = resolve_config(args, environ={})
        case_study_root = ROOT / "case-studies/architecture-eval/ATAM"
        self.assertEqual(resolved.case_study_root, case_study_root.resolve())
        self.assertEqual(resolved.case, CASE.resolve())
        self.assertEqual(
            resolved.output,
            (ROOT / "pilots/atam/deepagents/runs/banking-report.json").resolve(),
        )

    def test_session_filename_and_tool_argument_truncation(self):
        # Session IDs distinguish report files and long arguments remain bounded.
        output = session_output_path(Path("runs/architecture.json"), "session-123")
        self.assertEqual(output, Path("runs/architecture-session-123.json"))
        rendered = format_tool_args({"args": {"instruction": "x" * 500}})
        self.assertLessEqual(len(rendered), 303)
        self.assertTrue(rendered.endswith("..."))

    def test_atomic_report_write_preserves_normal_file_permissions(self):
        # Atomic publication should retain the default umask mode for new reports
        # and preserve an existing report's mode when replacing its contents.
        report = self._compose_sample_report()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            expected_mode_path = root / "normal-write.json"
            expected_mode_path.write_text("{}\n", encoding="utf-8")
            expected_mode = stat.S_IMODE(expected_mode_path.stat().st_mode)

            output = root / "report.json"
            new_report = write_report(report, output, "new-session")
            self.assertEqual(stat.S_IMODE(new_report.stat().st_mode), expected_mode)

            replaced_report = session_output_path(output, "existing-session")
            replaced_report.write_text("old contents\n", encoding="utf-8")
            os.chmod(replaced_report, 0o640)
            write_report(report, output, "existing-session")
            self.assertEqual(stat.S_IMODE(replaced_report.stat().st_mode), 0o640)

    def test_atomic_report_write_does_not_remove_a_colliding_temp_file(self):
        # A name collision belongs to another writer and must survive allocation failure.
        report = self._compose_sample_report()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.json"
            destination = session_output_path(output, "session-123")
            collision = Path(temporary_directory) / f".{destination.name}.deadbeefdeadbeef.tmp"
            collision.write_text("owned by another writer\n", encoding="utf-8")
            with patch("pilots.atam.deepagents.atam_harness.reports.secrets.token_hex", return_value="deadbeefdeadbeef"):
                with self.assertRaises(FileExistsError):
                    write_report(report, output, "session-123")

            self.assertEqual(collision.read_text(encoding="utf-8"), "owned by another writer\n")
            self.assertFalse(destination.exists())

    def test_run_writes_session_scoped_runtime_fidelity_record(self):
        from pilots.atam.deepagents.atam_harness import runner

        run_id = uuid4()
        payload = self._sample_payload()
        case = AtamCaseInputs(evaluation_inputs={"system_description": "Test system"})
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.json"
            config = ResolvedRunConfig(
                case=CASE,
                output=output,
                model="openai:test-model",
                request_timeout_seconds=120,
                harness_spec=ROOT / "pilots/atam/harnessspec-v0.2.yaml",
                workflow_strategy="supervisor",
                agent_interaction="one_shot_specialist_delegation",
                streaming=False,
                verbose=False,
                case_study_root=ROOT / "case-studies/architecture-eval/ATAM",
            )
            result = RunResult(
                run_id=run_id,
                status="succeeded",
                output_path=output,
                elapsed_seconds=1.25,
                capabilities=("deepagents", "supervisor", "one_shot_specialist_delegation"),
                approximations=("Specialists are one-shot.",),
                unsupported=("Persistent agent messaging.",),
                artifact=payload,
            )
            with (
                patch.object(runner, "uuid4", return_value=run_id),
                patch.object(runner, "load_case", return_value=case),
                patch.object(runner.DeepAgentsRuntimeAdapter, "run", return_value=result) as adapter_run,
            ):
                runner.run(config)

            request = adapter_run.call_args.args[0]
            self.assertEqual(request.profile.workflow_strategy.value, "supervisor")
            self.assertEqual(request.profile.agent_interaction.value, "one_shot_specialist_delegation")
            self.assertEqual(request.settings, {"request_timeout_seconds": 120})

            report_path = output.with_name(f"report-{run_id}.json")
            record_path = report_path.with_suffix(".runtime.json")
            record = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "succeeded")
            self.assertEqual(record["record_version"], "0.2")
            self.assertEqual(record["session_id"], str(run_id))
            self.assertEqual(record["workflow_strategy"], "supervisor")
            self.assertEqual(record["agent_interaction"], "one_shot_specialist_delegation")
            self.assertEqual(record["request_timeout_seconds"], 120)
            self.assertEqual(record["capabilities"], ["deepagents", "supervisor", "one_shot_specialist_delegation"])
            self.assertEqual(record["approximations"], ["Specialists are one-shot."])
            self.assertEqual(record["unsupported"], ["Persistent agent messaging."])
            self.assertEqual(record["report_path"], str(report_path))
            self.assertIsNone(record["cost_usd"])

    def test_failed_run_writes_a_session_record_without_publishing_a_report(self):
        from pilots.atam.deepagents.atam_harness import runner

        run_id = uuid4()
        case = AtamCaseInputs(evaluation_inputs={"system_description": "Test system"})
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.json"
            config = ResolvedRunConfig(
                case=CASE,
                output=output,
                model="openai:test-model",
                request_timeout_seconds=120,
                harness_spec=ROOT / "pilots/atam/harnessspec-v0.2.yaml",
                workflow_strategy="supervisor",
                agent_interaction="one_shot_specialist_delegation",
                streaming=False,
                verbose=False,
                case_study_root=ROOT / "case-studies/architecture-eval/ATAM",
            )
            with (
                patch.object(runner, "uuid4", return_value=run_id),
                patch.object(runner, "load_case", return_value=case),
                patch.object(
                    runner.DeepAgentsRuntimeAdapter,
                    "run",
                    side_effect=RuntimeError("provider failed: sk-proj-1234567890abcdefghijkl"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "provider failed"):
                    runner.run(config)

            report_path = output.with_name(f"report-{run_id}.json")
            record_path = report_path.with_suffix(".runtime.json")
            record = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["record_version"], "0.2")
            self.assertEqual(record["session_id"], str(run_id))
            self.assertEqual(record["error_type"], "RuntimeError")
            self.assertEqual(record["error_message"], "Error details omitted from persistent record.")
            self.assertNotIn("sk-proj-1234567890abcdefghijkl", record_path.read_text(encoding="utf-8"))
            self.assertIsNone(record["report_path"])
            self.assertFalse(report_path.exists())

    def test_keyboard_interrupt_writes_a_session_record_without_publishing_a_report(self):
        from pilots.atam.deepagents.atam_harness import runner

        run_id = uuid4()
        case = AtamCaseInputs(evaluation_inputs={"system_description": "Test system"})
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.json"
            config = ResolvedRunConfig(
                case=CASE,
                output=output,
                model="openai:test-model",
                request_timeout_seconds=120,
                harness_spec=ROOT / "pilots/atam/harnessspec-v0.2.yaml",
                workflow_strategy="sequential_pipeline",
                agent_interaction="typed_artifact_handoffs",
                streaming=False,
                verbose=False,
                case_study_root=ROOT / "case-studies/architecture-eval/ATAM",
            )
            with (
                patch.object(runner, "uuid4", return_value=run_id),
                patch.object(runner, "load_case", return_value=case),
                patch.object(
                    runner.DeepAgentsRuntimeAdapter,
                    "run",
                    side_effect=KeyboardInterrupt(),
                ),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    runner.run(config)

            report_path = output.with_name(f"report-{run_id}.json")
            record_path = report_path.with_suffix(".runtime.json")
            record = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["error_type"], "KeyboardInterrupt")
            self.assertEqual(record["error_message"], "Error details omitted from persistent record.")
            self.assertIsNone(record["report_path"])
            self.assertFalse(report_path.exists())

    def test_keyboard_interrupt_during_report_write_removes_partial_output(self):
        from pilots.atam.deepagents.atam_harness import reports, runner

        run_id = uuid4()
        case = AtamCaseInputs(evaluation_inputs={"system_description": "Test system"})
        payload = self._sample_payload()
        result = RunResult(
            run_id=run_id,
            status="succeeded",
            output_path=None,
            artifact=payload,
            elapsed_seconds=1.0,
            capabilities=("deepagents",),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.json"
            config = ResolvedRunConfig(
                case=CASE,
                output=output,
                model="openai:test-model",
                request_timeout_seconds=120,
                harness_spec=ROOT / "pilots/atam/harnessspec-v0.2.yaml",
                workflow_strategy="supervisor",
                agent_interaction="one_shot_specialist_delegation",
                streaming=False,
                verbose=False,
                case_study_root=ROOT / "case-studies/architecture-eval/ATAM",
            )
            with (
                patch.object(runner, "uuid4", return_value=run_id),
                patch.object(runner, "load_case", return_value=case),
                patch.object(runner.DeepAgentsRuntimeAdapter, "run", return_value=result),
                patch.object(reports.os, "fsync", side_effect=KeyboardInterrupt()),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    runner.run(config)

            report_path = output.with_name(f"report-{run_id}.json")
            record_path = report_path.with_suffix(".runtime.json")
            record = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["error_type"], "KeyboardInterrupt")
            self.assertIsNone(record["report_path"])
            self.assertFalse(report_path.exists())
            self.assertEqual(list(Path(temporary_directory).glob(".*.tmp")), [])

    def test_case_load_failure_writes_a_session_record(self):
        from pilots.atam.deepagents.atam_harness import runner

        run_id = uuid4()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.json"
            config = ResolvedRunConfig(
                case=Path(temporary_directory) / "missing-case.json",
                output=output,
                model="openai:test-model",
                request_timeout_seconds=120,
                harness_spec=ROOT / "pilots/atam/harnessspec-v0.2.yaml",
                workflow_strategy="supervisor",
                agent_interaction="one_shot_specialist_delegation",
                streaming=False,
                verbose=False,
                case_study_root=ROOT / "case-studies/architecture-eval/ATAM",
            )
            with (
                patch.object(runner, "uuid4", return_value=run_id),
                patch.object(runner, "load_case", side_effect=FileNotFoundError("case missing")),
            ):
                with self.assertRaisesRegex(FileNotFoundError, "case missing"):
                    runner.run(config)

            record_path = output.with_name(f"report-{run_id}.runtime.json")
            record = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "failed")
            self.assertEqual(record["error_type"], "FileNotFoundError")
            self.assertEqual(record["error_message"], "Error details omitted from persistent record.")
            self.assertIsNone(record["case_sha256"])
            self.assertIsNone(record["evaluation_inputs_sha256"])

    def test_run_record_survives_transient_fingerprint_read_timeout(self):
        from pilots.atam.deepagents.atam_harness import reports

        case = AtamCaseInputs(evaluation_inputs={"system_description": "Test system"})
        config = ResolvedRunConfig(
            case=CASE,
            output=ROOT / "report.json",
            model="openai:test-model",
            request_timeout_seconds=120,
            harness_spec=ROOT / "pilots/atam/harnessspec-v0.2.yaml",
            workflow_strategy="supervisor",
            agent_interaction="one_shot_specialist_delegation",
            streaming=False,
            verbose=False,
            case_study_root=ROOT / "case-studies/architecture-eval/ATAM",
        )
        with patch.object(reports, "sha256_file", side_effect=TimeoutError("filesystem read timed out")):
            record = reports.compose_run_record(
                case, config, None, None, str(uuid4()), error=RuntimeError("provider connection failed")
            )

        self.assertEqual(record.status, "failed")
        self.assertIsNone(record.case_sha256)
        self.assertIsNone(record.harness_spec_sha256)
        self.assertEqual(record.error_type, "RuntimeError")

    def test_shared_agent_builder_keeps_role_schema_and_common_runtime_setup(self):
        from pilots.atam.deepagents.atam_harness import agents
        from pilots.atam.deepagents.atam_harness.models import AtamContextArtifact

        model = object()
        sentinel_agent = object()
        with (
            patch("langchain.chat_models.init_chat_model", return_value=model) as init_model,
            patch("deepagents.create_deep_agent", return_value=sentinel_agent) as create_agent,
        ):
            result = agents.build_deep_agent(
                "openai:test-model",
                75,
                name="atam-context",
                system_prompt="Context stage instructions",
                schema=AtamContextArtifact,
            )

        self.assertIs(result, sentinel_agent)
        init_model.assert_called_once_with("openai:test-model", timeout=75)
        kwargs = create_agent.call_args.kwargs
        self.assertEqual(kwargs["name"], "atam-context")
        self.assertIs(kwargs["model"], model)
        self.assertEqual(kwargs["system_prompt"], "Context stage instructions")
        self.assertNotIn("subagents", kwargs)
        self.assertEqual(kwargs["skills"], ["./skills/"])
        self.assertIsNotNone(kwargs["backend"])
        self.assertIsNotNone(kwargs["response_format"])
        self.assertIsNotNone(kwargs["permissions"])

    def test_coordinator_keeps_deepagents_default_name_and_original_schema(self):
        from pilots.atam.deepagents.atam_harness import agents

        with (
            patch.object(agents, "load_subagents", return_value=[]),
            patch.object(agents, "build_deep_agent", return_value=object()) as build,
        ):
            agents.build_agent("openai:test-model", 90)

        self.assertNotIn("name", build.call_args.kwargs)
        self.assertIs(build.call_args.kwargs["schema"], agents.AtamReportPayload)
        self.assertEqual(build.call_args.kwargs["system_prompt"], agents.load_prompt("system.md"))
        self.assertEqual(build.call_args.kwargs["subagents"], [])

    def test_streaming_and_non_streaming_write_equivalent_report_content(self):
        from pilots.atam.deepagents.atam_harness import runner

        case = AtamCaseInputs(evaluation_inputs={"system_description": "Test system"})
        payload = self._sample_payload()
        run_ids = [uuid4(), uuid4()]
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.json"
            base_config = dict(
                case=CASE,
                output=output,
                model="openai:test-model",
                request_timeout_seconds=120,
                harness_spec=ROOT / "pilots/atam/harnessspec-v0.2.yaml",
                workflow_strategy="supervisor",
                agent_interaction="one_shot_specialist_delegation",
                verbose=False,
                case_study_root=ROOT / "case-studies/architecture-eval/ATAM",
            )
            configs = [
                ResolvedRunConfig(**base_config, streaming=False),
                ResolvedRunConfig(**base_config, streaming=True),
            ]
            def execute(request):
                return RunResult(
                    run_id=request.run_id,
                    status="succeeded",
                    output_path=output,
                    elapsed_seconds=1.0,
                    capabilities=("deepagents", "supervisor"),
                    artifact=payload,
                )

            with (
                patch.object(runner, "uuid4", side_effect=run_ids),
                patch.object(runner, "load_case", return_value=case),
                patch.object(runner.DeepAgentsRuntimeAdapter, "run", side_effect=execute),
            ):
                for config in configs:
                    runner.run(config)

            report_values = [
                json.loads(session_output_path(output, str(run_id)).read_text(encoding="utf-8"))
                for run_id in run_ids
            ]
            for report in report_values:
                report["ATAM_Evaluation"]["title"] = "normalized"
            self.assertEqual(report_values[0], report_values[1])

    def test_concurrent_runs_write_distinct_reports_and_runtime_records(self):
        from pilots.atam.deepagents.atam_harness import runner

        case = AtamCaseInputs(evaluation_inputs={"system_description": "Test system"})
        payload = self._sample_payload()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "report.json"
            config = ResolvedRunConfig(
                case=CASE,
                output=output,
                model="openai:test-model",
                request_timeout_seconds=120,
                harness_spec=ROOT / "pilots/atam/harnessspec-v0.2.yaml",
                workflow_strategy="supervisor",
                agent_interaction="one_shot_specialist_delegation",
                streaming=False,
                verbose=False,
                case_study_root=ROOT / "case-studies/architecture-eval/ATAM",
            )

            def execute(request):
                return RunResult(
                    run_id=request.run_id,
                    status="succeeded",
                    output_path=output,
                    elapsed_seconds=0.1,
                    capabilities=("deepagents", "supervisor"),
                    artifact=payload,
                )

            with (
                patch.object(runner, "load_case", return_value=case),
                patch.object(runner.DeepAgentsRuntimeAdapter, "run", side_effect=execute),
                ThreadPoolExecutor(max_workers=2) as pool,
            ):
                futures = [pool.submit(runner.run, config) for _ in range(2)]
                for future in futures:
                    future.result()

            reports = sorted(
                path for path in Path(temporary_directory).glob("report-*.json")
                if not path.name.endswith(".runtime.json")
            )
            records = sorted(Path(temporary_directory).glob("report-*.runtime.json"))
            self.assertEqual(len(reports), 2)
            self.assertEqual(len(records), 2)
            session_ids = {
                json.loads(record.read_text(encoding="utf-8"))["session_id"] for record in records
            }
            self.assertEqual(len(session_ids), 2)

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
                    "semantic_state": {
                        "context_status": {"value": "sufficient", "evidence": ["Scope is present in input."]},
                        "driver_status": {"value": "partial", "evidence": ["Some quality drivers are provided."]},
                        "architecture_evidence_status": {"value": "partial", "evidence": ["Architecture facts are limited."]},
                        "scenario_analysis_status": {"value": "not_started", "evidence": ["No review artifact is present."]},
                        "report_status": {"value": "draft", "evidence": ["This payload has not been reviewed by an architect."]},
                        "gaps": [],
                    },
                },
            }
        )

    def _compose_sample_report(self) -> AtamReportDocument:
        """Build a minimal typed report used by serialization and validation tests."""
        case = AtamCaseInputs(evaluation_inputs={"system_description": "Test"})
        return compose_report(case, self._sample_payload(), "test-session")


if __name__ == "__main__":
    unittest.main()
