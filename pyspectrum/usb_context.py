import logging
import ftd2xx as ftd

# Настройка логгера
logging.basicConfig(
    filename='app.log',
    filemode='w',
    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)


class UsbContext:
    """
    Класс для работы с устройством FTDI через библиотеку ftd2xx на системе Windows.
    
    ### Пример использования:
    ```python
    context = UsbContext()
    context.open()
    context.set_bitmode(0x40, 0x40)
    context.set_timeouts(300, 300)
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
        logger.info('Attempt to open FTDI device')
        self.device = ftd.open()

        if not self.device:
            logger.error("Failed to open device", exc_info=True)
            raise RuntimeError
        else:
            logger.info('FTDI device opened successfully')

    def close(self):
        """
        Закрывает устройство FTDI.
        """
        if self.device:
            self.device.close()
            logger.info('FTDI device closed')

    def set_bitmode(self, mask, enable):
        """
        Устанавливает режим работы на устройстве FTDI.
        
        :param mask: Маска для установки режима работы пинов.
        :param enable: Режим работы FTDI чипа (0x40 - 245 FIFO Mode)
        """
        try:
            logger.info(f'Setting bitmode {enable} for mask {mask}')
            self.device.setBitMode(mask, enable)
            logger.info('Bitmode set successfully')
        except Exception as e:
            logger.error(f'Error occured during setting bitmode: {e}', exc_info=True)
            raise RuntimeError

    def set_timeouts(self, read_timeout_millis: int, write_timeout_millis: int):
        """
         Устанавливает таймауты чтения и записи для устройства FTDI.

        :param read_timeout_millis: Таймаут чтения в миллисекундах.
        :param write_timeout_millis: Таймаут записи в миллисекундах.
        """
        try:
            logger.info(f'Setting timeouts: reading {read_timeout_millis} ms, writing {write_timeout_millis} ms')
            self.device.setTimeouts(read_timeout_millis, write_timeout_millis)
            logger.info('Timeouts set successfully')
        except Exception as e:
            logger.error(f'Error occured during setting timeouts: {e}', exc_info=True)
            raise RuntimeError

    def read(self, size) -> bytes:
        """
         Читает данные из устройства FTDI.
        
        :param size: Количество байтов для чтения.
        :return: Прочитанные данные в виде байтовой строки.
        :raises RuntimeError: Если произошла ошибка при чтении данных.
        """
        try:
            logger.info(f'Reading {size} bytes from device')
            return self.device.read(size)
        except Exception as e:
            logger.error(f'Device read error: {e}')
            raise RuntimeError

    def write(self, data: bytes) -> int:
        """
        Записывает данные в устройство FTDI.

        :param data: Данные для записи в виде байтовой строки.
        :return: Количество записанных байтов.
        :raises RuntimeError: Если произошла ошибка при записи данных.
        """
        try:
            logger.info(f'Writing {len(data)} bytes in device')
            return self.device.write(data)
        except Exception as e:
            logger.error(f'Device write error: {e}', exc_info=True)
            raise RuntimeError