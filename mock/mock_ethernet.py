import socket
import struct
import numpy as np
from threading import Thread
from time import sleep

CMD_READ_INI = 0x800B
CMD_READ_MULTILINE = 0x0005
CMD_SET_LINE_LENGTH = 0x000C
CMD_SET_TIMER = 0x0002

UDP_PORT = 555
TCP_PORT = 556
UDP_BUFFER_SIZE = 65536

mock_ini_data = {
    "num_chips": 1,
    "num_pixels_per_chip": 256,
    "chip_type": 1,
    "adc_rate": 16,
    "config_bits": 0xAA,
    "assembly_type": 1,
    "min_exposure": 1.0,
    "num_pixels": 256,
    "mtr0": 1.5,
    "mui0": 1.0,
    "dia_present": True,
    "thermostat_enabled": True,
}


def pack_ini_data():
    dia_present = 0xAB if mock_ini_data["dia_present"] else 0x00
    thermostat_enabled = 0xAB if mock_ini_data["thermostat_enabled"] else 0x00
    return struct.pack(
        "<B3xHHBBxBHHIBBff",
        mock_ini_data["num_chips"],
        mock_ini_data["num_pixels_per_chip"],
        mock_ini_data["chip_type"],
        mock_ini_data["adc_rate"],
        mock_ini_data["config_bits"],
        mock_ini_data["assembly_type"],
        int(mock_ini_data["min_exposure"] * 10),
        0,
        mock_ini_data["num_pixels"],
        dia_present,
        thermostat_enabled,
        mock_ini_data["mtr0"],
        mock_ini_data["mui0"],
    )


mock_ini_response = pack_ini_data()


def start_udp_server():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("127.0.0.1", UDP_PORT))
    global tcp_connection_active

    print("Mock UDP server started on port 555")

    while True:
        data, addr = udp_sock.recvfrom(UDP_BUFFER_SIZE)
        if len(data) < 4:
            continue

        opcode, seq_num = struct.unpack("<HH", data[:4])
        print(f"Received opcode: {opcode}, seq_num: {seq_num}")
        if opcode == CMD_READ_INI:
            ack_response = struct.pack("<HHHH", 0x0001, 0x0, CMD_READ_INI, seq_num)
            udp_sock.sendto(ack_response, addr)

            extended_response_header = struct.pack(
                "<HHHH", 0x0002, 0x0, CMD_READ_INI, seq_num
            )
            udp_sock.sendto(extended_response_header + mock_ini_response, addr)

        elif opcode == CMD_SET_TIMER:
            (timer_value,) = struct.unpack("<I", data[4:8])
            print(f"Received SetTimer command with timer value: {timer_value}")

            set_timer_ack = struct.pack("<HHHH", 0x0001, 0x0, CMD_SET_TIMER, seq_num)
            udp_sock.sendto(set_timer_ack, addr)

        elif opcode == CMD_SET_LINE_LENGTH:
            pixel_number_low, pixel_number_high, chips_num = struct.unpack(
                "<HHH", data[4:10]
            )
            pixel_number = (pixel_number_high << 16) | pixel_number_low

            print(
                f"Received SetLineLength command with pixelNumber: {pixel_number}, chipsNum: {chips_num}"
            )

            set_line_length_ack = struct.pack(
                "<HHHH", 0x0001, 0x0, CMD_SET_LINE_LENGTH, seq_num
            )
            udp_sock.sendto(set_line_length_ack, addr)

        elif opcode == CMD_READ_MULTILINE:
            if not tcp_connection_active:
                error_response = struct.pack(
                    "<HHHH", 0x0002, 0x0, CMD_READ_MULTILINE, seq_num
                )
                udp_sock.sendto(error_response, addr)
                continue
            control_register, line_number_low, line_number_high = struct.unpack(
                "<HHH", data[4:10]
            )
            line_number = (line_number_high << 16) | line_number_low

            print(
                f"Received ReadMultiLine command with lineNumber: {line_number}, Control_register: {control_register}"
            )

            ack_response = struct.pack(
                "<HHHH", 0x0001, 0x0, CMD_READ_MULTILINE, seq_num
            )
            udp_sock.sendto(ack_response, addr)

            global multiline_data_request
            multiline_data_request = (line_number, control_register)


def start_tcp_server():
    """Start a TCP server to listen for read frame commands on port 556."""
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind(("127.0.0.1", TCP_PORT))
    tcp_sock.listen(1)
    print("Mock TCP server started on port 556")

    global multiline_data_request
    multiline_data_request = None

    while True:
        conn, addr = tcp_sock.accept()
        print(f"Accepted TCP connection from {addr}")
        global tcp_connection_active
        tcp_connection_active = True

        try:
            while True:
                if multiline_data_request:
                    line_number, control_register = multiline_data_request
                    print(f"Sending {line_number} lines to {addr}")
                    multiline_data_request = None

                    for _ in range(line_number):
                        header = np.array(
                            [0x0000, 0x0000, 0x8000, 0x8000, 0xABAB, 0xABAB],
                            dtype=np.uint16,
                        )
                        data = np.random.randint(
                            0,
                            32768,
                            size=mock_ini_data["num_pixels"] - len(header),
                            dtype=np.uint16,
                        )
                        data |= 0x8000
                        frame = np.concatenate((header, data))
                        conn.sendall(frame.tobytes())
                        sleep(0.1)

                    print(f"Sent {line_number} frames to {addr}")

        except (ConnectionResetError, BrokenPipeError, KeyboardInterrupt):
            print("Connection closed by client")
        finally:
            conn.close()


udp_thread = Thread(target=start_udp_server, daemon=True)
tcp_thread = Thread(target=start_tcp_server, daemon=True)

udp_thread.start()
tcp_thread.start()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("Mock server shutting down.")
