import unittest
from pathlib import Path

from jeli.state import JeliState, StateError


LESSONS = Path(__file__).resolve().parents[1] / "content" / "lessons.json"


class JeliStateTests(unittest.TestCase):
    def setUp(self):
        self.state = JeliState(LESSONS)

    def test_select_and_talk_cycle(self):
        selected = self.state.select_card("greeting-morning")
        self.assertEqual(selected["mode"], "card_ready")
        listening = self.state.set_talk(True)
        self.assertTrue(listening["recording_indicator"])
        released = self.state.set_talk(False)
        self.assertEqual(released["last_event"], "talk.stopped")

    def test_talk_requires_lesson(self):
        with self.assertRaisesRegex(StateError, "select a lesson"):
            self.state.set_talk(True)

    def test_privacy_lock_forces_talk_stop_and_fails_closed(self):
        self.state.select_card("letter-a")
        self.state.set_talk(True)
        locked = self.state.set_privacy(mic_enabled=False)
        self.assertFalse(locked["talk_active"])
        self.assertFalse(locked["mic_enabled"])
        with self.assertRaisesRegex(StateError, "privacy lock"):
            self.state.set_talk(True)

    def test_unknown_card_is_rejected(self):
        with self.assertRaisesRegex(StateError, "unknown lesson"):
            self.state.select_card("invented-card")


if __name__ == "__main__":
    unittest.main()
