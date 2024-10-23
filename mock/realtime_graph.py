import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.widgets import Button
from os import path, getcwd
from time import time


class MockFactoryConfig:
    def __init__(self, param1, param2, param3, intensity_scale) -> None:
        self.intensity_scale = intensity_scale


class MockEthernetID:
    def __init__(self, ip) -> None:
        self.ip = ip


class MockSpectrometer:
    def __init__(self, ethernet_id, factory_config) -> None:
        self.ethernet_id = ethernet_id
        self.factory_config = factory_config
        self.is_configured = False
        self.__dark_signal = None
        self.__config = None
        self.__wavelengths = np.linspace(
            start=400, stop=700, num=2048
        )  # Заглушка до загрузки калибровки

    def set_config(
        self, n_times=None, exposure=None, wavelength_calibration_path=None
    ) -> None:
        self.__config = {
            "n_times": n_times,
            "exposure": exposure,
            "wavelength_calibration_path": wavelength_calibration_path,
        }
        if wavelength_calibration_path:
            self.__wavelengths = self.load_wavelength_calibration(
                filepath=wavelength_calibration_path
            )
            self.is_configured = True
        print(
            f"Mock device configured: n_times={n_times}, exposure={exposure}, "
            f"wavelength_calibration_path={wavelength_calibration_path}"
        )

    def load_wavelength_calibration(self, filepath):
        """Загрузка калибровки длин волн из JSON файла."""
        try:
            with open(file=filepath, mode="r") as file:
                data = json.load(fp=file)
                wavelengths = np.array(object=data["wavelengths"])
                print(f"Wavelength calibration loaded from {filepath}")
                return wavelengths
        except FileNotFoundError:
            print(f"Calibration file {filepath} not found!")
            return np.linspace(
                start=400, stop=700, num=2048
            )  # Возвращание заглушки, если файл не найден

    def read_dark_signal(self, n_times) -> None:
        # Подделывание темнового сигнала
        self.__dark_signal = np.random.normal(loc=0, scale=0.01, size=(n_times, 2048))
        print(f"Mock dark signal read with {n_times} frames.")

    def read_raw(self):
        # Подделывание сырых данных
        return MockData(
            intensity=np.random.random(size=(1, 2048)) * 1000,  # Генерация сырых данных
            clipped=np.random.random(size=(1, 2048)) > 0.5,
            exposure=self.__config["exposure"],
            n_numbers=2048,
        )

    def read(self):
        if self.__dark_signal is None:
            raise RuntimeError("Dark signal is not loaded")
        data = self.read_raw()
        intensity = data.intensity - np.mean(a=self.__dark_signal, axis=0)
        return MockData(
            intensity=intensity,
            clipped=data.clipped,
            exposure=self.__config["exposure"],
            wavelength=self.__wavelengths,
        )


class MockData:
    def __init__(
        self, intensity, clipped, exposure, wavelength=None, n_numbers=None
    ) -> None:
        self.intensity = intensity
        self.clipped = clipped
        self.exposure = exposure
        self.wavelength = wavelength
        self.n_numbers = n_numbers


# Использование поддельного устройства
d = MockSpectrometer(
    ethernet_id=MockEthernetID(ip="10.116.220.2"),
    factory_config=MockFactoryConfig(param1=0, param2=2048, param3=False, intensity_scale=1.0),
)

matplotlib.use(backend="Qt5agg")
figure, axs = plt.subplots(ncols=2)
ax = axs[0]

figure.subplots_adjust(bottom=0.2)

running = True


def on_close(_) -> None:
    global running
    running = False


def read_dark_signal(_) -> None:
    d.read_dark_signal(n_times=10)


figure.canvas.mpl_connect(s="close_event", func=on_close)

ax_dark = figure.add_axes([0.5, 0.05, 0.2, 0.075])
ax_profile = figure.add_axes([0.71, 0.05, 0.2, 0.075])

b_dark = Button(ax=ax_dark, label="Read dark signal")
b_dark.on_clicked(func=read_dark_signal)

b_profile = Button(ax=ax_profile, label="Load profile data")
profile_path = path.join(
    getcwd(), "../data/profile.json"
)  # Получание путь относительно текущей директории
b_profile.on_clicked(
    func=lambda e: d.set_config(wavelength_calibration_path=profile_path)
)

n_times = 1
d.set_config(n_times=n_times, exposure=100)

while running:
    read_start = time()
    if d.is_configured:
        data = d.read()
        wl = data.wavelength
    else:
        data = d.read_raw()
        wl = np.array(range(0, data.n_numbers))
    read_time = time() - read_start

    ax.clear()
    axs[1].clear()
    ax.plot(wl, np.mean(a=data.intensity, axis=0))
    axs[1].plot(wl, np.max(a=data.clipped, axis=0))
    plt.pause(interval=0.05)
