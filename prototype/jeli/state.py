"""Thread-safe state machine shared by the Jeli browser prototype."""

from __future__ import annotations

import copy
import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional


class StateError(ValueError):
    """A requested transition violates Jeli's interaction or privacy contract."""


class JeliState:
    def __init__(self, lessons_path: Path):
        payload = json.loads(lessons_path.read_text(encoding="utf-8"))
        lessons = payload.get("lessons")
        if not isinstance(lessons, list) or not lessons:
            raise ValueError("lessons.json must contain a non-empty lessons array")

        self._lessons: Dict[str, Dict[str, Any]] = {}
        for lesson in lessons:
            card_id = lesson.get("card_id")
            if not card_id or card_id in self._lessons:
                raise ValueError(f"invalid or duplicate card_id: {card_id!r}")
            self._lessons[card_id] = lesson

        self._lock = threading.RLock()
        self._revision = 0
        self._mode = "idle"
        self._selected_card_id: Optional[str] = None
        self._talk_active = False
        self._mic_enabled = True
        self._camera_open = False
        self._last_event = "prototype.ready"
        self._events: List[Dict[str, Any]] = []
        self._record_event("prototype.ready", {})

    @property
    def lessons(self) -> List[Dict[str, Any]]:
        return [copy.deepcopy(item) for item in self._lessons.values()]

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            card = self._lessons.get(self._selected_card_id)
            return {
                "revision": self._revision,
                "mode": self._mode,
                "selected_card_id": self._selected_card_id,
                "lesson": copy.deepcopy(card),
                "talk_active": self._talk_active,
                "recording_indicator": self._talk_active and self._mic_enabled,
                "mic_enabled": self._mic_enabled,
                "camera_open": self._camera_open,
                "last_event": self._last_event,
                "events": copy.deepcopy(self._events[-12:]),
                "trust": {
                    "pronunciation_scoring": False,
                    "audio_upload": False,
                    "camera_capture": False,
                    "authority": "canonical local corpus plus human review",
                },
            }

    def select_card(self, card_id: str) -> Dict[str, Any]:
        with self._lock:
            if card_id not in self._lessons:
                raise StateError(f"unknown lesson card: {card_id}")
            if self._talk_active:
                raise StateError("release the talk button before changing cards")
            self._selected_card_id = card_id
            self._mode = "card_ready"
            self._record_event("card.selected", {"card_id": card_id})
            return self.snapshot()

    def set_talk(self, active: bool) -> Dict[str, Any]:
        with self._lock:
            if active:
                if not self._mic_enabled:
                    raise StateError("microphone privacy lock is active")
                if self._selected_card_id is None:
                    raise StateError("select a lesson card before speaking")
                if not self._talk_active:
                    self._talk_active = True
                    self._mode = "listening"
                    self._record_event("talk.started", {"card_id": self._selected_card_id})
            elif self._talk_active:
                self._talk_active = False
                self._mode = "card_ready"
                self._record_event("talk.stopped", {"card_id": self._selected_card_id})
            return self.snapshot()

    def set_privacy(
        self,
        *,
        mic_enabled: Optional[bool] = None,
        camera_open: Optional[bool] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            changes: Dict[str, bool] = {}
            if mic_enabled is not None and bool(mic_enabled) != self._mic_enabled:
                self._mic_enabled = bool(mic_enabled)
                changes["mic_enabled"] = self._mic_enabled
                if not self._mic_enabled and self._talk_active:
                    self._talk_active = False
                    self._mode = "card_ready" if self._selected_card_id else "idle"
                    changes["talk_forced_stopped"] = True
            if camera_open is not None and bool(camera_open) != self._camera_open:
                self._camera_open = bool(camera_open)
                changes["camera_open"] = self._camera_open
            if changes:
                self._record_event("privacy.changed", changes)
            return self.snapshot()

    def reset(self) -> Dict[str, Any]:
        with self._lock:
            self._selected_card_id = None
            self._talk_active = False
            self._mic_enabled = True
            self._camera_open = False
            self._mode = "idle"
            self._record_event("prototype.reset", {})
            return self.snapshot()

    def _record_event(self, name: str, payload: Dict[str, Any]) -> None:
        self._revision += 1
        self._last_event = name
        self._events.append({"revision": self._revision, "type": name, "payload": payload})

