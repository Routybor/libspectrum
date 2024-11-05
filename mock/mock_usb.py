import random
import time
from threading import Thread
import usb.core
import usb.util


class MockUsbSpectrometer:
    def __init__(self, vid=0x0403, pid=0x6014, serial="") -> None:
        self.vid = vid
        self.pid = pid
        self.serial = serial
        self.device = None
        self.running = False

    def start(self) -> None:
        self.device = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        if self.device is None:
            print("Mock USB device initialized. Waiting for connection...")
        self.running = True
        self.thread = Thread(target=self._generate_data)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
        print("Mock USB device stopped.")

    def _generate_data(self) -> None:
        while self.running:
            time.sleep(1)
            data = [random.randint(0, 65535) for _ in range(2050)]
            print(f"Generated mock data: {data[:10]} ...")


if __name__ == "__main__":
    mock_device = MockUsbSpectrometer()
    mock_device.start()

    try:
        time.sleep(10000)
    finally:
        mock_device.stop()
