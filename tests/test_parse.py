# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Marcel Petrick <mail@marcelpetrick.it>
"""Parser tests -- run against the synthetic fixtures in tests/fixtures/raw."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from context import FIXTURE_RAW  # noqa: F401  (also fixes sys.path)

import classify
import parse


class ParseFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = classify.annotate(parse.build(FIXTURE_RAW))
        cls.events = {event["uid"]: event for event in cls.data["events"]}

    # -- day and grid ----------------------------------------------------
    def test_day_metadata_comes_from_the_timetable(self):
        day = self.data["days"][0]
        self.assertEqual(day["id"], "9001")
        self.assertEqual(day["date"], "30.11.2026")
        self.assertEqual(day["weekday"], "Mo")
        self.assertEqual(day["rooms"], ["Fixture Saal", "Fixture Raum"])

    def test_room_index_follows_the_column_order(self):
        self.assertEqual(self.events["session_5001_9001"]["room_index"], 0)
        self.assertEqual(self.events["session_5002_9001"]["room_index"], 1)

    def test_times_are_parsed_into_minutes(self):
        event = self.events["session_5001_9001"]
        self.assertEqual((event["start"], event["end"]), ("09:00", "10:00"))
        self.assertEqual((event["start_min"], event["end_min"]), (540, 600))

    def test_general_event_spanning_rooms_is_deduplicated(self):
        """A break is repeated per room column in the grid -- one event, many rooms."""
        general = [e for e in self.data["events"] if e["kind"] == "general"]
        self.assertEqual(len(general), 1)
        self.assertEqual(general[0]["rooms"], ["Fixture Saal", "Fixture Raum"])
        self.assertEqual(general[0]["ident"], "1_7001")

    # -- session details -------------------------------------------------
    def test_session_info_labels_are_stripped(self):
        event = self.events["session_5001_9001"]
        self.assertEqual(event["rooms"], ["Fixture Saal"])
        self.assertEqual(event["topic"], "Fixture-Thema Eins")
        self.assertEqual(event["form"], "Fachvortrag (35 Minuten)")
        self.assertEqual(event["duration"], "60 Minuten")
        self.assertEqual(event["topic_color"], "#008CFF")

    def test_direction_is_kept_when_present(self):
        self.assertEqual(self.events["session_5002_9001"]["direction"], "Fixture Moderation")
        self.assertEqual(self.events["session_5001_9001"]["direction"], "")

    def test_papers_keep_order_time_and_subtitle(self):
        papers = self.events["session_5002_9001"]["papers"]
        self.assertEqual([p["id"] for p in papers], ["8002", "8003"])
        self.assertEqual(papers[0]["time"], "09:00")
        self.assertEqual(papers[1]["time"], "09:30")
        self.assertEqual(papers[0]["subtitle"], "Von der Projektplanung bis zur Fehlerkultur")

    def test_person_is_split_into_name_affiliation_country(self):
        person = self.events["session_5001_9001"]["papers"][0]["persons"][0]
        self.assertEqual(person["id"], "4711")
        self.assertEqual(person["name"], "Dr. Fixture Erste")
        self.assertEqual(person["affiliation"], "Fixture GmbH")
        self.assertEqual(person["country"], "Germany")

    def test_person_without_country_or_affiliation(self):
        persons = self.events["session_5002_9001"]["papers"][0]["persons"]
        self.assertEqual([p["name"] for p in persons], ["Fixture Zweite", "Fixture Dritte"])
        self.assertEqual(persons[0]["country"], "")
        self.assertEqual(persons[1]["affiliation"], "")

    def test_author_label_is_not_mistaken_for_an_author(self):
        authors = self.events["session_5002_9001"]["papers"][0]["authors"]
        self.assertNotIn("Autor:innen:", authors)
        self.assertEqual(authors, ["Fixture Zweite | Fixture AG", "Fixture Dritte"])

    def test_abstract_is_captured_as_html_and_text(self):
        paper = self.events["session_5001_9001"]["papers"][0]
        self.assertIn("<br", paper["abstract_html"])
        self.assertIn("Coding Agent", paper["abstract_text"])
        self.assertNotIn("<br", paper["abstract_text"])

    def test_general_event_room_and_duration(self):
        general = self.events["general_7001_9001"]
        self.assertEqual(general["title"], "Fixture-Pause")
        self.assertEqual(general["papers"], [])
        self.assertEqual(general["source_url"].count("do=16"), 1)

    # -- topic registry --------------------------------------------------
    def test_topics_are_recovered_from_events_not_only_from_the_filter_form(self):
        """The site's filter form lists a subset only; 9102 exists just on the event."""
        names = {key: value["name"] for key, value in self.data["topics"].items()}
        self.assertEqual(names["9101"], "Fixture-Thema Eins")
        self.assertEqual(names["9102"], "Mensch, Team, Führung")
        self.assertEqual(self.data["topics"]["9102"]["color"], "#0F8A6A")

    # -- outputs ---------------------------------------------------------
    def test_write_produces_readable_json_and_a_loadable_data_js(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "congress.json"
            web_path = Path(tmp) / "web" / "data.js"
            parse.write(self.data, json_path, web_path)

            reloaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(len(reloaded["events"]), len(self.data["events"]))

            payload = web_path.read_text(encoding="utf-8")
            self.assertIn("window.CONGRESS_DATA = ", payload)
            self.assertTrue(payload.rstrip().endswith(";"))
            inline = payload.split("window.CONGRESS_DATA = ", 1)[1].rstrip().rstrip(";")
            self.assertEqual(json.loads(inline)["conference"], self.data["conference"])

    def test_build_without_timetables_fails_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                parse.build(Path(tmp))


if __name__ == "__main__":
    unittest.main()
