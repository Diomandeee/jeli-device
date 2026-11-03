import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "firmware"))
from jeli_protocol import ProtocolError, decode, encode, validate_command  # noqa: E402


class ProtocolTests(unittest.TestCase):
    def test_round_trip(self):
        message = decode(encode("device.ping", request_id="bench-1"))
        self.assertEqual(message["v"], 1)
        self.assertEqual(message["request_id"], "bench-1")

    def test_motion_bounds(self):
        command = validate_command(encode("motion.look", yaw=90, pitch=80))
        self.assertEqual(command["yaw"], 90)
        with self.assertRaisesRegex(ProtocolError, "yaw"):
            validate_command(encode("motion.look", yaw=180, pitch=80))

    def test_unknown_command_and_protocol_are_rejected(self):
        with self.assertRaisesRegex(ProtocolError, "unsupported command"):
            validate_command(encode("device.self-authorize"))
        with self.assertRaisesRegex(ProtocolError, "protocol version"):
            decode('{"v":2,"type":"device.ping"}')


if __name__ == "__main__":
    unittest.main()
