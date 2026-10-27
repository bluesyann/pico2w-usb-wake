# Pico 2 W USB Wake Service

A Raspberry Pi Pico 2 W joins a WiFi network and exposes a small HTTP page. A request to `/wake` makes it signal USB remote wakeup and send one configurable key stroke to the connected computer.

## Requirements

- Raspberry Pi Pico 2 W connected to the computer by USB
- MicroPython firmware for Pico 2 W with `machine.USBDevice` support
- The MicroPython USB device library modules listed below
- A 2.4 GHz WiFi network reachable by the Pico
- A host computer that supports USB keyboard wake from sleep and allows this USB device to wake it

The firmware was developed with MicroPython 1.29.0 on the Pico 2 W. USB remote wake support and host power settings vary by computer and operating system.

## Files

Copy these four files to the root of the Pico's filesystem, preserving their names:

```text
main.py
usb_core.py
usb_hid.py
usb_keyboard.py
```

The three `usb_*.py` modules are the micropython-lib USB device core, HID, and keyboard modules, adjusted to import each other as root-level files. They are kept flat so they can be uploaded without creating directories. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for upstream sources and license terms.

## Configure

Before uploading, edit `main.py` and replace the WiFi placeholders:

```python
WIFI_SSID = "your-wifi-name"
WIFI_PASSWORD = "your-wifi-password"
```

Use a DHCP reservation in your router if you want the Pico's printed IP address to remain stable. Avoid committing real WiFi credentials to a public repository.

The default `TEST_MODE = False` enables USB keyboard mode. `KEY_CODE` selects the key sent on a request; it is set to `KeyCode.DOWN` in the current configuration.

## Use

1. Upload all four files to the Pico's root directory.
2. Reset or power-cycle the Pico.
3. Wait for the serial output to show `WiFi connected, IP: ...` and `HTTP server listening on port 80`.
4. On a device on the same LAN, open `http://<pico-ip>/` and press **Wake up**, or send a request directly:

   ```sh
   curl http://<pico-ip>/wake
   ```

The Pico attempts USB remote wakeup, waits briefly for the host to resume, then presses and releases the configured key. The root page also includes a button that calls `/wake`.

## USB Serial Recovery

By default, the Pico starts without the built-in USB CDC serial interface, so it does not appear as a MicroPython serial device during normal use. To enable USB serial for one boot, press and release the onboard BOOTSEL button during the first 10 seconds after the program starts. The press must last between 50 ms and 1 second. A held press does not select recovery mode.

The BOOTSEL check is supported by the RP2 `rp2.bootsel_button()` API. If it is unavailable in the firmware, the program continues with USB serial disabled.

## LED Indicators

- WiFi disconnected or connecting: 100 ms flash once per second
- WiFi connected: 100 ms flash every 10 seconds
- Wake request received: on for one second

## Host Wake Settings

USB remote wake must be supported and enabled by the host. Depending on the operating system, enable the option allowing the Pico's HID keyboard to wake the computer. Some systems also require a BIOS/UEFI setting such as **USB wake**. A keyboard stroke cannot wake a computer if the USB port is unpowered during sleep.

## Security

The Pico HTTP service has no authentication or TLS. Keep it on a trusted LAN; do not expose port 80 directly to the Internet. If a separate authenticated service or tunnel relays requests to the Pico, protect that public entry point with access controls.