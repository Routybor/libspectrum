import struct
import numpy as np

from dataclasses import dataclass
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, MSG_WAITALL

from .data import Frame

# Идентификаторы типа команды CMD_OPCODE:
CMD_READ_INI            = 0x800B  # Прочитать конфигурационный файл
CMD_READ_ASSEMBLY_SWAP  = 0x8013  # Прочитать информацию о перестановках
CMD_READ_MULTILINE      = 0x0005  # Старт регистрации последовательности из N кадров
CMD_SET_LINE_LENGTH     = 0x000C  # Задать количество считываемых пикселей в детекторе
CMD_SET_LINE_NUMBER     = 0x0010  # Задать количество запрашиваемых кадров (N)
CMD_SET_TIMER           = 0x0002  # Задать значение таймера продолжительности экспозиции

UDP_PORT = 555
TCP_PORT = 556
UDP_BUFFER_SIZE = 65536


@dataclass
class EthernetDeviceIni:
    """
    Информация о содержании конфигурационного файла устройства.

    Attributes:
        num_chips: общее количество кристаллов в сборке принимает значения от 1 до 255
        num_pixels_per_chip: количество фоточувствительных пикселей единичного кристалла сборки
        chip_type: тип кристалла, коды приведены в таблице
        adc_rate: период оцифровки АЦП
        config_bits: флаги 8 бит, конфигурирующие режим управления многоэлементными фотодетекторами
        assembly_type: способ построения сборки
        min_exposure: минимальное время экспозиции
        num_pixels: суммарное количество пикселей при чтении всех фотодетекторов гибридной сборки
        mtr0: требуемая температура радиатора в градусах Цельсия, значение пишется во float 32-бит, big-endian
        mui0: напряжение сигнала Ui0 в вольтах
        dia_present: флаг наличия записанной диаграммы. При наличие, равен 0xAB
        thermostat_enabled: флаг включенного термостата(стабилизации температуры радиатора на значении mTr0). Во включенном состоянии, равен 0xAB
    """
    num_chips: int
    num_pixels_per_chip: int
    chip_type: int
    adc_rate: int
    config_bits: int
    assembly_type: int
    min_exposure: float
    num_pixels: int
    mtr0: float
    mui0: float
    dia_present: bool
    thermostat_enabled: bool


class EthernetDevice:
    """
    Класс, предоставляющий интерфейс для взаимодействия со Спектрометром через:
    - Управляющий протокол, работающий в режиме запрос-ответ (UDP)
    - Протокол передачи данных (TCP)
    """

    def __init__(self, addr: str):
        """
        :param str addr: IP адресс устройства
        """
        self._device_addr = addr
        self._seq_number = 1

        self.udp_sock = socket(AF_INET, SOCK_DGRAM)
        self.tcp_sock = socket(AF_INET, SOCK_STREAM)
        self.tcp_sock.connect((addr, TCP_PORT))

        self._ini = self._read_ini()

        self._opened = True

    def close(self):
        """ Закрывает TCP и UDP сокеты """
        self.tcp_sock.close()
        self.udp_sock.close()

    @property
    def isOpened(self) -> bool:
        """
        :return: True если со открыт для работы
        :rtype: bool
        """
        return self._opened

    def _send_command(self, opcode, data=b'', ext_packets=0, pad_to=16):
        """
        Отправляет команду устройству и обрабатывает ответ.

        :param opcode: идентификатор типа команды (2 байта)
        :param bytes data: данные для отправки в управляющем пакете (по умолчанию пусто)
        :param int ext_packets: Кол-во доп. пакетов для ожидания (по умолчанию 0)
        :param int pad_to: Размер padding-а (по умолчанию 16 байт)

        :return: список из (1 + ext_packets)  `RESP_DATA` частей ответных пакетов
        :rtype: list[bytes]

        Алгоритм работы Устройства:
        1) Устройство принимает управляющие UDP пакеты на порт 555
        2) Выполняет запрошенную команду
        3) Отправляет пакет с подтверждением на IP адрес и порт отправителя
        4) Ответный пакет отправляется в любом случае, даже если команда завершилась неудачей

        Управляющие пакеты и пакеты ответов состоят из 16-битных слов(W).

        Структура управляющего пакета:
        - `[CMD_OPCODE(W) | SEQ_NUM(W) | DATA(n*W) | padding]`
        - `SEQ_NUM` - номер отправленного пакета.

        Структура пакета ответа:
        - `[RESP_OPCODE(W) | padding(W) | CMD_OPCODE(W) | SEQ_NUM(W) | RESP_DATA(n*W)]`
        - Полученый `SEQ_NUM` возвращается в ответе на посланную команду в неизменном виде.
        - `RESP_OPCODE` - код ответа

        На ряд команд Устройство помимо пакета с ответом отправляет дополнительные пакеты.
        Такие пакеты имеют структуру аналогичную пакету ответа, но `RESP_OPCODE` = `UDP_EXT`.
        """
        packet = struct.pack('<HH', opcode, self._seq_number)
        packet += data
        packet += bytes([0]*(pad_to-4-len(data)))

        self.udp_sock.sendto(packet, (self._device_addr, UDP_PORT))

        response_data = []

        for _ in range(1 + ext_packets):
            response = self.udp_sock.recvfrom(UDP_BUFFER_SIZE)[0]
            resp_opcode, ans_opcode, resp_seq_num = struct.unpack('<H2xHH', response[:8])

            if resp_seq_num != self._seq_number:
                raise Exception(f"Response sequence number mismatch: expected {self._seq_number}, got {resp_seq_num}")
            if ans_opcode != opcode:
                raise Exception(f"Response opcode mismatch: expected {opcode}, got {resp_opcode}")
            if resp_opcode > 2:
                raise Exception(f'Unsuccessful response code: {resp_opcode}')

            response_data.append(response[8:])

        self._seq_number = (self._seq_number + 1) & 0xFFFF # stay in 16 bits range
        return response_data

    def setTimer(self, millis: int):
        """
        Выставляет продолжительность единичного кадра (накопления) - время базовой экспозиции `τ`

        :param int millis: время базовой экспозиции в мс

        Базовое время экспозиции определяется из мантиссы и экспоненты таймера как:

        `τ = 0.1 ms * mant * 10 ^ exp`

        Размеры мантиссы и экспоненты:
            Мантиса таймера - 10 бит
            Экспонента таймера - 2 бита
        """
        if millis < self._ini.min_exposure:
            raise Exception(f'Exposure too low, minimal is {self._ini.min_exposure}')

        millis *= 10
        exponent = 0
        while millis >= (1 << 10):
            exponent += 1
            millis //= 10
        if exponent >= 4:
            raise Exception("Exposure too big")

        self._send_command(
            CMD_SET_TIMER,
            data=struct.pack('<H2xH', millis, exponent)
        )

    def readFrame(self, n_times):
        ini = self._ini
        self._set_line_length(ini.num_pixels, ini.num_chips)
        arr = np.empty((n_times, ini.num_pixels), dtype=np.uint16)
        self._send_command(CMD_READ_MULTILINE, struct.pack('<H2xI', 0, n_times))
        self.tcp_sock.recv_into(arr, n_times * ini.num_pixels * 2, MSG_WAITALL)
        measurement_header = np.array([0, 0, 0x8000, 0x8000, 0xabab, 0xabab])
        header_len = len(measurement_header)
        for i in range(n_times):
            if not np.array_equal(measurement_header, arr[i][:header_len]):
                raise Exception('Invalid measurement header')

        samples = arr[:, header_len:].astype('int32')
        # TODO: clipped support
        return Frame(samples=samples, clipped=np.zeros(samples.shape))

    def _read_ini(self) -> EthernetDeviceIni:
        """
        Прочитать конфигурацию устройства.

        :return: Конфигурация устройства
        :rtype: EthernetDeviceIni
        """
        data = self._send_command(CMD_READ_INI, data=bytes([0]), ext_packets=1)[1]
        chips_num, chip_pixel_num, chip_type, adc_rate, config_bits, assembly_type, min_exposure_value, min_exposure_exponent, pixel_number, dia_present, termostat_en, temp0, v0 = struct.unpack('<B3xHHBBxBHHIBBff', data[:30])
        return EthernetDeviceIni(
            num_chips=chips_num,
            num_pixels_per_chip=chip_pixel_num,
            chip_type=chip_type,
            adc_rate=adc_rate,
            config_bits=config_bits,
            assembly_type=assembly_type,
            min_exposure=0.1*min_exposure_value*(10**min_exposure_exponent),
            num_pixels=pixel_number,
            mtr0=temp0,
            mui0=v0,
            dia_present=(dia_present == 0xAB),
            thermostat_enabled=(termostat_en == 0xAB),
        )

    def _set_line_length(self, num_pixels: int, num_chips: int):
        """
        Позволяет конфигурировать количество опрашиваемых фотодетекторов в гибридной
        сборке фотодетекторов и количество опрашиваемых пикселей для каждого из фотодетекторов.

        :param int num_pixels: суммарное количество пикселей при чтении всех фотодетекторов гибридной сборки (4 байта)
        :param int num_chips: количество опрашиваемых фотодетекторов (кол-во линеек фотодиодов) (2 байта)

        Если отправить команду со значением num_chips или num_pixels равным 0, то
        при выполнении команды возьмутся стандартные значения для данной сборки фотодетекторов,
        хранящиеся в конфигурационном файле Устройства.
        """
        self._send_command(
            CMD_SET_LINE_LENGTH,
            struct.pack('<IH', num_pixels, num_chips)
        )
