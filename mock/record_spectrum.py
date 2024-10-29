from pyspectrum_debug import Spectrometer
from pyspectrum_debug.device_factory import EthernetID

def run_test():
    # Открываем устройство
    device = Spectrometer(device_id=EthernetID(ip="127.0.0.1"))

    # Настройка устройства
    device.set_config(
        exposure=1,     # Экспозиция 1 мс
        n_times=10,   # За один раз будет считана 10 кадров
        wavelength_calibration_path='./mock/data/profile.json' # Путь к файлу калибровки длин волн
    )

    # Чтение темнового сигнала (ячейку нужно выполнять, закрыв спектрометр от света)
    device.read_dark_signal(n_times=10)

    # Чтение данных с устройства (будет считана 10 кадров)
    spectrum = device.read()

    # Сохранение считанных данных
    spectrum.save('recorded_spectrum')

if __name__ == '__main__':
    run_test()