import pickle
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from .errors import LoadError


def _check_slice_key(key):
    if type(key) == slice:
        return
    if type(key) == tuple:
        for k in key:
            if type(k) != slice:
                raise Exception('Only slices are supported')
        return
    raise Exception('Only slices are supported')


@dataclass()
class Data:
    """Сырые данные, полученные со спектрометра"""
    intensity: NDArray[float]
    """Двумерный массив данных измерения. Первый индекс - номер кадра, второй - номер сэмпла в кадре"""
    clipped: NDArray[bool]
    """Массив boolean значений. Если `clipped[i,j]==True`, `intensity[i,j]` содержит зашкаленное значение"""
    exposure: int
    """Экспозиция в миллисекундах"""

    @property
    def n_times(self) -> int:
        """Количество измерений"""
        return self.intensity.shape[0]

    @property
    def n_numbers(self) -> int:
        """Количество отсчетов"""
        return self.intensity.shape[1]

    @property
    def shape(self) -> tuple[int, int]:
        """Размерность данынх"""
        return self.intensity.shape

    def save(self, path: str):
        """Сохранить объект в файл"""
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str) -> 'Data':
        """Прочитать объект из файла"""

        with open(path, 'rb') as f:
            result = pickle.load(f)

        if not isinstance(result, cls):
            raise LoadError(path)

        return result

    def check_exposure(self, other: 'Data'):
        if self.exposure != other.exposure:
            raise ValueError('Exposures are different')

    def to_spectrum(self, wavelength: NDArray[float]) -> 'Spectrum':
        return Spectrum(self.intensity, self.clipped, self.exposure, wavelength, None)

    def __add__(self, other):
        if isinstance(other, Data):
            # add Data or Spectrum
            self.check_exposure(other)
            return Data(
                self.intensity + other.intensity,
                np.bitwise_or(self.clipped, other.clipped),
                self.exposure
            )
        else:
            # add numpy array or scalar
            return Data(
                self.intensity + other,
                self.clipped,
                self.exposure
            )

    def __sub__(self, other):
        if isinstance(other, Data):
            # sub Data or Spectrum
            self.check_exposure(other)
            return Data(
                self.intensity - other.intensity,
                np.bitwise_or(self.clipped, other.clipped),
                self.exposure
            )
        else:
            # sub numpy array or scalar
            return Data(
                self.intensity - other,
                self.clipped,
                self.exposure
            )

    def __mul__(self, other):
        # multiplying by data is not supported
        if isinstance(other, Data):
            raise TypeError('Cannot multiply by Data')
        return Data(
            self.intensity * other,
            self.clipped,
            self.exposure
        )

    def __repr__(self) -> str:
        cls = self.__class__
        return f'{cls.__name__}({self.n_times = }, {self.n_numbers = })'

    def __getitem__(self, key) -> 'Data':
        _check_slice_key(key)
        return Data(
            intensity=self.intensity.__getitem__(key),
            clipped=self.clipped.__getitem__(key),
            exposure=self.exposure
        )


@dataclass()
class Spectrum(Data):
    """Обработанные данные, полученные со спектрометра.
    Содержит в себе информацию о длинах волн измерения.
    В данный момент обработка заключается в вычитании темнового сигнала.
    """

    wavelength: NDArray[float]
    """длина волны фотоячейки"""
    number: NDArray[float] | None = field(default=None)  # номер фотоячейки TODO: not implemented

    # TODO: slice support
    def __add__(self, other):
        return super().__add__(other).to_spectrum(self.wavelength)

    def __sub__(self, other):
        return super().__sub__(other).to_spectrum(self.wavelength)

    def __mul__(self, other):
        return super().__mul__(other).to_spectrum(self.wavelength)

    def __getitem__(self, key) -> 'Spectrum':
        _check_slice_key(key)
        if type(key) == tuple and len(key) >= 2:
            new_wl = self.wavelength[key[1]]
        else:
            new_wl = self.wavelength
        return Spectrum(
            wavelength=new_wl,
            exposure=self.exposure,
            intensity=self.intensity.__getitem__(key),
            clipped=self.clipped.__getitem__(key)
        )

