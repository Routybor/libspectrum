from dataclasses import dataclass, field
from typing import Any
from abc import ABC, abstractmethod

import _pyspectrum as internal
from .ethernet_device import EthernetDevice


class DeviceID(ABC):
    @abstractmethod
    def _create(self):
        pass


@dataclass(unsafe_hash=True)
class UsbID(DeviceID):
    """Идентификатор usb спектрометра"""
    """Usb vendor id"""
    vid: int = 0x0403
    """Usb product id"""
    pid: int = 0x6014
    """Usb serial (по умоолчанию открывается первое устройство с подходящими `vid` и `pid`)"""
    serial: str = ''

    read_timeout: int = field(default=10_000, compare=False)

    def _create(self):
        return internal.UsbRawSpectrometer(self.vid, self.pid, self.serial, self.read_timeout)


@dataclass(unsafe_hash=True)
class EthernetID(DeviceID):
    ip: str

    def _create(self):
        return EthernetDevice(self.ip)


__device_cache: dict[DeviceID, Any] = dict()


def create_device(spec: DeviceID, reopen: bool):
    if reopen and (spec in __device_cache):
        __device_cache[spec].close()
    device = spec._create()
    __device_cache[spec] = device
    return device
