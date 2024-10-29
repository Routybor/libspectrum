import socket
import struct
import numpy as np
from threading import Thread
from time import sleep

UDP_PORT = 555
TCP_PORT = 556
UDP_BUFFER_SIZE = 65536


def mock_ini_data():
    """Returns mock initialization data structured like EthernetDeviceIni."""
    return struct.pack(
        "<B3xHHHHxBHHIBBff", 2, 1024, 1, 255, 1, 1, 1, 0, 2048, 0xAB, 0xAB, 23.0, 1.5
    )


def mock_frame_data(n_times, num_pixels):
    """Generate mock measurement data similar to what `readFrame` might produce."""
    header = np.array([0, 0, 0x8000, 0x8000, 0xABAB, 0xABAB], dtype=np.uint16)
    samples = np.random.randint(
        0, 4096, size=(n_times, num_pixels - len(header)), dtype=np.uint16
    )
    data = np.hstack([np.tile(header, (n_times, 1)), samples])
    return data.tobytes()


class MockEthernetDevice:
    def __init__(self, ip="127.0.0.1"):
        self.ip = ip
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        Thread(target=self.run_udp, daemon=True).start()
        Thread(target=self.run_tcp, daemon=True).start()

    def run_udp(self):
        self.udp_sock.bind((self.ip, UDP_PORT))
        print("UDP mock server started...")
        while True:
            self.udp_sock.settimeout(1.0)
            try:
                data, addr = self.udp_sock.recvfrom(UDP_BUFFER_SIZE)
            except socket.timeout:
                print("No data received, retrying...")
                continue
            opcode, seq_num = struct.unpack("<HH", data[:4])
            response_code = 0  # Success
            response = struct.pack("<H2xHH", response_code, opcode, seq_num)
            response += mock_ini_data() if opcode == 0x800B else b""
            print(f"Received opcode: {opcode}, sending response: {response}")
            self.udp_sock.sendto(response, addr)

    def run_tcp(self):
        self.tcp_sock.bind((self.ip, TCP_PORT))
        self.tcp_sock.listen(1)
        print("TCP mock server started...")
        while True:
            conn, addr = self.tcp_sock.accept()
            print("TCP connection from:", addr)
            try:
                while True:
                    data = conn.recv(UDP_BUFFER_SIZE)
                    if not data:
                        break
                    opcode, seq_num, n_times = struct.unpack("<H2xI", data[:8])
                    if opcode == 0x0005:
                        num_pixels = 2048
                        conn.sendall(mock_frame_data(n_times, num_pixels))
                    else:
                        print(f"Unknown opcode received: {opcode}")
            finally:
                conn.close()
                print("TCP connection closed")


mock_device = MockEthernetDevice()
mock_device.start()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("Mock server shutting down...")
