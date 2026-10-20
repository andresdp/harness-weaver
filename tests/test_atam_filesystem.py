import unittest

from examples.atam.deepagents.atam_harness.filesystem import atam_filesystem_permissions


class AtamFilesystemBoundaryTests(unittest.TestCase):
    def test_agents_can_read_skills_but_not_prior_reports_or_write_files(self):
        try:
            from deepagents.middleware.filesystem import _check_fs_permission
        except ImportError:
            self.skipTest("DeepAgents is an optional backend dependency")

        rules = atam_filesystem_permissions()
        self.assertEqual(_check_fs_permission(rules, "read", "/skills/evaluate-architecture/SKILL.md"), "allow")
        self.assertEqual(_check_fs_permission(rules, "read", "/runs/prior-report.json"), "deny")
        self.assertEqual(_check_fs_permission(rules, "write", "/runs/new-report.json"), "deny")


if __name__ == "__main__":
    unittest.main()
