from .errors import *
from .data import Data, Spectrum
from .spectrometer import Spectrometer, FactoryConfig
from .usb_device import UsbDevice

import platform
if platform.system() != "Linux":
    from .usb_context import UsbContext