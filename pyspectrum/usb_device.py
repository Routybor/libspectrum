import numpy as np
from .usb_context import UsbContext
from .data import Data

CMD_CODE_WRITE_CR = 0x01
CMD_CODE_WRITE_TIMER = 0x02
CMD_CODE_WRITE_PIXEL_NUMBER = 0x0c
CMD_CODE_READ_ERRORS = 0x92
CMD_CODE_READ_VERSION = 0x91
CMD_CODE_READ_FRAME = 0x05

CMD_SUCCESS = 0x2B
CMD_FAILURE = 0x2D
CMD_UNKNOWN = 0x3F

class UsbRawSpectrometer:
    def __init__(self, vendor: int, product: int, serial: str, read_timeout: int):
        """
        Initializes UsbDevice and opens the USB device.

        :param vendor: USB vendor ID
        :param product: USB product ID
        :param serial: USB serial number (optional)
        :param read_timeout: Timeout for read operations (in milliseconds)
        """
        self.context = UsbContext()
        self._read_timeout = read_timeout
        self._pixel_number = 0x1006
        self._sequence_number = 1

        self.context.open(vendor=vendor, product=product, serial=serial)
        self.context.set_bitmode(0x40, 0x40)
        self.context.set_timeouts(300, 300)

        self._send_command(CMD_CODE_WRITE_CR, 0)
        self._send_command(CMD_CODE_WRITE_TIMER, 0x03e8)
        self._send_command(CMD_CODE_WRITE_PIXEL_NUMBER, self._pixel_number)

        self.opened: bool = True

    def close(self):
        """Closes the USB spectrometer device."""
        if not self.opened:
            raise RuntimeError("Device is not opened.")
        self.context.close()
        self.opened = False

    def isOpened(self) -> bool:
        """True if USB Device is open"""
        return self.opened

    def get_pixel_count(self) -> int:
        """Returns pixel number"""
        return self._pixel_number

    def _send_command(self, code: int, data: int) -> bytearray[10]:
        """
        Sends a command to the USB device and handles the response.

        ### Structure of command packet:
            `[ #CMD | CMD_CODE | CMD_LENGTH = 4 | SEQ_NUMBER | DATA]`
            `DATA` lenght is specifyed by `CMD_LENGTH` ( <=4, but we always send 4)
            `SEQ_NUMBER` - 2 bytes
            total: 12 bytes long

        ### Structure of answer packet:
            `[ #ANS | ANS_CODE | ANS_LENGTH = 2 | SEQ_NUMBER | DATA]`
            Recieved `SEQ_NUMBER` is unchanged from sent command packet
            `ANS_CODE = CMD_SUCCESS | CMD_FALIURE | CMD_UNKNOWN`
            total: 10 bytes long
            
        :param  code (int): Command code(`CMD_CODE`) to send.
        :param  data (int): Associated data(`DATA`) to send (4 bytes).

        Returns:
            bytearray: The 10-byte answer packet from the device.
        """
        command = bytearray(12)
        command[:4] = b"#CMD"
        command[4] = code
        command[5] = 4
        command[6:8] = self._sequence_number.to_bytes(2, byteorder="little")
        command[8:12] = data.to_bytes(4, byteorder="little")
        self.context.write(command)

        ans = self._read_exact(10)

        if ans[:4] != b"#ANS":
            raise RuntimeError(f"Received bad answer magic: {ans[:4]}")
        elif ans[6:8] != self._sequence_number.to_bytes(2, byteorder="little"):
            raise RuntimeError(
                f"SEQ_NUMBER number mismatch: sent {self._sequence_number}, "
                f"received {int.from_bytes(ans[6:8], byteorder='little')}"
            )
        elif ans[4] == CMD_FAILURE:
            raise RuntimeError(f"Command was not completed")
        elif ans[4] == CMD_UNKNOWN:
            raise RuntimeError(f"Unknown command: {code}")
        elif ans[4] != CMD_SUCCESS:
            raise RuntimeError(f"Unexpected command status: {ans[4]}")
        
        self._sequence_number = (self._sequence_number + 1) & 0xFFFF # stay in 16 bits range
        return ans
        
        #TODO: implement handling of commands failure (retry mechanism)