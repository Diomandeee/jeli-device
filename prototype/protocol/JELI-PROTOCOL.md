# Jeli device protocol v1

Transport for the first bench build is newline-delimited UTF-8 JSON over USB serial. This keeps the body local and inspectable. BLE or Wi-Fi transport can be added later without changing message semantics.

Every message contains:

```json
{"v":1,"type":"device.ping"}
```

## Browser/iPhone to body commands

- `card.select` — identify the canonical lesson card selected by the brain.
- `display.lesson` — give the body already-approved display text.
- `motion.look` — set bounded yaw `15...165` and pitch `35...145` degrees.
- `privacy.set` — reflect a deliberate physical privacy transition.
- `audio.play` — request playback of an approved local asset identifier.
- `device.ping` — liveness check.

## Body to browser/iPhone events

- `device.ready`, `device.pong`, `device.error`
- `talk.started`, `talk.stopped`
- `privacy.changed`
- `motion.changed`
- `card.detected` when a PN532 adapter is attached
- `adapter.pending` while a commanded peripheral still uses a stub

## Authority boundary

The ESP32-S3 never decides linguistic correctness. It reports buttons, shutters, tags, and motion state and renders content selected by the phone/local brain. Pronunciation scoring is forbidden in v1. Audio capture must be press-to-talk and visibly indicated by the physical status light.

