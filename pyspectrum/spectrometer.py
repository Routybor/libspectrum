import json
import sys
from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from .data import Data, Spectrum
from .errors import ConfigurationError, LoadError, DeviceClosedError
from .usb_device import UsbDevice


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@dataclass(frozen=True)
class FactoryConfig:
    """
    Настройки, индивидуадьные для каждого устройства.
    """
    start: int
    end: int
    reverse: bool
    intensity_scale: float

    @staticmethod
    def load(path: str) -> 'FactoryConfig':
        """
        Загружает заводские настройки из файла.
        
        :param path: Путь к файлу заводских настроек
        :type path: str
        :return: Объект заводских настроек
        :rtype: FactoryConfig
        """
        try:
            with open(path, 'r') as f:
                json_data = json.load(f)
            return FactoryConfig(**json_data)

        except KeyError:
            raise LoadError(path)

    @staticmethod
    def default() -> 'FactoryConfig':
        """
        Создаёт заводские настройки для тестрирования.
        
        :return: Объект заводских настроек
        :rtype: FactoryConfig
        """
        return FactoryConfig(
            2050,
            3850,
            True,
            1.220703125,
        )


@dataclass(frozen=False)
class Config:
    exposure: int = 10  # время экспозиции, ms
    n_times: int = 1  # количество измерений
    dark_signal_path: Optional[str] = None


class Spectrometer:
    """
    Класс, предоставляющий высокоуровневую абстракцию для работы со спетрометром
    """

    def __init__(self, vendor=0x0403, product=0x6014, factory_config: FactoryConfig = FactoryConfig.default()):
        """
        :param int vendor: Идентификатор производителя.
        :param int product: Идентификатор продукта.
        :param factory_config: Заводские настройки
        :type factory_config: FactoryConfig
        """
        self.__device: UsbDevice = UsbDevice(vendor=vendor, product=product)
        self.__factory_config = factory_config
        self.__config = Config()
        self.__device.set_timer(self.__config.exposure)
        self.__dark_signal: Data | None = None
        self.__wavelengths: NDArray[float] | None = None

    def __check_opened(self):
        if not self.__device.is_opened:
            raise DeviceClosedError()

    def close(self) -> None:
        """
        Закрывает соединение с устройством.
        """
        self.__device.close()

    # --------        dark signal        --------

    @property
    def dark_signal(self) -> Data | None:
        """
        Возвращает текущий темновой сигнал.
        
        :rtype: Data | None
        """
        return self.__dark_signal

    def __load_dark_signal(self):
        try:
            data = Data.load(self.__config.dark_signal_path)
        except Exception:
            eprint('Dark signal file is invalid or does not exist, dark signal was NOT loaded')
            return

        if data.shape[1] != (self.__factory_config.end - self.__factory_config.start):
            eprint("Saved dark signal has different shape, dark signal was NOT loaded")
            return
        if data.exposure != self.__config.exposure:
            eprint('Saved dark signal has different exposure, dark signal was NOT loaded')
            return

        self.__dark_signal = data
        eprint('Dark signal loaded')

    def read_dark_signal(self, n_times: Optional[int] = None) -> None:
        """
        Измеряет темновой сигнал.
        :param n_times: Количество измерений. При обработке данных будет использовано среднее значение
        :type n_timess: int | None
        """
        self.__dark_signal = self.read_raw(n_times)

    def save_dark_signal(self):
        """
        Сохраняет темновой сигнал в файл.
        """
        if self.__config.dark_signal_path is None:
            raise ConfigurationError('Dark signal path is not set')
        if self.__dark_signal is None:
            raise ConfigurationError('Dark signal is not loaded')

        self.__dark_signal.save(self.__config.dark_signal_path)

    # --------        wavelength calibration        --------
    def __load_wavelength_calibration(self, path: str) -> None:
        factory_config = self.__factory_config

        with open(path, 'r') as file:
            data = json.load(file)

        wavelengths = np.array(data['wavelengths'], dtype=float)
        if len(wavelengths) != (factory_config.end - factory_config.start):
            raise ValueError("Wavelength calibration data has incorrect number of pixels")

        self.__wavelengths = wavelengths
        eprint('Wavelength calibration loaded')

    # --------        read raw        --------
    def read_raw(self, n_times: Optional[int] = None) -> Data:
        """
        Получить сырые данные с устройства.
        
        :param n_times: Количество измерений.
        :type n_timess: int | None

        :return: Данные с устройства.
        :rtype: Data
        """
        self.__check_opened()

        device = self.__device
        config = self.__config
        start = self.__factory_config.start
        end = self.__factory_config.end
        scale = self.__factory_config.intensity_scale

        direction = -1 if self.__factory_config.reverse else 1
        n_times = config.n_times if n_times is None else n_times

        data = device.read_frame(n_times)  # type: Frame
        intensity = data.samples[:, start:end][:, ::direction] * scale
        clipped = data.clipped[:, start:end][:, ::direction]

        return Data(
            intensity=intensity,
            clipped=clipped,
            exposure=config.exposure,
        )

    # --------        read        --------
    def read(self, force: bool = False) -> Spectrum:
        """
        Получить обработанный спектр с устройства.

        :param bool force: Если ``True``, позволяет считать сигнал без калибровки по длина волн
        
        :return: Считанный спектр
        :rtype: Spectrum
        """
        if self.__wavelengths is None and not force:
            raise ConfigurationError('Wavelength calibration is not loaded')
        if self.__dark_signal is None:
            raise ConfigurationError('Dark signal is not loaded')

        data = self.read_raw()
        scale = self.__factory_config.intensity_scale
        return Spectrum(
            intensity=(data.intensity / scale - np.round(
                np.mean(self.__dark_signal.intensity / scale, axis=0))) * scale,
            clipped=data.clipped,
            wavelength=self.__wavelengths,
            exposure=self.__config.exposure,
        )

    # --------        config        --------
    @property
    def config(self) -> Config:
        """
        Возвращает текущую конфигурацию спектрометра.
        :rtpe: Config
        """
        return self.__config

    @property
    def is_configured(self) -> bool:
        """
        Возвращает `True`, если спектрометр настроен для чтения обработанных данных.
        :rtype: bool
        """
        return (self.__dark_signal is not None) and (self.__wavelengths is not None)

    def set_config(self,
                   exposure: Optional[int] = None,
                   n_times: Optional[int] = None,
                   dark_signal_path: Optional[str] = None,
                   wavelength_calibration_path: Optional[str] = None,
                   ):
        """
        Установить настройки спектрометра. Все параметры опциональны, при
        отсутствии параметра соответствующая настройка не изменяется.

        :param exposure: Время экспозиции в мс. При изменении темновой сигнал будет сброшен.
        :type exposure: int | None

        :param n_times: Количество измерений
        :type n_times: int | None

        :param dark_signal_path: Путь к файлу темнового сигнала. Если файл темнового сигнала существует и валиден, он будет загружен.
        :type dark_signal_path: str | None

        :param wavelength_calibration_path: Путь к файлу данных калибровки по длине волны
        :type wavelength_calibration_path: str | None
        """
        if (exposure is not None) and (exposure != self.__config.exposure):
            self.__check_opened()
            self.__config.exposure = exposure
            self.__device.set_timer(self.__config.exposure)

            if self.__dark_signal is not None:
                self.__dark_signal = None
                eprint('Different exposure was set, dark signal invalidated')

        if n_times is not None:
            self.__config.n_times = n_times

        if (dark_signal_path is not None) and (dark_signal_path != self.__config.dark_signal_path):
            self.__config.dark_signal_path = dark_signal_path
            self.__load_dark_signal()

        if wavelength_calibration_path is not None:
            self.__load_wavelength_calibration(wavelength_calibration_path)
