import json
import sys
from dataclasses import dataclass
import threading
from typing import Callable, List, Optional

import numpy as np
from numpy.typing import NDArray

from .data import Data, Spectrum, Frame
from .errors import ConfigurationError, LoadError
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
            1.0,
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
        При инициализации класса соединение с устройством не открывается.

        :param int vendor: Идентификатор производителя.
        :param int product: Идентификатор продукта.
        :param factory_config: Заводские настройки
        :type factory_config: FactoryConfig
        """
        self.__device = None
        self.__vendor = vendor
        self.__product = product
        self.__factory_config = factory_config
        self.__config = Config()
        self.__dark_signal: Data | None = None
        self.__wavelengths: NDArray[float] | None = None

        
        self.running = False
        self.__is_opened = False

        self.__stop_reading_flag = False
        self.__reading_thread: Optional[threading.Thread] = None

    def open(self):
        """
        Открывает соединение с устройством.
        """
        if self.__is_opened:
            return
            
        self.__device: UsbDevice = UsbDevice(vendor=self.__vendor, product=self.__product)
        self.__device.set_timer(self.__config.exposure)
        self.__is_opened = True

    def close(self) -> None:
        """
        Закрывает соединение с устройством.
        """
        if not self.__is_opened:
           return 
        
        self.__device.close()
        self.__is_opened = False

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
        is_opened = self.__is_opened
        try:
            if not is_opened:
               self.open() 
            self.__dark_signal = self.read_raw(n_times)
        finally:
            if not is_opened:
               self.close()

    def save_dark_signal(self):
        """
        Сохраняет темновой сигнал в файл.
        """
        if self.__config.dark_signal_path is None:
            raise ConfigurationError('Dark signal path is not set')
        if self.__dark_signal is None:
            raise ConfigurationError('Dark signal is not loaded')

        self.__dark_signal.save(self.__config.dark_signal_path)

    def __load_wavelength_calibration(self, path: str) -> None:
        factory_config = self.__factory_config

        with open(path, 'r') as file:
            data = json.load(file)

        wavelengths = np.array(data['wavelengths'], dtype=float)
        if len(wavelengths) != (factory_config.end - factory_config.start):
            raise ValueError("Wavelength calibration data has incorrect number of pixels")

        self.__wavelengths = wavelengths
        eprint('Wavelength calibration loaded')

    def read_raw(self, n_times: Optional[int] = None) -> Data:
        """
        Получить сырые данные с устройства.

        :param n_times: Количество измерений.
        :type n_timess: int | None

        :return: Данные с устройства.
        :rtype: Data
        
        :raises RuntimeError: Если устройство не открыто.
        """
        if self.__device == None or self.__is_opened == False:
            raise RuntimeError('Device is not opened')

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

    def read(self, n_times: Optional[int] = None, force: bool = False) -> Spectrum:
        """
        Получить обработанный спектр с устройства.
        
        Если устройство еще не было открыто, открывает его автоматически и закрывает после считывания.
        Если устройство было открыто ранее, оставляет его открытым.

        :param bool force: Если ``True``, позволяет считать сигнал без калибровки по длина волн
        :param int n_times: Количество измерений. Если не указано, используется значение из конфига.

        :return: Считанный спектр
        :rtype: Spectrum
        """
        if self.__wavelengths is None and not force:
            raise ConfigurationError('Wavelength calibration is not loaded')
        if self.__dark_signal is None:
            raise ConfigurationError('Dark signal is not loaded')

        is_opened = self.__is_opened
        try:
            if not is_opened:
               self.open()
            data = self.read_raw(n_times)
            scale = self.__factory_config.intensity_scale
            return Spectrum(
                intensity=(data.intensity / scale - np.round(
                    np.mean(self.__dark_signal.intensity / scale, axis=0))) * scale,
                clipped=data.clipped,
                wavelength=self.__wavelengths,
                exposure=self.__config.exposure,
            )
        finally:
            if not is_opened:
               self.close()

    def stop_reading(self):
        """
        Останавливает поток постоянного считывания спектров, если он был запущен через `read_non_stop`.  
        """
        self.__stop_reading_flag = True
        if self.__reading_thread and self.__reading_thread.is_alive():
            self.__reading_thread.join() # Wait for the thread to finish if is not None
        self.__reading_thread = None
    
    def _reset_stop_reading(self):
        self.__stop_reading_flag = False

    def read_non_block(self, callback: Callable[[Spectrum], None], frames_to_read: int, frames_interval: int = 100):
        """
        Читает нужное количество кадров в неблокирующем режиме и вызывает callback-функцию для каждого считанного спектра.
        
        :param callback: функция-callback для вызова с каждым считанным спектром.
        :param frames_to_read: Максимальное количество кадров для считывания.
        :param frames_interval: Кол-во кадров для считывания в одной итерации цикла.
        """

        if not self.is_configured:
            raise ConfigurationError("Spectrometer not configured.")
        
        is_opened = self.__is_opened
        try:
            if not is_opened:
                   self.open()
            self._reset_stop_reading()
            read_frames = 0
            while (frames_to_read is None or read_frames < frames_to_read) and not self.__stop_reading_flag:
                spectrum = self.read(n_times=frames_interval)
                read_frames += frames_interval
                if spectrum is None:
                    break

                try:
                    callback(spectrum)
                except Exception as e:
                    eprint(f"Error in callback: {e}")
                    break
        finally:
            if not is_opened:
                   self.close()

    def read_non_stop(self, callback: Callable[[Spectrum], None], frames_interval: int = 100):
        """
        Непрерывно считывает спектры в отдельном потоке и вызывает callback-функцию для каждого считанного спектра.
        Для остановки чтения спектров используйте метод `stop_reading`.

        :param callback: функция-callback для вызова с каждым считанным спектром.
        :param frames_interval: Кол-во кадров для считывания в одной итерации цикла.
        :raises RuntimeError: если поток чтения уже запущен.
        """

        if self.__reading_thread and self.__reading_thread.is_alive():
             raise RuntimeError("Reading thread is already running")
        
        self.__reading_thread = threading.Thread(target=self.read_non_block, args=(callback, None, frames_interval))
        self.__reading_thread.start()

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
            self.__config.exposure = exposure

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
