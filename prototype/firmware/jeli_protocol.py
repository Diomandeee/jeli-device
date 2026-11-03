"""Small JSON-line protocol that runs on CPython and MicroPython."""

try:
    import ujson as json
except ImportError:  # pragma: no cover - CPython path
    import json


PROTOCOL_VERSION = 1
COMMANDS = {
    "card.select",
    "display.lesson",
    "motion.look",
    "privacy.set",
    "audio.play",
    "device.ping",
}


class ProtocolError(ValueError):
    pass


def encode(message_type, **payload):
    if not isinstance(message_type, str) or not message_type:
        raise ProtocolError("message type is required")
    message = {"v": PROTOCOL_VERSION, "type": message_type}
    message.update(payload)
    return json.dumps(message) + "\n"


def decode(line):
    if isinstance(line, bytes):
        line = line.decode("utf-8")
    try:
        message = json.loads(line)
    except (ValueError, TypeError) as error:
        raise ProtocolError("invalid JSON") from error
    if not isinstance(message, dict):
        raise ProtocolError("message must be an object")
    if message.get("v") != PROTOCOL_VERSION:
        raise ProtocolError("unsupported protocol version")
    message_type = message.get("type")
    if not isinstance(message_type, str) or not message_type:
        raise ProtocolError("message type is required")
    return message


def validate_command(message):
    message = decode(message) if isinstance(message, (str, bytes)) else message
    if message.get("type") not in COMMANDS:
        raise ProtocolError("unsupported command")
    if message["type"] == "motion.look":
        yaw = message.get("yaw")
        pitch = message.get("pitch")
        if not isinstance(yaw, (int, float)) or not 15 <= yaw <= 165:
            raise ProtocolError("yaw must be between 15 and 165")
        if not isinstance(pitch, (int, float)) or not 35 <= pitch <= 145:
            raise ProtocolError("pitch must be between 35 and 145")
    return message

