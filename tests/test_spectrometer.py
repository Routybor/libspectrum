from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
import json
import pytest
from pyspectrum import Spectrometer, Data, FactoryConfig, DeviceClosedError


@dataclass()
class MockInternalRawSpectrum:
    clipped: NDArray
    samples: NDArray


class MockInternalSpectrometer:
    resolution = 4096
    def __init__(self):
        self.__opened = True

    def setTimer(self, _):
        pass

    def readFrame(self, n_times):
        samples = np.array([np.arange(0, self.resolution, 1) + i for i in range(n_times)])
        clipped = np.zeros((n_times, self.resolution))
        return MockInternalRawSpectrum(clipped, samples)

    @property
    def isOpened(self) -> bool:
        return self.__opened

    def close(self):
        self.__opened = False


def create_factory_config(path: str, start: int, end: int, reverse: bool, intensity_scale: float = 1.0):
    data = {'start': start, 'end': end, 'reverse': reverse, 'intensity_scale': intensity_scale}
    with open(path, 'w') as f:
        json.dump(data, f)


def create_device(tmp_path, start=0, end=10, reverse=False) -> Spectrometer:
    config_path = str(tmp_path / 'cfg.json')
    create_factory_config(config_path, start, end, reverse)
    return Spectrometer(MockInternalSpectrometer(), FactoryConfig.load(config_path))


def write_calibration_data(path, wl):
    with open(path, "w") as f:
        json.dump({"wavelengths": wl}, f)


@pytest.mark.parametrize("start", [10, 20, 30])
@pytest.mark.parametrize("end", [40, 50, 60])
@pytest.mark.parametrize("reverse", [True, False])
def test_factory_config(tmp_path, start, end, reverse):
    device = create_device(tmp_path, start, end, reverse)
    data = device.read_raw().intensity
    assert data.shape[1] == end - start
    assert data[0, 0] > data[0, 1] if reverse else data[0, 0] < data[0, 1]


# device with default factory config
# first frame is linear range from 0 to 9
@pytest.fixture()
def device(tmp_path) -> Spectrometer:
    return create_device(tmp_path)


@pytest.mark.parametrize("exposure", [1, 2, 3])
def test_exposure(device: Spectrometer, exposure):
    device.set_config(exposure=exposure)
    assert device.read_raw().exposure == exposure


@pytest.mark.parametrize("n_times", [1, 2, 3])
def test_n_times(device: Spectrometer, n_times):
    device.set_config(n_times=n_times)
    assert device.read_raw().intensity.shape[0] == n_times


def test_full_configuration(tmp_path):
    d1 = create_device(tmp_path)
    assert not d1.is_configured
    with pytest.raises(Exception):
        d1.read()
    profile_path = str(tmp_path / 'profile.json')
    dark_signal_path = str(tmp_path / 'dark')
    wls = np.arange(0, 10, 1)
    write_calibration_data(profile_path, wls.tolist())
    d1.set_config(dark_signal_path=dark_signal_path, wavelength_calibration_path=profile_path)
    # no save dark signal, still not configured
    assert not d1.is_configured
    with pytest.raises(Exception):
        d1.read()
    d1.read_dark_signal()
    # now it should be configured
    assert d1.is_configured
    assert np.array_equal(d1.read().wavelength, wls)
    d1.save_dark_signal()

    d2 = create_device(tmp_path)
    assert not d2.is_configured
    d2.set_config(dark_signal_path=dark_signal_path, wavelength_calibration_path=profile_path)
    # dark signal was already saved, so it should be loaded automatically
    assert d2.is_configured


def test_incompatible_values(tmp_path, capsys):
    d1 = create_device(tmp_path)
    profile_path = str(tmp_path / 'profile.json')
    dark_signal_path = str(tmp_path / 'dark')
    write_calibration_data(profile_path, [1, 2, 3])
    # calibration data has different shape
    with pytest.raises(ValueError):
        d1.set_config(wavelength_calibration_path=profile_path)

    d1.set_config(exposure=333, dark_signal_path=dark_signal_path)
    d1.read_dark_signal()
    d1.save_dark_signal()

    d2 = create_device(tmp_path)
    capsys.readouterr()
    d2.set_config(dark_signal_path=dark_signal_path)
    assert "exposure" in capsys.readouterr().err


def test_force_read(device: Spectrometer):
    device.read_dark_signal()
    s = device.read(force=True)
    assert s.wavelength is None


def test_arithmetics():
    d1 = Data(np.array([1, 2, 999]), np.array([0, 0, 1]), 3)
    d2 = Data(np.array([666, 3, 4]), np.array([1, 0, 0]), 3)

    added = d1 + d2
    subbed = d1 - d2

    assert np.array_equal(added.intensity, [667, 5, 1003])
    assert np.array_equal(subbed.intensity, [-665, -1, 995])
    target_clipped = [1, 0, 1]
    assert np.array_equal(target_clipped, added.clipped)
    assert np.array_equal(target_clipped, subbed.clipped)
    assert added.exposure == subbed.exposure == 3

    assert type(subbed) == type(added) == Data

    with pytest.raises(ValueError):
        d1 + Data(np.array([1, 1, 1]), np.array([1, 1, 1]), 1)

    added_s = d1 + 3
    assert np.array_equal(np.array([4, 5, 1002]), added_s.intensity)
    assert np.array_equal(d1.clipped, added_s.clipped)
    assert d1.exposure == added_s.exposure

    with pytest.raises(TypeError):
        d1 * d2

    multiplies = d1 * 2
    assert np.array_equal(np.array([2, 4, 1998]), multiplies.intensity)


def test_device_close(device: Spectrometer):
    device.read_raw() # should not fail
    device.close()
    with pytest.raises(DeviceClosedError):
        device.read_raw()
