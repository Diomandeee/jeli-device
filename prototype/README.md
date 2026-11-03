# Jeli v0.1 local prototype

Jeli is an N'Ko learning companion prototype: a local browser device twin, a small state/API layer, a USB-serial body protocol, and an ESP32-S3 MicroPython target. It turns the existing Jeli shell concept into something testable without claiming the unbuilt electronics or linguistic scoring are complete.

## Run it

```bash
cd prototype
./run.sh
```

Open `http://127.0.0.1:8787`. Choose a lesson card, hold the amber button to capture your voice locally, and use the physical-style mic lock and camera shutter controls. Microphone permission is requested only when the talk button is held. Captured audio is held in a browser blob for replay and is destroyed when the page closes or resets.

Run the verification gate with:

```bash
python3 -m unittest discover -s tests -v
node --check web/app.js
python3 -m py_compile jeli/*.py firmware/*.py
```

## Prototype boundary

- Lesson cards were copied from my N'Ko data repository and keep their source paths.
- No automatic pronunciation score is presented.
- No audio is uploaded or persisted by the server.
- Camera capture is not implemented; the UI models the shell's mechanical shutter.
- The browser and ESP32 implementations meet at `protocol/JELI-PROTOCOL.md` but are not yet connected by a serial bridge.
- Firmware peripheral adapters remain explicit stubs until the exact modules are selected and bench-tested.
- The printable body is in `../cad` and `../stl`; the Pi dock is in `../dock`.

See `BOM.md` and `WIRING.md` for the planned electronics. They are bench plans, not a verified build.
