import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from jeli.server import make_server


class JeliServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        self.post("/api/reset", {})

    def get(self, path):
        with urlopen(self.base + path, timeout=2) as response:
            return response.status, response.headers, response.read()

    def post(self, path, payload):
        request = Request(
            self.base + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            return json.loads(response.read())

    def test_health_static_and_security_headers(self):
        status, headers, body = self.get("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["ok"])
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        status, _, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Jeli", body)

    def test_api_transition_and_privacy_gate(self):
        self.post("/api/card", {"card_id": "greeting-afternoon"})
        self.assertTrue(self.post("/api/talk", {"active": True})["talk_active"])
        locked = self.post("/api/privacy", {"mic_enabled": False})
        self.assertFalse(locked["talk_active"])
        request = Request(
            self.base + "/api/talk",
            data=b'{"active":true}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=2)
        self.assertEqual(caught.exception.code, 409)
        caught.exception.close()

    def test_boolean_fields_reject_truthy_strings(self):
        request = Request(
            self.base + "/api/privacy",
            data=b'{"mic_enabled":"false"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=2)
        self.assertEqual(caught.exception.code, 409)
        caught.exception.close()


if __name__ == "__main__":
    unittest.main()
