import time
import numpy as np
from multiprocessing import Process, Queue
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from struct import pack, unpack

udp_port = 555
tcp_port = 556
udp_buff_size = 65536


class MockEthernetDevice:
    def __init__(self, ip: str) -> None:
        self.ip = ip
        self.seq_num = 1

    def start(self):
        self.udp_sock = socket(family=AF_INET, type=SOCK_DGRAM)
        self.udp_sock.bind((self.ip, udp_port))
        self.tcp_sock = socket(family=AF_INET, type=SOCK_STREAM)
        self.tcp_sock.bind((self.ip, tcp_port))
        self.tcp_sock.listen(1)
        print(f"Mock Ethernet device running on {self.ip}")
        while True:
            data, addr = self.udp_sock.recvfrom(udp_buff_size)
            self.handle_udp_request(data=data, addr=addr)
            conn, _ = self.tcp_sock.accept()
            self.handle_tcp_request(conn=conn)

    def handle_tcp_request(self, conn) -> None:
        frame = np.random.randint(low=0, high=65535, size=(10, 2048), dtype=np.uint16)
        conn.send(frame.tobytes())
        conn.close()

    def handle_udp_request(self, data, addr):
        opcode, seq_num = unpack("<HH", data[:4])
        response = pack("<HH", opcode, seq_num) + bytes(12)
        self.udp_sock.sendto(response, addr)

    def stop(self) -> None:
        self.udp_sock.close()
        self.tcp_sock.close()


def run_mock_device(ip):
    device = MockEthernetDevice(ip=ip)
    device.start()
