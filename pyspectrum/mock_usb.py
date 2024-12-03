import numpy as np
import csv
from pathlib import Path

from .data import Frame


class MockUsbDevice:
    def __init__(self, data_file: str, read_timeout: int):
        """
        Имитирует поведение USB устройства, используя данные из файла .csv
        :param data_file: путь к файлу .csv с реальными данными спектра.
        :param read_timeout: время ожидания для операций чтения (в миллисекундах).
        """
        self._data_file = Path(data_file)
        self._read_timeout = read_timeout
        self._pixel_number = 0x1006  # фиксированное количество пикселей
        self._sequence_number = 1
        self._data = self._load_data()

    def _load_data(self):
        """
        Загружает данные из файла и масштабирует их.
        """
        if not self._data_file.exists():
            raise FileNotFoundError(f"Data file {self._data_file} not found.")
        
        scaled_data = []
        with open(self._data_file, 'r') as file:
            reader = csv.reader(file, delimiter='\t')
            for row in reader:
                # Преобразуем значения в float и масштабируем
                scaled_row = [float(value) * 100 * (2**16 - 1) for value in row]
                scaled_data.append(scaled_row)
        
        # Обрезаем значения, чтобы они соответствовали диапазону uint16
        scaled_data = np.array(scaled_data, dtype=np.float64)
        scaled_data = np.clip(scaled_data, 0, np.iinfo(np.uint16).max)
        return scaled_data.astype(np.uint16)


    def close(self):
        """Закрыть соединение."""
        pass  # Ничего не делаем для mock

    @property
    def isOpened(self) -> bool:
        """
        :return: True если устройство готово к работе
        """
        return True

    def get_pixel_count(self) -> int:
        """
        :return: Кол-во пикселей
        """
        return self._pixel_number

    def setTimer(self, millis: int):
        """Эмулирует установку экспозиции."""
        pass  # Не влияет на mock-данные

    def readFrame(self, n_times: int):
        """
        Имитирует чтение кадра спектральных данных.
        :param n_times: количество накоплений/линий
        :return: Массив данных спектра
        """
        if n_times > len(self._data):
            raise ValueError(
                f"Requested {n_times} frames, but only {len(self._data)} available in mock data."
            )

        # Получаем кадры из mock-данных
        frames = self._data[:n_times]
        clipped = np.where(frames == np.iinfo(np.uint16).max, 1, 0)
        return Frame(samples=frames, clipped=clipped)
