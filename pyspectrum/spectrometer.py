import json
import multiprocessing
import queue
import sys
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
        
    def read_continuous(self, callback: Callable[[Spectrum], None], 
                        frames_to_read: Optional[int] = None,
                        frames_per_read: int = 100,
                        max_queue_size: int = 10):
        """
        Запускает непрерывное чтение в отдельном процессе и выполняет обратные вызовы в основном процессе.
        
        :param callback: Функция-callback для вызова с каждым считанным спектром.
        :param frames_to_read: Максимальное количество кадров для считывания (если None, то бесконечно).
        :param frames_per_read: Размер единичного спектра для считывания.
        :param max_queue_size: Максимальный размер очереди до блокировки читающего процесса.
        :raises RuntimeError: если процесс чтения уже запущен
        """
        if hasattr(self, '_producer_process_instance') and self._producer_process_instance and self._producer_process_instance.is_alive():
            raise RuntimeError("Reading process is already running")
        
        self._data_queue = multiprocessing.Queue(maxsize=max_queue_size)
        self._error_queue = multiprocessing.Queue()
        self._stop_event = multiprocessing.Event()
        self._frame_count = multiprocessing.Value('i', 0)
        
        self._consumer_thread_instance = threading.Thread(
            target=self._consumer_thread,
            args=(callback, self._data_queue, self._error_queue, self._stop_event, 
                self._frame_count, frames_to_read, frames_per_read)
        )
        self._consumer_thread_instance.daemon = True
        self._consumer_thread_instance.start()
        
        self._producer_process_instance = multiprocessing.Process(
            target=self._producer_process,
            args=(self._data_queue, self._error_queue, self._stop_event, frames_per_read)
        )
        self._producer_process_instance.daemon = True
        self._producer_process_instance.start()
        
    def _producer_process(self, data_queue, error_queue, stop_event, frames_per_read):
        """
        Функция-Производитель, которая выполняется в отдельном процессе, читая спектры и помещения их в очередь.
        
        :param data_queue: Очередь для помещения спектров.
        :param error_queue: Очередь для помещения ошибок.
        :param stop_event: Event, сигнализирующий остановку.
        :param frames_per_read: Кол-во кадров для считывания в одной итерации цикла.
        """
        try:
            self.open()
            
            while not stop_event.is_set():
                try:
                    spectrum = self.read(n_times=frames_per_read)
                    data_queue.put(spectrum, timeout=1.0)
                except queue.Full:
                    continue
                except Exception as e:
                    error_queue.put(str(e))
                    break
        except Exception as e:
            error_queue.put(str(e))
        finally:
            self.close()
            
    def _consumer_thread(self, callback, data_queue, error_queue, stop_event, 
                        frame_count, frames_per_read, frames_to_read=None):
        """
        Функция, которая работает в потоке основного процесса для выполнения обратных вызовов.
        
        :param callback: Определенная пользователем callback-функция.
        :param data_queue: Очередь для получения спектров.
        :param error_queue: Очередь для проверки ошибок.
        :param stop_event: Event, сигнализирующий о необходимости остановки.
        :param frame_count: Value для отслеживания количества прочитанных кадров.
        :param frames_per_read: Кол-во кадров для считывания в одной итерации цикла.
        """
        while not stop_event.is_set():
            
            if frames_to_read is not None and frame_count.value >= frames_to_read:
                stop_event.set()
                break
            
            try:
                if not error_queue.empty():
                    error = error_queue.get_nowait()
                    eprint(f"Error in producer process: {error}")
                    break
            except:
                pass
            
            try:
                spectrum = data_queue.get(timeout=0.1)
                try:
                    callback(spectrum)
                except Exception as e:
                    eprint(f"Error in callback: {e}")
                    stop_event.set()
                    break
            except queue.Empty:
                continue
            except Exception as e:
                eprint(f"Error getting data from queue: {e}")
                break
            
            with frame_count.get_lock():
                frame_count.value += frames_per_read

    def stop_continuous_reading(self):
        """
        Останавливает непрерывное чтение, запущенное через read_continious, gracefully.
        """
        if hasattr(self, '_stop_event') and self._stop_event:
            self._stop_event.set()
        
        if hasattr(self, '_producer_process_instance') and self._producer_process_instance and self._producer_process_instance.is_alive():
            self._producer_process_instance.join(timeout=5.0)
            if self._producer_process_instance.is_alive():
                self._producer_process_instance.terminate()
        
        if hasattr(self, '_consumer_thread_instance') and self._consumer_thread_instance and self._consumer_thread_instance.is_alive():
            self._consumer_thread_instance.join(timeout=5.0)
        
        if hasattr(self, '_data_queue'):
            self._data_queue = None
        if hasattr(self, '_error_queue'):
            self._error_queue = None
        if hasattr(self, '_stop_event'):
            self._stop_event = None
        if hasattr(self, '_producer_process_instance'):
            self._producer_process_instance = None
        if hasattr(self, '_consumer_thread_instance'):
            self._consumer_thread_instance = None

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
