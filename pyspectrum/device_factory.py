from dataclasses import dataclass, field
from typing import Any
from abc import ABC, abstractmethod

from .ethernet_device import EthernetDevice
from .usb_device import UsbDevice
from .mock_usb import MockUsbDevice


class DeviceID(ABC):
    @abstractmethod
    def _create(self) -> UsbDevice | EthernetDevice:
        pass


@dataclass(unsafe_hash=True)
class UsbID(DeviceID):
    """Идентификатор usb спектрометра"""

    """Usb vendor id"""
    vid: int = 0x0403
    """Usb product id"""
    pid: int = 0x6014
    """Usb serial (по умоолчанию открывается первое устройство с подходящими `vid` и `pid`)"""
    serial: str = ""

    read_timeout: int = field(default=10_000, compare=False)

    def _create(self) -> UsbDevice:
        return UsbDevice(
            vendor=self.vid,
            product=self.pid,
            serial=self.serial,
            read_timeout=self.read_timeout,
        )


@dataclass(unsafe_hash=True)
class EthernetID(DeviceID):
    ip: str

    def _create(self) -> EthernetDevice:
        return EthernetDevice(addr=self.ip)


__device_cache: dict[DeviceID, Any] = dict()


def create_device(spec: DeviceID, reopen: bool) -> UsbDevice | EthernetDevice:
    if reopen and (spec in __device_cache):
        __device_cache[spec].close()
    device = spec._create()
    __device_cache[spec] = device
    return device


@dataclass(unsafe_hash=True)
class MockUsbID(DeviceID):
    """Идентификатор usb спектрометра"""
    read_timeout: int = field(default=10_000, compare=False)
    mock_data_file: str = field(default=None)  # путь к mock .csv файлу
    
    def _create(self) -> MockUsbDevice:
        return MockUsbDevice(
            read_timeout=self.read_timeout,
            data_file=self.mock_data_file,
        )
