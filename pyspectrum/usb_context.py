import platform
import ftd2xx as ftd
import pylibftdi as ftdi


class UsbContext:
    def __init__(self):
        self.device = None
        self.is_linux = platform.system() != "Windows"

    def open(self, vendor, product, serial=""):
        if self.is_linux:
            self.device = ftdi.Device(device_id=serial,vid=vendor, pid=product)
            self.device.open()
        else:
            num_devs = ftd.createDeviceInfoList()
            for index in range(num_devs):
                info = ftd.getDeviceInfoDetail(index)
                if serial and serial != info['serial']:
                    continue
                if (info['id'] >> 16) & 0xFFFF == vendor and info['id'] & 0xFFFF == product:
                    self.device = ftd.open(index)
                    return
            raise RuntimeError("Device not found")

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
            self.device.ftdi_fn.ftdi_set_usb_read_timeout(read_timeout_millis)
            self.device.ftdi_fn.ftdi_set_usb_write_timeout(write_timeout_millis)
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
