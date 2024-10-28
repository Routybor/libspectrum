from multiprocessing import Process
import time
import socket
from mock_ethernet_device import run_mock_device
from record_spectrum import run_test

tcp_port = 556


def wait_for_server(ip, port, timeout=5) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(address=(ip, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            print("Waiting")
            time.sleep(0.1)
    return False


def main() -> None:
    mock_device_process = Process(target=run_mock_device, args=("127.0.0.1",))
    mock_device_process.start()

    socket.create_connection(address=("127.0.0.1", tcp_port), timeout=1)

    if not wait_for_server(ip="127.0.0.1", port=tcp_port):
        print("Error: Mock server failed to start.")
        mock_device_process.terminate()
        return

    print("Running test\n")
    run_test()

    mock_device_process.terminate()
    mock_device_process.join()


if __name__ == "__main__":
    main()
