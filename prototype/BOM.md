# Jeli prototype bench BOM

This list is for the personal prototype using the hardware already available where possible. Exact module dimensions and board pinouts must be checked before the shell is revised or any full enclosure is printed.

## Core

- 1 Raspberry Pi 4 or 5 Model B — local Jeli API, lesson content, display service, camera service, and offline runtime; identify the owned model before assembly
- 1 Arducam B0478 48 MP USB camera — documented 34 × 34 mm board; measure the owned enclosure and lens depth
- 1 iPhone or local browser host — retained initially for the already validated speech/CoreML path and as a development console
- 1 ESP32-S3 development board with native USB, optional — deterministic servos, buttons, LEDs, and hard privacy events
- USB-C data and power cables with measured bend clearance
- 1 regulated 5 V supply rated at least 2 A for the servo rail, with common ground to the controller
- Breadboard or perfboard, wire, connectors, and strain relief

## Interaction

- 1 SPI IPS display, nominally 2.0–2.4 inches; CAD proxy is 64 × 48 × 8 mm
- 1 PN532 NFC module in I2C mode; CAD proxy is 50 × 40 × 6 mm
- 4 or more NFC cards/tags for lesson cards
- 1 momentary talk button, nominally 28 mm
- 1 latching microphone privacy switch
- 1 microswitch for the mechanical camera-shutter state
- 1 visible status LED or addressable LED ring/diffuser

## Motion and audio

- 2 SG90-class micro servos; CAD proxy is 23 × 12.2 × 29 mm each
- 1 40 mm, 8 ohm, 3 W speaker; CAD proxy is 40 × 14 mm
- 1 MAX98357A-class I2S mono amplifier

## Shell hardware

- Printed Jeli shell parts from `../stl/`
- `pi_carrier.stl`, `arducam_carrier.stl`, and `power_bank_sled.stl` for reversible prototype integration
- M3 screws, matching heat-set inserts, and rubber feet
- M2.5 screws or removable straps for the Pi carrier after the owned board is measured
- Certified removable USB-C power bank that meets the owned Pi's verified input requirements; no DIY lithium pack
- PLA or PETG for the first fit prototypes

## Deliberately excluded

- DIY battery and charging circuit
- Cloud account or hosted backend
- Always-on microphone
- Automatic pronunciation-scoring hardware
