# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Marcel Petrick <mail@marcelpetrick.it>
"""Consistency checks between the parts that have to agree with each other.

Nothing here needs the network. These are the checks that catch the kind of
drift no single module can notice on its own: a highlight category added to the
classifier but never given a colour in the viewer, a viewer file renamed, a
dependency pin loosened, or the Windows interpreter path breaking.
"""

from __future__ import annotations

import re
import unittest
from unittest import mock

from context import REPO_ROOT  # noqa: F401  (also fixes sys.path)

import classify
import run

WEB = REPO_ROOT / "web"


class ViewerAgreesWithClassifierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (WEB / "style.css").read_text(encoding="utf-8")
        cls.js = (WEB / "app.js").read_text(encoding="utf-8")
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")

    def test_every_category_has_a_colour(self):
        for tag in classify.RULES:
            self.assertIn(f"--tag-{tag}:", self.css, f"no colour for category {tag}")

    def test_every_category_has_a_dark_mode_colour(self):
        dark = self.css.split("prefers-color-scheme: dark", 1)[1]
        for tag in classify.RULES:
            self.assertIn(f"--tag-{tag}:", dark, f"no dark colour for category {tag}")

    def test_every_category_is_known_to_the_viewer(self):
        order = re.search(r"const TAG_ORDER = \[(.*?)\]", self.js, re.S).group(1)
        short = re.search(r"const TAG_SHORT = \{(.*?)\};", self.js, re.S).group(1)
        for tag in classify.RULES:
            self.assertIn(f"'{tag}'", order, f"{tag} missing from TAG_ORDER")
            self.assertIn(f"'{tag}'", short, f"{tag} missing from TAG_SHORT")

    def test_viewer_knows_no_category_the_classifier_does_not_produce(self):
        order = re.search(r"const TAG_ORDER = \[(.*?)\]", self.js, re.S).group(1)
        self.assertEqual(set(re.findall(r"'([a-z-]+)'", order)), set(classify.RULES))

    def test_index_html_pulls_in_the_generated_payload_and_the_app(self):
        for asset in ("style.css", "data.js", "app.js"):
            self.assertIn(asset, self.html, f"index.html does not reference {asset}")
        self.assertLess(self.html.index("data.js"), self.html.index("app.js"),
                        "data.js must be loaded before app.js reads window.CONGRESS_DATA")


class BootstrapTest(unittest.TestCase):
    def test_python_floor_matches_the_pinned_dependencies(self):
        # requests 2.34.2 declares Requires-Python >=3.10.
        self.assertEqual(run.MIN_PYTHON, (3, 10))

    def test_venv_interpreter_path_per_platform(self):
        with mock.patch.object(run.os, "name", "posix"):
            self.assertEqual(run.venv_python().parts[-2:], ("bin", "python"))
        with mock.patch.object(run.os, "name", "nt"):
            self.assertEqual(run.venv_python().parts[-2:], ("Scripts", "python.exe"))

    def test_requirements_hash_is_stable_and_hex(self):
        first, second = run.requirements_hash(), run.requirements_hash()
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")

    def test_dependencies_are_pinned_to_exact_versions(self):
        for line in run.REQUIREMENTS.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                self.assertRegex(line, r"^[A-Za-z0-9_.-]+==\d+(\.\d+)*$",
                                 f"dependency not pinned exactly: {line!r}")


if __name__ == "__main__":
    unittest.main()
