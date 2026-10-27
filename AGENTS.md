# Agent Instructions

## Project Scope

This repository contains MicroPython firmware for a Raspberry Pi Pico 2 W that exposes a WiFi HTTP wake trigger and acts as a USB HID keyboard.

## Firmware Constraints

- Keep code compatible with the MicroPython RP2 port and the target Pico 2 W firmware.
- The board upload layout is flat: `main.py`, `usb_core.py`, `usb_hid.py`, and `usb_keyboard.py` are uploaded to the filesystem root. Preserve the root-level imports unless intentionally changing the upload instructions too.
- The normal boot path must use `builtin_driver=False`; short BOOTSEL press detection during the initial 10-second window is the recovery path that enables the built-in USB CDC interface.
- Preserve USB remote wake configuration (`remote_wakeup=True`) and key press/release behavior when modifying wake logic.
- Avoid CPython-only APIs and dependencies in firmware code. `python -m py_compile` checks syntax only; it does not validate MicroPython hardware behavior.
- Preserve third-party copyright/license headers in the vendored USB modules; record upstream provenance or changes in `THIRD_PARTY_NOTICES.md`.

## Configuration and Security

- Never commit real WiFi credentials, tokens, or other private configuration. Keep placeholders in tracked firmware and documentation.
- The HTTP listener is unauthenticated. Do not add instructions to expose it directly to the public Internet; public access must go through a protected relay.
- Document changes to required board files, firmware support, boot behavior, HTTP routes, or host setup in `README.md`.

## Validation

- Run a Python syntax check for edited `.py` files.
- For changes involving USB, WiFi, BOOTSEL, GPIO, or LED timing, clearly distinguish syntax validation from actual on-board testing.
- Keep changes focused and preserve the existing simple MicroPython structure.