import json
import unittest
from pathlib import Path


PROTOTYPE = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[3]


class ContentProvenanceTests(unittest.TestCase):
    # The lesson cards were copied from the private N'Ko data repository.
    # This check only runs when that repository is checked out around this one.
    @unittest.skipUnless(
        (REPOSITORY / "data" / "nko-characters.json").exists(),
        "N'Ko data repository not present",
    )
    def test_lesson_cards_match_canonical_sources(self):
        lesson_list = json.loads(
            (PROTOTYPE / "content" / "lessons.json").read_text(encoding="utf-8")
        )["lessons"]
        lessons = {item["card_id"]: item for item in lesson_list}

        greetings = json.loads(
            (REPOSITORY / "data" / "cultural" / "greetings-unified.json").read_text(
                encoding="utf-8"
            )
        )["greetings"]
        by_id = {item["id"]: item for item in greetings}
        for card_id, source_id in (
            ("greeting-morning", "greeting-01"),
            ("greeting-afternoon", "greeting-03"),
        ):
            card = lessons[card_id]
            source = by_id[source_id]
            self.assertEqual(card["nko"], source["text_nko"])
            self.assertEqual(card["latin"], source["text_latin"])
            self.assertEqual(card["english"], source["english_translation"])
            self.assertEqual(card["expected_response"], source["expected_response"])

        vowels = json.loads(
            (REPOSITORY / "data" / "nko-characters.json").read_text(encoding="utf-8")
        )["vowels"]
        self.assertEqual(lessons["letter-a"]["latin"], vowels["ߊ"]["latin"])
        self.assertEqual(lessons["letter-i"]["latin"], vowels["ߌ"]["latin"])

    def test_every_card_has_visible_provenance(self):
        payload = json.loads(
            (PROTOTYPE / "content" / "lessons.json").read_text(encoding="utf-8")
        )
        self.assertIn("human review", payload["authority"])
        for lesson in payload["lessons"]:
            self.assertTrue(lesson["source"].startswith("data/"))


if __name__ == "__main__":
    unittest.main()
