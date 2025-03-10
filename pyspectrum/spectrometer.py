import json
import sys
import queue
from dataclasses import dataclass
import threading
from typing import Callable, Optional

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

        self.__is_opened = False

        self.__reading_lock = threading.RLock()
        self.__data_queue = queue.Queue(maxsize=10)
        self.__producer_thread = None
        self.__consumer_thread = None
        self.__stop_threads_event = threading.Event()

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
        with self.__reading_lock:
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
        with self.__reading_lock:
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

    def read_continuous(self, callback: Callable[[Spectrum], None], frames_to_read: Optional[int] = None, batch_size: int = 100) -> None:
        """
        Непрерывное чтение спектров батчами с вызовом callback-функции для каждого считанного батча спектров.
            
        :param callback: Функция-callback, которая будет вызвана для каждого считанного батча (Принимает объект Spectrum в качестве аргумента)
        :type callback: Callable[[Spectrum], None]
            
        :param frames_to_read: Количество кадров для чтения. При отсутствии параметра, чтение будет продолжаться, пока не будет вызван метод stop_reading.
        :type frames_to_read: int | None
            
        :param batch_size: Размер пакета/батча. По умолчанию равен 100.
        :type batch_size: int
            
        :raises ConfigurationError: Если спектрометр не настроен (отсутствует темновой сигнал или калибровка по длине волны).
        :raises RuntimeError: Если уже выполняется процесс непрерывного чтения.
        """
        if not self.is_configured:
            raise ConfigurationError("Spectrometer not configured.")

        if (self.__producer_thread and self.__producer_thread.is_alive()) or \
        (self.__consumer_thread and self.__consumer_thread.is_alive()):
            raise RuntimeError("Reading already in progress. Call stop_reading() first.")

        if self.__producer_thread or self.__consumer_thread:
            self.__threads_cleanup()

        self.__stop_threads_event.clear()

        was_opened = self.__is_opened
        if not was_opened:
            self.open()

        if frames_to_read is not None:
            frames_read = [0]

            def counting_callback(spectrum):
                callback(spectrum)
                frames_read[0] += batch_size
                if frames_read[0] >= frames_to_read:
                    self.__stop_threads_event.set()

            wrapper_callback = counting_callback
        else:
            wrapper_callback = callback

        self.__producer_thread = threading.Thread(
            target=self.__producer_task,
            args=(batch_size, was_opened),
            daemon=True
        )
        self.__consumer_thread = threading.Thread(
            target=self.__consumer_task,
            args=(wrapper_callback,),
            daemon=True
        )

        self.__producer_thread.start()
        self.__consumer_thread.start()

    def __producer_task(self, batch_size: int, was_opened: bool):
        try:
            while not self.__stop_threads_event.is_set():
                with self.__reading_lock:
                    spectrum = self.read(n_times=batch_size)

                if self.__stop_threads_event.is_set():
                    break

                while True:
                    try:
                        self.__data_queue.put(spectrum, timeout=0.1)
                        break
                    except queue.Full:
                        if self.__stop_threads_event.is_set():
                            break
        except Exception as e:
            eprint(f"Error in producer thread: {e}")
        finally:
            if not was_opened:
                try:
                    self.close()
                except Exception as e:
                    eprint(f"Error closing device: {e}")

    def __consumer_task(self, callback: Callable[[Spectrum], None]):
        try:
            while not self.__stop_threads_event.is_set():
                try:
                    spectrum = self.__data_queue.get(timeout=1.0)
                    try:
                        callback(spectrum)
                    except Exception as e:
                        eprint(f"Error in callback: {e}")
                    finally:
                        self.__data_queue.task_done()
                except queue.Empty:
                    continue
        except Exception as e:
            eprint(f"Error in consumer thread: {e}")

    def stop_reading(self):
        """
        Останавливает процесс непрерывного чтения, запущенного через вызов метода read_continuous.
        """
        self.__stop_threads_event.set()
        self.__threads_cleanup()

    def __threads_cleanup(self):
        if self.__producer_thread:
            self.__producer_thread.join(timeout=2.0)
        if self.__consumer_thread:
            self.__consumer_thread.join(timeout=2.0)

        while not self.__data_queue.empty():
            try:
                self.__data_queue.get_nowait()
                self.__data_queue.task_done()
            except queue.Empty:
                break

        self.__producer_thread = None
        self.__consumer_thread = None

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
