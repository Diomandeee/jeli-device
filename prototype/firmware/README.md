# ESP32-S3 body target

This is a MicroPython bench target, chosen because it needs no framework-specific application code and keeps the body/controller boundary visible.

Copy `boot.py`, `main.py`, and `jeli_protocol.py` to a MicroPython-capable ESP32-S3 after the exact board is selected and flashed. The current Mac has no `esptool`, MicroPython image, or confirmed ESP32 serial device, so nothing has been flashed.

The GPIO assignments are provisional and must be reconciled against the purchased board's pinout. Servos require a separate regulated 5 V supply with common ground; never power two SG90-class servos from the ESP32's 3.3 V rail.

PN532, display, and I2S speaker handlers are explicit adapter seams. The firmware emits `adapter.pending` until the real module drivers and dimensions are verified.

