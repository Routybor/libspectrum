import struct
import time
import numpy as np

from .data import Frame
from .usb_context import UsbContext

CMD_CODE_WRITE_CR = 0x01
CMD_CODE_WRITE_TIMER = 0x02
CMD_CODE_WRITE_PIXEL_NUMBER = 0x0c
CMD_CODE_READ_ERRORS = 0x92
CMD_CODE_READ_VERSION = 0x91
CMD_CODE_READ_FRAME = 0x05

CMD_SUCCESS = 0x2B
CMD_FAILURE = 0x2D
CMD_UNKNOWN = 0x3F


class UsbDevice:
    """
    Класс для работы с USB устройством.
    
    Пример использования:
    ```python
    device = UsbDevice(vendor=0x0403, product=0x6014)
    device.set_timer(1)
    frame = device.read_frame(10)
    device.close()
    ```
    """
    def __init__(self, vendor: int, product: int, read_timeout=10000):
        """
        :param int vendor: Vendor ID USB устройства
        :param int product: Product ID USB устройства
        :param int read_timeout: Timeout для операций чтения (в миллисекундах)
        """
        self.context = UsbContext()
        self._read_timeout = read_timeout
        self._pixel_number = 0x1006
        self._sequence_number = 1

        self.context.open()
        self.context.set_bitmode(0x40, 0x40)
        self.context.set_timeouts(300, 300)

        self._send_command(CMD_CODE_WRITE_CR, 0)
        self._send_command(CMD_CODE_WRITE_TIMER, 0x03e8)
        self._send_command(CMD_CODE_WRITE_PIXEL_NUMBER, self._pixel_number)

        self._opened: bool = True

    def close(self):
        """
        Закрывает соединение с USB Спектрометром.
        """
        if not self._opened:
            raise RuntimeError("Device is not opened.")
        self.context.close()
        self._opened = False

    @property
    def is_opened(self) -> bool:
        """
        Открыто ли USB устройство.
        
        :return: True если USB Device открыт для работы
        :rtype: bool
        """
        return self._opened

    def get_pixel_count(self) -> int:
        """
        Возвращает кол-во пикселей в линии.
        
        :return: Кол-во пикселей
        :rtype: int
        """
        return self._pixel_number

    def _send_command(self, code: int, data: int) -> bytes:
        """
        Отправляет команду USB устройству и обрабатывает ответ.
        
        Структура пакета команды:
        ```
        - [ #CMD | CMD_CODE | CMD_LENGTH = 4 | SEQ_NUMBER | DATA ]
        - Длинна `DATA` определяется `CMD_LENGTH` ( <=4, мы всегда отправляем 4)
        - SEQ_NUMBER - 2 байта
        - всего: 12 байт
        ```

        Структура пакета ответа:
        ```
        - [ #ANS | ANS_CODE | ANS_LENGTH = 2 | SEQ_NUMBER | DATA ]
        - Полученый SEQ_NUMBER возвращается в ответе на посланную команду в неизменном виде.
        - ANS_CODE = CMD_SUCCESS | CMD_FALIURE | CMD_UNKNOWN
        - всего: 10 байт
        ```

        :param int code: Код команды(`CMD_CODE`)
        :param int data: Данные для посылки(`DATA`), мы посылаем 4 байта

        :return: 10-байтовый пакет ответа
        :rtype: bytes
        """

        command = struct.pack('<4sBBH4s',
                            b'#CMD',
                            code,
                            4,
                            self._sequence_number,
                            data.to_bytes(4, byteorder="little"))

        self.context.write(bytes(command))
        ans = self._read_exact(10)

        magic, ans_code, _, seq_number, _ = struct.unpack('<4sBBH2s', ans)

        if magic != b'#ANS':
            raise RuntimeError(f"Received bad answer magic: {magic}")
        elif seq_number != self._sequence_number:
            raise RuntimeError(
                f"SEQ_NUMBER number mismatch: sent {self._sequence_number}, "
                f"received {seq_number}"
            )
        elif ans_code == CMD_FAILURE:
            raise RuntimeError("Command was not completed")
        elif ans_code == CMD_UNKNOWN:
            raise RuntimeError(f"Unknown command: {code}")
        elif ans_code != CMD_SUCCESS:
            raise RuntimeError(f"Unexpected command status: {ans_code}")

        self._sequence_number = (self._sequence_number + 1) & 0xFFFF # stay in 16 bits range
        return ans

    def set_timer(self, millis: int):
        """
        Выставляет продолжительность единичного кадра (накопления) - время базовой экспозиции `τ`.
        
        Базовое время экспозиции определяется из мантиссы и экспоненты таймера как:

        `τ = 0.1 ms * mant * 10 ^ exp`

        Размеры мантиссы и экспоненты:
        
        - Мантиса таймера - `10 бит`
            
        - Экспонента таймера - `2 бита`

        Структура данных пакета команды:
        ```
        DATA[0] = мантисса, младший байт
        DATA[1] = мантисса, старший байт
        DATA[2] = экспонента
        DATA[3] = 0
        ```

        Поле `ANS_DATA` в ответе содержит 0.

        :param int millis: время базовой экспозиции в мс
        """
        millis *= 10
        exponent = 0
        while millis >= (1 << 10):
            exponent += 1
            millis //= 10
        if exponent >= 4:
            raise ValueError("Exposure too large")

        command_data = millis | (exponent << 16)
        self._send_command(CMD_CODE_WRITE_TIMER, command_data)

    def _read_exact(self, amount: int) -> bytes:
        """
        Читаем точное количество байт с USB устройства.

        :param int amount: кол-во байт на чтение
        """
        buffer = bytearray(amount)
        data_read = 0

        last_successful_read = time.monotonic_ns()
        while data_read < amount:
            chunk = self.context.read(amount - data_read)
            buffer[data_read:data_read+len(chunk)] = chunk
            data_read += len(chunk)

            current_time = time.monotonic_ns()
            if (current_time - last_successful_read > self._read_timeout * 1_000_000):
                raise RuntimeError("Device read timeout")
        return bytes(buffer)

    def _read_data(self, amount: int) -> bytes:
        """
        Читает данные, получаемые от USB устройства в пакетах данных `DAT`.

        Извлекает только `DATA` часть из каждого пакета с данными.
        
        Структура пакета данных:
        ```
        - [ #DAT | DATA_LENGTH | DATA ]
        - DATA_LENGTH - 2 байта (значение всегда четное)
        - DATA - минимум 400 байт (кроме последнего пакета)
        ```

        :param int amount: кол-во байт на чтение
        """
        buffer = bytearray(amount)
        data_read = 0

        while data_read < amount:
            header = self._read_exact(6)
            magic, length = struct.unpack('<4sH', header)

            if magic != b'#DAT':
                raise RuntimeError("Received bad #DAT magic from device")

            if length > (amount - data_read):
                raise ValueError("Trying to read more data than expected")

            buffer[data_read:data_read+length] = self._read_exact(length)
            data_read += length

        return bytes(buffer)

    def read_frame(self, n_times: int) -> Frame:
        """
        Читает кадр спектральных данных с USB спектрометра.
        
        Один кадр состоит из `n_times` накоплений/линий.
        
        Каждое накопление/линия в свою очередь состоит из `pixelNumber` пикселей в гибридной сборке фотодетекторов.
        
        - `pixelNumber` - устанавливается командой `CMD_CODE_WRITE_PIXEL_NUMBER`
        
        - Каждый пиксель - `2 байта`
        
        - Каждый кадр = `pixelNumber * n_times * 2 байт`

        :param int n_times: кол-во накоплений/линий (4 байта `DATA` поля команды)

        :return: Объект кадра
        :rtype: Frame
        """
        pixel_count = self.get_pixel_count()
        total_samples = pixel_count * n_times

        self._send_command(CMD_CODE_READ_FRAME, n_times)
        data = self._read_data(total_samples * 2)

        data_array = np.frombuffer(data, dtype=np.uint16)
        samples = data_array.reshape((n_times, pixel_count))
        samples = samples ^ (1 << 15)
        clipped = np.where(samples == np.iinfo(np.uint16).max, 1, 0)

        return Frame(samples=samples, clipped=clipped)