# Pico 2 W: USB keyboard + WiFi HTTP trigger to wake the host computer.
#
# Files to copy to the board root: main.py, usb_core.py, usb_hid.py,
# usb_keyboard.py.
#
# Open http://<board-ip>/ from another device and press the button: the board
# remote-wakes the host over USB and sends one keystroke.
#
# TEST_MODE = True keeps the runtime USB device unconfigured, so the serial
# REPL (and its prints) stays connected. Requests then only print
# "Wake up request received !". Set TEST_MODE = False for real operation.
#
# Host-side prerequisites for wakeup (see previous notes): the OS must allow
# this HID device to wake the computer, and the BIOS must allow USB wake.

import socket
import time

import network
import rp2
import usb_core
from machine import Pin, USBDevice
from usb_keyboard import KeyCode, KeyboardInterface

TEST_MODE = False

WIFI_SSID = "ssid"
WIFI_PASSWORD = "password"
WIFI_RETRY_MS = 10000
WIFI_POLL_MS = 50
BOOTSEL_WINDOW_MS = 10000
BOOTSEL_POLL_MS = 20
BOOTSEL_MIN_PRESS_MS = 50
BOOTSEL_MAX_PRESS_MS = 1000

HTTP_PORT = 80
LED_FLASH_MS = 100
LED_REQUEST_MS = 1000
LED_WIFI_INTERVAL_MS = 1000
LED_CONNECTED_INTERVAL_MS = 10000

KEY_CODE = KeyCode.DOWN  # HID keycode sent to wake the host
KEY_HOLD_MS = 20  # time the key stays pressed before release
RESUME_DELAY_MS = 1000  # let the host resume polling after remote wakeup
ENUMERATION_TIMEOUT_MS = 10000
USB_POLL_MS = 100

INDEX_HTML = """<!DOCTYPE html>
<html><head><title>Wake on USB</title></head>
<body style="font-family:sans-serif;text-align:center;margin-top:4em">
<h1>Wake on USB</h1>
<form action="/wake" method="get">
<button style="font-size:2em;padding:0.5em 1em">Wake up</button>
</form></body></html>
"""

DONE_HTML = """<!DOCTYPE html>
<html><head><title>Wake on USB</title>
<meta http-equiv="refresh" content="2;url=/"></head>
<body style="font-family:sans-serif;text-align:center;margin-top:4em">
<h1>Wake up request sent</h1></body></html>
"""

ERROR_HTML = """<!DOCTYPE html>
<html><head><title>Wake on USB</title></head>
<body style="font-family:sans-serif;text-align:center;margin-top:4em">
<h1>Not found</h1><p><a href="/">Back</a></p></body></html>
"""


class StatusLed:
    """Show WiFi state with short pulses and requests with a long pulse."""

    def __init__(self):
        self._pin = Pin("LED", Pin.OUT)
        self._connected = False
        self._pulse_until = None
        self._request_until = None
        self._next_flash = time.ticks_add(time.ticks_ms(), LED_WIFI_INTERVAL_MS)
        self._is_on = False
        self._pin.off()

    def _set(self, is_on):
        if self._is_on != is_on:
            self._pin.value(1 if is_on else 0)
            self._is_on = is_on

    def update(self, connected):
        now = time.ticks_ms()
        if connected != self._connected:
            self._connected = connected
            interval = LED_CONNECTED_INTERVAL_MS if connected else LED_WIFI_INTERVAL_MS
            self._next_flash = time.ticks_add(now, interval)
            self._pulse_until = None

        if self._request_until is not None:
            if time.ticks_diff(self._request_until, now) > 0:
                self._set(True)
                return
            self._request_until = None
            interval = LED_CONNECTED_INTERVAL_MS if connected else LED_WIFI_INTERVAL_MS
            self._next_flash = time.ticks_add(now, interval)
            self._pulse_until = None
            self._set(False)
            return

        if self._pulse_until is not None:
            if time.ticks_diff(self._pulse_until, now) > 0:
                self._set(True)
                return
            self._pulse_until = None
            self._set(False)

        if time.ticks_diff(now, self._next_flash) >= 0:
            interval = LED_CONNECTED_INTERVAL_MS if connected else LED_WIFI_INTERVAL_MS
            self._next_flash = time.ticks_add(now, interval)
            self._pulse_until = time.ticks_add(now, LED_FLASH_MS)
            self._set(True)
        else:
            self._set(False)

    def request_flash(self):
        now = time.ticks_ms()
        self._request_until = time.ticks_add(now, LED_REQUEST_MS)
        self._pulse_until = None
        self._set(True)

    def off(self):
        self._request_until = None
        self._pulse_until = None
        self._set(False)


def connect_wifi(led):
    """Join WiFi, showing the disconnected pulse pattern while retrying."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    last_attempt = None
    while not wlan.isconnected():
        led.update(False)
        now = time.ticks_ms()
        if last_attempt is None or time.ticks_diff(now, last_attempt) >= WIFI_RETRY_MS:
            print("Connecting to WiFi", WIFI_SSID)
            try:
                wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            except OSError as exc:
                print("WiFi connection attempt failed:", exc)
            last_attempt = now
        time.sleep_ms(WIFI_POLL_MS)
    led.update(True)
    print("WiFi connected, IP:", wlan.ifconfig()[0])
    return wlan


def select_builtin_driver(led):
    """Allow a short BOOTSEL press at startup to enable USB serial recovery."""
    if TEST_MODE:
        return False

    bootsel_button = getattr(rp2, "bootsel_button", None)
    if bootsel_button is None:
        print("BOOTSEL detection unavailable; using builtin_driver=False.")
        return False

    print("Press and release BOOTSEL within 10 seconds for USB serial access.")
    started_at = time.ticks_ms()
    pressed_at = None

    while time.ticks_diff(time.ticks_ms(), started_at) < BOOTSEL_WINDOW_MS:
        now = time.ticks_ms()
        is_pressed = bool(bootsel_button())
        led.update(False)

        if is_pressed and pressed_at is None:
            pressed_at = now
        elif not is_pressed and pressed_at is not None:
            press_ms = time.ticks_diff(now, pressed_at)
            pressed_at = None
            if BOOTSEL_MIN_PRESS_MS <= press_ms <= BOOTSEL_MAX_PRESS_MS:
                print("BOOTSEL short press detected; enabling USB serial.")
                return True

        time.sleep_ms(BOOTSEL_POLL_MS)

    print("No BOOTSEL short press; USB serial disabled.")
    return False


class UsbKeyboard:
    """USB HID keyboard able to wake a suspended host."""

    def __init__(self, led, builtin_driver):
        self._led = led
        self._keyboard = KeyboardInterface()
        usb_core.get().init(
            self._keyboard,
            builtin_driver=builtin_driver,
            remote_wakeup=True,
        )
        print("Waiting for USB keyboard to enumerate...")
        self._wait_for_host()
        print("USB keyboard ready.")

    def _wait_for_host(self):
        waited_ms = 0
        while not self._keyboard.is_open():
            self._led.update(True)
            if waited_ms >= ENUMERATION_TIMEOUT_MS:
                raise RuntimeError("USB keyboard was not enumerated by the host")
            time.sleep_ms(USB_POLL_MS)
            waited_ms += USB_POLL_MS

    def wake(self):
        """Remote-wake the host if it is suspended, then send one keystroke."""
        if self._remote_wakeup():
            time.sleep_ms(RESUME_DELAY_MS)  # host resumes polling
        self._keyboard.send_keys((KEY_CODE,))
        time.sleep_ms(KEY_HOLD_MS)
        self._keyboard.send_keys(())

    def release(self):
        """Release any key that may still be reported as pressed."""
        self._keyboard.send_keys(())

    @staticmethod
    def _remote_wakeup():
        try:
            return USBDevice().remote_wakeup()
        except OSError:
            return False


def parse_path(request):
    """Extract the URL path from a raw HTTP request, or None if malformed."""
    request_line = request.split(b"\r\n", 1)[0]
    parts = request_line.split(b" ")
    if len(parts) < 2:
        return None
    return parts[1].split(b"?")[0]


def send_response(conn, status, body):
    header = "HTTP/1.1 {}\r\nContent-Type: text/html\r\nConnection: close\r\nContent-Length: {}\r\n\r\n".format(
        status, len(body)
    )
    conn.send(header.encode())
    conn.send(body.encode())


def serve_forever(on_wake, led, wlan):
    """Serve HTTP requests; call on_wake() for each GET /wake."""
    while True:
        addr = socket.getaddrinfo("0.0.0.0", HTTP_PORT)[0][-1]
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(addr)
        server.listen(1)
        server.settimeout(0.1)
        print("HTTP server listening on port", HTTP_PORT)

        while wlan.isconnected():
            try:
                conn, _ = server.accept()
            except OSError:
                led.update(wlan.isconnected())
                continue

            try:
                path = parse_path(conn.recv(1024))
                if path == b"/wake":
                    on_wake()
                    send_response(conn, "200 OK", DONE_HTML)
                elif path == b"/":
                    send_response(conn, "200 OK", INDEX_HTML)
                elif path is None:
                    send_response(conn, "400 Bad Request", ERROR_HTML)
                else:
                    send_response(conn, "404 Not Found", ERROR_HTML)
            except OSError as exc:  # client disconnected mid-request
                print("HTTP error:", exc)
            finally:
                conn.close()

        server.close()
        wlan = connect_wifi(led)


def main():
    led = StatusLed()
    builtin_driver = select_builtin_driver(led)
    wlan = connect_wifi(led)

    keyboard = None if TEST_MODE else UsbKeyboard(led, builtin_driver)
    if TEST_MODE:
        print("TEST_MODE enabled: USB keyboard stays off, requests only print.")

    def on_wake():
        led.request_flash()
        print("Wake up request received !")
        if keyboard:
            keyboard.wake()

    try:
        serve_forever(on_wake, led, wlan)
    except KeyboardInterrupt:
        pass
    finally:
        if keyboard:
            keyboard.release()
        led.off()
        print("Finished.")


main()
