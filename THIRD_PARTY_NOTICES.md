# Third-Party Notices

## MicroPython USB Device Modules

The following files are vendored from the USB device packages in
[micropython/micropython-lib](https://github.com/micropython/micropython-lib/tree/master/micropython/usb):

- `usb_core.py` is based on `usb-device/usb/device/core.py`.
- `usb_hid.py` is based on `usb-device-hid/usb/device/hid.py`.
- `usb_keyboard.py` is based on `usb-device-keyboard/usb/device/keyboard.py`.

The imports between these modules were adjusted to work with this project's
flat Pico filesystem layout. The upstream copyright notices are retained in
each source file.

Copyright notices:

- `usb_core.py`: Copyright (c) 2022-2024 Angus Gratton
- `usb_hid.py`: Copyright (c) 2023 Angus Gratton
- `usb_keyboard.py`: Copyright (c) 2023-2024 Angus Gratton

These modules are distributed under the MIT License:

```text
MIT License

Copyright (c) 2022-2024 Angus Gratton

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```