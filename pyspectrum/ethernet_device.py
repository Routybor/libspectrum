from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, MSG_WAITALL
import struct
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from data import Frame

CMD_READ_INI            = 0x800B
CMD_READ_ASSEMBLY_SWAP  = 0x8013
CMD_READ_MULTILINE      = 0x0005
CMD_SET_LINE_LENGTH     = 0x000C
CMD_SET_LINE_NUMBER     = 0x0010
CMD_SET_TIMER           = 0x0002

udp_port = 555
tcp_port = 556
udp_buff_size = 65536


@dataclass
class EthernetDeviceIni:
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
    def __init__(self, addr: str):
        self.dev_addr = addr
        self.seq_num = 1

        self.udp_sock = socket(AF_INET, SOCK_DGRAM)
        self.tcp_sock = socket(AF_INET, SOCK_STREAM)
        self.tcp_sock.connect((addr, tcp_port))

        self.ini = self.read_ini()

        self.opened = True

    @property
    def isOpened(self) -> bool:
        return self.opened

    def setTimer(self, millis):
        if millis < self.ini.min_exposure:
            raise Exception(f'Exposure too low, minimal is {self.ini.min_exposure}')
        millis *= 10
        millis = int(millis)
        exponent = 0
        while millis >= (1 << 10):
            exponent += 1
            millis //= 10
        if exponent >= 4:
            raise Exception("Exposure too big")

        self.send_command(
            CMD_SET_TIMER,
            data=struct.pack('<H2xH', millis, exponent)
        )

    def close(self):
        self.tcp_sock.close()
        self.udp_sock.close()

    def readFrame(self, n_times):
        ini = self.ini
        self.set_line_length(ini.num_pixels, ini.num_chips)
        arr = np.empty((n_times, ini.num_pixels), dtype=np.uint16)
        self.send_command(CMD_READ_MULTILINE, struct.pack('<H2xI', 0, n_times))
        self.tcp_sock.recv_into(arr, n_times * ini.num_pixels * 2, MSG_WAITALL)
        measurement_header = np.array([0, 0, 0x8000, 0x8000, 0xabab, 0xabab])
        header_len = len(measurement_header)
        for i in range(n_times):
            if not np.array_equal(measurement_header, arr[i][:header_len]):
                raise Exception('Invalid measurement header')

        samples = arr[:, header_len:].astype('int32')
        # TODO: clipped support
        return Frame(samples=samples, clipped=np.zeros(samples.shape))

    # internal stuff
    def send_command(self, opcode, data=b'', ext_packets=0, pad_to=16):
        seq_num = self.seq_num
        self.seq_num += 1

        packet = struct.pack('<HH', opcode, seq_num) + data + bytes([0]*(pad_to-4-len(data)))
        self.udp_sock.sendto(packet, (self.dev_addr, udp_port))

        response_payloads = []

        for _ in range(1 + ext_packets):
            response = self.udp_sock.recvfrom(udp_buff_size)[0]
            resp_code, resp_cmd, resp_seq_num = struct.unpack('<H2xHH', response[:8])
            if resp_code > 2:
                raise Exception(f'Unsuccessful response code: {resp_code}')
            if resp_cmd != opcode:
                raise Exception(f'Response opcode does not match request')
            if resp_seq_num != seq_num:
                raise Exception(f'Response sequence number does not match request')
            response_payloads.append(response[8:])

        return response_payloads

    def read_ini(self) -> EthernetDeviceIni:
        data = self.send_command(CMD_READ_INI, data=bytes([0]), ext_packets=1)[1]
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

    def set_line_length(self, num_pixels, num_chips):
        self.send_command(
            CMD_SET_LINE_LENGTH,
            struct.pack('<IH', num_pixels, num_chips)
        )
