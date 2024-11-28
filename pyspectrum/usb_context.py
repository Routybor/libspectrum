import platform

if platform.system() == "Windows" or platform.system() == "Darwin":
    import ftd2xx as ftd
else:
    import pylibftdi as ftdi


class UsbContext:
    def __init__(self):
        self.device = None
        self.is_linux = platform.system() != "Windows" and platform.system() != "Darwin"

    def open(self):
        if self.is_linux:
            self.device = ftdi.Device()
            self.device.open()
        else:
            self.device = ftd.open()

        if not self.device:
            raise RuntimeError("Failed to open device")

    def close(self):
        if self.device:
            if self.is_linux:
                self.device.close()
            else:
                self.device.close()

    def set_bitmode(self, mask, enable):
        if self.is_linux:
            self.device.ftdi_fn.ftdi_set_bitmode(mask, enable)
        else:
            self.device.setBitMode(mask, enable)

    def set_timeouts(self, read_timeout_millis: int, write_timeout_millis: int):
        if self.is_linux:
            self.device.ctx.usb_read_timeout = read_timeout_millis
            self.device.ctx.usb_write_timeout = write_timeout_millis
        else:
            self.device.setTimeouts(read_timeout_millis, write_timeout_millis)

    def read(self, size) -> bytes:
        try:
            return self.device.read(size)
        except Exception:
            raise RuntimeError("Device read error")

    def write(self, data: bytes) -> int:
        try:
            return self.device.write(data)
        except Exception:
            raise RuntimeError("Device write error")
