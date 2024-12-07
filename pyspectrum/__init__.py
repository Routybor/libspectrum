from .errors import *
from .data import Data, Spectrum
from .spectrometer import Spectrometer, FactoryConfig

import platform

if platform.system() == "Windows":
    from .usb_device import UsbDevice
    from .usb_context import UsbContext
else:
    try:
        from .usb_device import UsbDevice
    except ImportError as e:
        raise ImportError(
            "Failed to import compiled USB device module."
            "Make sure you're using the correct version for your platform."
        ) from e