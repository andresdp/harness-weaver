"""Paths shared by the ATAM DeepAgents backend modules."""

from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = PACKAGE_DIR.parent
REPOSITORY_ROOT = PACKAGE_DIR.parents[3]
AGENT_DEFINITIONS_PATH = PACKAGE_DIR / "agents.yaml"
DEFAULT_CASE_STUDY_ROOT = REPOSITORY_ROOT / "case-studies/architecture-eval/ATAM"
DEFAULT_HARNESS_SPEC_PATH = REPOSITORY_ROOT / "pilots/atam/harnessspec-v0.2.yaml"
SETTINGS_FILENAME = "settings.yaml"
