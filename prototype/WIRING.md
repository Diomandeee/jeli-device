# Jeli v0.1 provisional wiring

The GPIO map is a bench hypothesis, not a manufacturing pinout. Reconcile it against the exact ESP32-S3 board before applying power. Do not power either servo from the 3.3 V rail.

| Function | GPIO / bus | Notes |
| --- | ---: | --- |
| Talk button | 4 | Input pull-up; button to ground |
| Mic privacy switch | 5 | Input pull-up; locked position to ground |
| Shutter microswitch | 3 | Input pull-up; open state to ground |
| Status LED | 48 | Board-dependent; confirm whether GPIO48 drives the onboard LED |
| Yaw servo signal | 17 | Servo power from separate regulated 5 V rail |
| Pitch servo signal | 18 | Servo power from separate regulated 5 V rail |
| PN532 SDA / SCL | 8 / 9 | I2C; confirm module voltage and pull-ups |
| Display SCK / MOSI | 12 / 11 | SPI |
| Display CS / DC | 10 / 13 | SPI control |
| Display reset / backlight | 14 / 15 | Confirm backlight current requirement |
| I2S BCLK / LRCLK / DATA | 16 / 7 / 6 | ESP32 to MAX98357A input |

## Power topology

```text
USB host ──USB-C── ESP32-S3
                    │ 3.3 V logic
                    ├── display / PN532, only if their modules support it
                    └── GPIO signals

regulated 5 V ≥2 A ─┬── yaw servo
                     └── pitch servo

all grounds ─────────── common ground
```

Bench-test each servo separately with conservative travel limits before installing the yoke. The firmware bounds commanded motion to yaw 15–165 degrees and pitch 35–145 degrees, but the real safe range must be calibrated mechanically.
