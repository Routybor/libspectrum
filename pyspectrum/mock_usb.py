import numpy as np
from .usb_device import UsbDevice
from .data import Frame


class MockUsbDevice(UsbDevice):
    def __init__(
        self,
        vendor: int,
        product: int,
        serial: str,
        read_timeout: int,
    ) -> None:
        """
        Мок-реализация USB устройства.
        """
        self._vendor = vendor
        self._product = product
        self._serial = serial
        self._read_timeout = read_timeout
        self._pixel_number = 0x1006  # Количество пикселей
        self._sequence_number = 1
        self._opened = True

    def close(self) -> None:
        """
        Закрывает соединение с мок-устройством.
        """
        if not self._opened:
            raise RuntimeError("Device is not opened.")
        self._opened = False

    @property
    def isOpened(self) -> bool:
        return self._opened

    def get_pixel_count(self) -> int:
        return self._pixel_number

    def _send_command(self, code: int, data: int) -> bytes:
        """
        Мок-реализация отправки команды. Возвращает фейковый успешный ответ.
        """
        return (
            b"#ANS\x2B\x02"
            + self._sequence_number.to_bytes(length=2, byteorder="little")
            + b"\x00\x00"
        )

    def readFrame(self, n_times: int) -> Frame:
        """
        Возвращает сгенерированные данные вместо чтения их с реального устройства.
        """
        pixel_count = self.get_pixel_count()
        samples = np.random.randint(
            low=0, high=65535, size=(n_times, pixel_count), dtype=np.uint16
        )
        clipped = np.random.choice(
            a=[False, True], size=(n_times, pixel_count), p=[0.95, 0.05]
        )
        return Frame(samples=samples, clipped=clipped)
