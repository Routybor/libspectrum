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
    """Pack the mock INI data as binary for a response."""
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

    print("Mock UDP server started on port 555")

    while True:
        data, addr = udp_sock.recvfrom(UDP_BUFFER_SIZE)
        if len(data) < 4:
            continue

        opcode, seq_num = struct.unpack("<HH", data[:4])

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
            control_register, line_number_low, line_number_high = struct.unpack(
                "<HHH", data[4:10]
            )
            line_number = (line_number_high << 16) | line_number_low

            print(
                f"Received ReadMultiLine command with Control_register: {control_register}, lineNumber: {line_number}"
            )

            read_multiline_ack = struct.pack(
                "<HHHH", 0x0001, 0x0, CMD_READ_MULTILINE, seq_num
            )
            udp_sock.sendto(read_multiline_ack, addr)

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
                    tcp_sock.connect(("127.0.0.1", TCP_PORT))
                    for _ in range(line_number):
                        sync_signal = struct.pack("<H", 0xABCD)
                        data = np.random.randint(
                            0, 65535, size=mock_ini_data["num_pixels"], dtype=np.uint16
                        )
                        data = data ^ 0x8000
                        tcp_sock.sendall(sync_signal + data.tobytes())

            except Exception as e:
                print(f"TCP connection error: {e}")


def start_tcp_server():
    """Start a TCP server to listen for read frame commands on port 556."""
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind(("127.0.0.1", TCP_PORT))
    tcp_sock.listen(1)
    print("Mock TCP server started on port 556")

    while True:
        conn, addr = tcp_sock.accept()
        print(f"Accepted connection from {addr}")

        try:
            while True:
                break; # ! DEVELOPMENT
                command = conn.recv(4)
                if len(command) < 4:
                    break

                (opcode,) = struct.unpack("<H", command[:2])

                if opcode == CMD_READ_MULTILINE:
                    params = conn.recv(6)
                    (frame_count,) = struct.unpack("<I", params[2:])

                    num_pixels = mock_ini_data["num_pixels"]
                    header = np.array(
                        [0, 0, 0x8000, 0x8000, 0xABAB, 0xABAB], dtype=np.uint16
                    )
                    data = np.concatenate(
                        (
                            header,
                            np.random.randint(
                                0, 65535, size=num_pixels - len(header), dtype=np.uint16
                            ),
                        )
                    )
                    frames = np.tile(data, (frame_count, 1))

                    conn.sendall(frames.tobytes())
                    sleep(0.05)

        except (ConnectionResetError, BrokenPipeError):
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
