# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Marcel Petrick <mail@marcelpetrick.it>
"""Rules for the four highlight categories: weighting, threshold, false friends."""

from __future__ import annotations

import unittest

from context import FIXTURE_RAW  # noqa: F401  (also fixes sys.path)

import classify
import parse


def event(topic="", title="", subtitle="", abstract="", persons=(), rooms=()):
    """Minimal event shaped like parse.build() produces one."""
    return {
        "topic": topic,
        "form": "",
        "title": title,
        "rooms": list(rooms),
        "papers": [{
            "title": "",
            "subtitle": subtitle,
            "abstract_text": abstract,
            "persons": [{"display": name} for name in persons],
        }],
    }


class ScoringTest(unittest.TestCase):
    def test_field_weights_are_applied(self):
        """The same keyword is worth 4 in the topic and 1 in an abstract."""
        in_topic = classify.classify_event(event(topic="Agentic AI"))
        in_abstract = classify.classify_event(event(abstract="agentic ai"))
        self.assertEqual(in_topic["agentic-ai"]["score"], 4)
        self.assertEqual(in_abstract["agentic-ai"]["score"], 1)

    def test_repetition_does_not_inflate_a_score(self):
        once = classify.classify_event(event(abstract="scrum"))
        often = classify.classify_event(event(abstract="scrum scrum scrum scrum scrum"))
        self.assertEqual(once["project-management"]["score"],
                         often["project-management"]["score"])

    def test_distinct_keywords_do_add_up(self):
        result = classify.classify_event(event(abstract="scrum kanban backlog"))
        self.assertEqual(result["project-management"]["score"], 3)

    def test_matched_keywords_are_reported_per_field(self):
        result = classify.classify_event(event(title="Scrum", abstract="kanban"))
        matches = result["project-management"]["matches"]
        self.assertEqual(matches["title"], ["scrum"])
        self.assertEqual(matches["abstract"], ["kanban"])


class ThresholdTest(unittest.TestCase):
    def test_threshold_splits_strong_from_weak(self):
        data = {"events": [
            event(abstract="scrum"),                    # score 1 -> weak
            event(abstract="scrum kanban backlog"),     # score 3 -> strong
        ]}
        classify.annotate(data)
        self.assertEqual(data["events"][0]["tags"], [])
        self.assertEqual(data["events"][0]["weak_tags"], ["project-management"])
        self.assertEqual(data["events"][1]["tags"], ["project-management"])
        self.assertEqual(data["events"][1]["weak_tags"], [])

    def test_tags_are_ordered_by_score(self):
        data = {"events": [event(topic="Mensch, Team, Führung",
                                 abstract="scrum kanban backlog llm")]}
        classify.annotate(data)
        tags = data["events"][0]["tags"]
        scores = [data["events"][0]["tag_details"][tag]["score"] for tag in tags]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_annotate_publishes_the_rule_definitions(self):
        data = {"events": []}
        classify.annotate(data)
        self.assertEqual(set(data["tag_definitions"]), set(classify.RULES))
        self.assertEqual(data["tag_config"]["min_score"], classify.MIN_SCORE)


class FalseFriendTest(unittest.TestCase):
    """A functional-safety congress is full of words that look like framework names."""

    def test_safe_and_safety_are_not_the_safe_framework(self):
        result = classify.classify_event(event(
            title="From Functional Safety to Safe Intelligence",
            abstract="a safe system is safer than an unsafe one"))
        self.assertNotIn("scaling", result)

    def test_the_actual_safe_framework_still_scores(self):
        result = classify.classify_event(event(abstract="we roll out SAFe across the org"))
        self.assertIn("scaling", result)
        self.assertEqual(result["scaling"]["matches"]["abstract"], ["safe"])

    def test_less_is_not_large_scale_scrum(self):
        self.assertNotIn("scaling", classify.classify_event(event(abstract="less code, less risk")))
        self.assertIn("scaling", classify.classify_event(event(abstract="we scaled with LeSS")))


class SearchIndexTest(unittest.TestCase):
    def test_search_text_is_lowercase_and_covers_people_and_rooms(self):
        data = {"events": [event(title="Titel", abstract="Inhalt",
                                 persons=["Dr. Fixture Erste | Fixture GmbH"],
                                 rooms=["Fixture Saal"])]}
        classify.annotate(data)
        haystack = data["events"][0]["search_text"]
        self.assertEqual(haystack, haystack.lower())
        for needle in ("titel", "inhalt", "fixture gmbh", "fixture saal"):
            self.assertIn(needle, haystack)


class FixtureTaggingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = classify.annotate(parse.build(FIXTURE_RAW))
        cls.events = {e["uid"]: e for e in data["events"]}

    def test_agentic_session_is_tagged(self):
        self.assertEqual(self.events["session_5001_9001"]["tags"], ["agentic-ai"])

    def test_team_session_is_tagged_team_before_project(self):
        self.assertEqual(self.events["session_5002_9001"]["tags"],
                         ["team-management", "project-management"])

    def test_safety_contribution_does_not_produce_a_scaling_tag(self):
        self.assertEqual(self.events["session_5002_9001"]["weak_tags"], [])

    def test_break_is_not_tagged(self):
        self.assertEqual(self.events["general_7001_9001"]["tags"], [])


if __name__ == "__main__":
    unittest.main()
