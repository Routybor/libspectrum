import ftd2xx as ftd


class UsbContext:
    """
    Класс для работы с устройством FTDI через библиотеку ftd2xx на системе Windows.
    
    ### Пример использования:
    ```
    context = UsbContext()
    context.open()
    context.set_bitmode(0x40, 0x40)
    context.set_timeouts(5000, 5000)
    # Ваш код для работы с устройством FTDI...
    context.close()
    ```
    """
    def __init__(self):
        self.device = None

    def open(self):
        """
        Открывает первое найденное устройство FTDI.
        
        :raises RuntimeError: Если устройство не найдено или невозможно его открыть.
        """
        self.device = ftd.open()

        if not self.device:
            raise RuntimeError("Failed to open device")

    def close(self):
        """
        Закрывает устройство FTDI.
        """
        if self.device:
            self.device.close()

    def set_bitmode(self, mask, enable):
        """
        Устанавливает режим работы на устройстве FTDI.
        
        :param mask: Маска для установки режима работы пинов.
        :param enable: Режим работы FTDI чипа (0x40 - 245 FIFO Mode)
        """
        self.device.setBitMode(mask, enable)

    def set_timeouts(self, read_timeout_millis: int, write_timeout_millis: int):
        """
         Устанавливает таймауты чтения и записи для устройства FTDI.

        :param read_timeout_millis: Таймаут чтения в миллисекундах.
        :param write_timeout_millis: Таймаут записи в миллисекундах.
        """
        self.device.setTimeouts(read_timeout_millis, write_timeout_millis)

    def read(self, size) -> bytes:
        """
         Читает данные из устройства FTDI.
        
        :param size: Количество байтов для чтения.
        :return: Прочитанные данные в виде байтовой строки.
        :raises RuntimeError: Если произошла ошибка при чтении данных.
        """
        try:
            return self.device.read(size)
        except Exception:
            raise RuntimeError("Device read error")

    def write(self, data: bytes) -> int:
        """
        Записывает данные в устройство FTDI.

        :param data: Данные для записи в виде байтовой строки.
        :return: Количество записанных байтов.
        :raises RuntimeError: Если произошла ошибка при записи данных.
        """
        try:
            return self.device.write(data)
        except Exception:
            raise RuntimeError("Device write error")