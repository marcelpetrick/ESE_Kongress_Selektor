# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Marcel Petrick <mail@marcelpetrick.it>
"""Guard the important contracts in the GitHub Actions workflows."""

from __future__ import annotations

import re
import unittest

from context import REPO_ROOT

WORKFLOWS = REPO_ROOT / ".github" / "workflows"


class WorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        cls.release = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")

    def test_actions_are_pinned_to_exact_releases(self):
        action_uses = re.findall(r"^\s*uses:\s*([^#\s]+)", self.ci + self.release, re.M)
        self.assertTrue(action_uses)
        for action in action_uses:
            self.assertRegex(action, r"^[\w.-]+/[\w.-]+@v\d+\.\d+\.\d+$")

    def test_ci_and_release_run_the_shared_gate(self):
        command = "python localPipeline.py"
        self.assertIn(command, self.ci)
        self.assertIn(command, self.release)

    def test_release_waits_for_quality_and_has_scoped_write_permission(self):
        publish_job = self.release.split("  release:", 1)[1]
        self.assertIn("needs: quality", publish_job)
        self.assertIn("contents: write", publish_job)
        self.assertIn("contents: read", self.release.split("jobs:", 1)[0])

    def test_release_validates_semantic_version_tags(self):
        self.assertIn(r"^v[0-9]+\.[0-9]+\.[0-9]+$", self.release)
        self.assertIn("--verify-tag", self.release)

    def test_release_is_always_published_as_stable(self):
        self.assertIn("--draft=false", self.release)
        self.assertIn("--prerelease=false", self.release)


if __name__ == "__main__":
    unittest.main()
