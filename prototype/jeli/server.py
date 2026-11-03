"""Dependency-free localhost server for the Jeli browser prototype."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import urlparse

from .state import JeliState, StateError


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"
LESSONS_PATH = ROOT / "content" / "lessons.json"


class JeliHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: Tuple[str, int], state: JeliState):
        super().__init__(address, JeliHandler)
        self.state = state


class JeliHandler(BaseHTTPRequestHandler):
    server: JeliHTTPServer
    server_version = "JeliPrototype/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json({"ok": True, "service": "jeli-local", "version": "0.1.0"})
        elif path == "/api/state":
            self._json(self.server.state.snapshot())
        elif path == "/api/lessons":
            self._json({"lessons": self.server.state.lessons})
        elif path.startswith("/api/"):
            self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
        else:
            self._static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/card":
                response = self.server.state.select_card(str(payload.get("card_id", "")))
            elif path == "/api/talk":
                active = self._optional_bool(payload, "active", required=True)
                response = self.server.state.set_talk(active)
            elif path == "/api/privacy":
                response = self.server.state.set_privacy(
                    mic_enabled=self._optional_bool(payload, "mic_enabled"),
                    camera_open=self._optional_bool(payload, "camera_open"),
                )
            elif path == "/api/reset":
                response = self.server.state.reset()
            else:
                self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
                return
            self._json(response)
        except (StateError, ValueError, json.JSONDecodeError) as error:
            self._json({"error": "invalid_transition", "detail": str(error)}, HTTPStatus.CONFLICT)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 16_384:
            raise ValueError("request body too large")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("request body must be an object")
        return payload

    @staticmethod
    def _optional_bool(payload: Dict[str, Any], key: str, required: bool = False):
        if key not in payload:
            if required:
                raise StateError(f"{key} is required")
            return None
        if not isinstance(payload[key], bool):
            raise StateError(f"{key} must be a boolean")
        return payload[key]

    def _json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _static(self, request_path: str) -> None:
        relative = "index.html" if request_path in ("", "/") else request_path.lstrip("/")
        candidate = (WEB_ROOT / relative).resolve()
        try:
            candidate.relative_to(WEB_ROOT.resolve())
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not candidate.is_file():
            candidate = WEB_ROOT / "index.html"
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; media-src 'self' blob:; img-src 'self' data:; object-src 'none'",
        )


def make_server(host: str = "127.0.0.1", port: int = 8787) -> JeliHTTPServer:
    return JeliHTTPServer((host, port), JeliState(LESSONS_PATH))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the private Jeli browser prototype")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8787, type=int)
    args = parser.parse_args()
    server = make_server(args.host, args.port)
    print(f"Jeli prototype: http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
