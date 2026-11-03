"""Jeli ESP32-S3 MicroPython bench firmware.

This target intentionally controls only the body. The iPhone/local browser is
the lesson and audio authority. NFC/display/audio integrations are adapters,
not hidden intelligence on the microcontroller.
"""

import sys
import time

try:
    import select
    import ujson as json
    from machine import Pin, PWM
except ImportError:  # Allows host syntax/import checks.
    select = None
    json = None
    Pin = None
    PWM = None

from jeli_protocol import ProtocolError, encode, validate_command


PINS = {
    "talk_button": 4,
    "privacy_switch": 5,
    "shutter_switch": 3,
    "status_led": 48,
    "servo_yaw": 17,
    "servo_pitch": 18,
    "i2c_sda": 8,
    "i2c_scl": 9,
    "display_sck": 12,
    "display_mosi": 11,
    "display_cs": 10,
    "display_dc": 13,
    "display_reset": 14,
    "display_backlight": 15,
    "i2s_bclk": 16,
    "i2s_lrclk": 7,
    "i2s_data": 6,
}


class JeliBody:
    def __init__(self):
        if Pin is None:
            raise RuntimeError("JeliBody requires MicroPython on an ESP32-S3")
        self.talk = Pin(PINS["talk_button"], Pin.IN, Pin.PULL_UP)
        self.privacy = Pin(PINS["privacy_switch"], Pin.IN, Pin.PULL_UP)
        self.shutter = Pin(PINS["shutter_switch"], Pin.IN, Pin.PULL_UP)
        self.led = Pin(PINS["status_led"], Pin.OUT, value=0)
        self.yaw = PWM(Pin(PINS["servo_yaw"]), freq=50)
        self.pitch = PWM(Pin(PINS["servo_pitch"]), freq=50)
        self.last = {
            "talk": self.talk.value(),
            "privacy": self.privacy.value(),
            "shutter": self.shutter.value(),
        }
        self.set_look(90, 90)
        self.emit("device.ready", pins=PINS, protocol=1)

    def emit(self, event_type, **payload):
        sys.stdout.write(encode(event_type, **payload))

    def set_look(self, yaw, pitch):
        self._servo_angle(self.yaw, yaw)
        self._servo_angle(self.pitch, pitch)
        self.emit("motion.changed", yaw=yaw, pitch=pitch)

    @staticmethod
    def _servo_angle(channel, angle):
        # SG90-class 50 Hz approximation. Calibrate endpoints on the real yoke.
        pulse_us = 500 + (float(angle) / 180.0) * 2000
        duty = int((pulse_us / 20_000.0) * 65_535)
        channel.duty_u16(duty)

    def poll_inputs(self):
        current = {
            "talk": self.talk.value(),
            "privacy": self.privacy.value(),
            "shutter": self.shutter.value(),
        }
        if current["talk"] != self.last["talk"]:
            active = current["talk"] == 0 and current["privacy"] != 0
            self.led.value(1 if active else 0)
            self.emit("talk.started" if active else "talk.stopped", active=active)
        if current["privacy"] != self.last["privacy"]:
            enabled = current["privacy"] != 0
            if not enabled:
                self.led.value(0)
            self.emit("privacy.changed", mic_enabled=enabled)
        if current["shutter"] != self.last["shutter"]:
            self.emit("privacy.changed", camera_open=current["shutter"] == 0)
        self.last = current

    def handle(self, raw):
        try:
            command = validate_command(raw)
            command_type = command["type"]
            if command_type == "motion.look":
                self.set_look(command["yaw"], command["pitch"])
            elif command_type == "device.ping":
                self.emit("device.pong", now=time.ticks_ms())
            elif command_type == "privacy.set":
                self.emit("privacy.commanded", mic_enabled=command.get("mic_enabled"))
            elif command_type in ("card.select", "display.lesson", "audio.play"):
                # Adapter seams: attach the real PN532/display/I2S drivers here.
                self.emit("adapter.pending", command=command_type)
        except ProtocolError as error:
            self.emit("device.error", detail=str(error))


def main():
    body = JeliBody()
    poller = select.poll()
    poller.register(sys.stdin, select.POLLIN)
    while True:
        body.poll_inputs()
        if poller.poll(0):
            line = sys.stdin.readline()
            if line:
                body.handle(line)
        time.sleep_ms(15)


if __name__ == "__main__":
    main()

