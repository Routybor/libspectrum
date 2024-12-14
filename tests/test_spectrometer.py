import numpy as np
import json
import pytest
from pyspectrum import Spectrometer, Data, FactoryConfig, Spectrum
from pyspectrum.data import Frame
import threading
import time

class MockUsbDevice:
    resolution = 4096
    
    def __init__(self, vendor=0, product=0, read_timeout=0):
        self._opened = True
        self._timer = 0
        
    def set_timer(self, millis):
        self._timer = millis
        
    def read_frame(self, n_times):
        samples = np.array([np.arange(0, self.resolution, 1) + i for i in range(n_times)])
        clipped = np.zeros((n_times, self.resolution), dtype=bool)
        return Frame(samples=samples, clipped=clipped)
    
    @property
    def is_opened(self) -> bool:
        return self._opened
        
    def close(self):
        self._opened = False

# Mock the UsbDevice import in spectrometer module
@pytest.fixture(autouse=True)
def mock_usb_device(monkeypatch):
    monkeypatch.setattr('pyspectrum.spectrometer.UsbDevice', MockUsbDevice)

def create_factory_config(path: str, start: int, end: int, reverse: bool, intensity_scale: float = 1.0):
    data = {
        'start': start, 
        'end': end, 
        'reverse': reverse, 
        'intensity_scale': intensity_scale
    }
    with open(path, 'w') as f:
        json.dump(data, f)

def create_device(tmp_path, start=0, end=10, reverse=False) -> Spectrometer:
    config_path = str(tmp_path / 'cfg.json')
    create_factory_config(config_path, start, end, reverse)
    return Spectrometer(factory_config=FactoryConfig.load(config_path))

def write_calibration_data(path, wl):
    with open(path, "w") as f:
        json.dump({"wavelengths": wl}, f)


@pytest.mark.parametrize("start", [10, 20, 30])
@pytest.mark.parametrize("end", [40, 50, 60])
@pytest.mark.parametrize("reverse", [True, False])
def test_factory_config(tmp_path, start, end, reverse):
    device = create_device(tmp_path, start, end, reverse)
    device.open()
    data = device.read_raw().intensity
    assert data.shape[1] == end - start
    assert data[0, 0] > data[0, 1] if reverse else data[0, 0] < data[0, 1]
    device.close()

@pytest.fixture()
def device(tmp_path) -> Spectrometer:
    return create_device(tmp_path)

@pytest.mark.parametrize("exposure", [1, 2, 3])
def test_exposure(device: Spectrometer, exposure):
    device.open()
    device.set_config(exposure=exposure)
    assert device.read_raw().exposure == exposure
    device.close()


@pytest.mark.parametrize("n_times", [1, 2, 3])
def test_n_times(device: Spectrometer, n_times):
    device.open()
    device.set_config(n_times=n_times)
    assert device.read_raw().intensity.shape[0] == n_times
    device.close()

def test_full_configuration(tmp_path):
    d1 = create_device(tmp_path)
    assert not d1.is_configured
    with pytest.raises(Exception):
        d1.read()
        
    profile_path = str(tmp_path / 'profile.json')
    dark_signal_path = str(tmp_path / 'dark')
    wls = np.arange(0, 10, 1)
    write_calibration_data(profile_path, wls.tolist())
    
    d1.set_config(
        dark_signal_path=dark_signal_path,
        wavelength_calibration_path=profile_path
    )
    
    assert not d1.is_configured
    with pytest.raises(Exception):
        d1.read()
        
    d1.read_dark_signal()
    assert d1.is_configured
    d1.open()
    assert np.array_equal(d1.read().wavelength, wls)
    d1.close()
    d1.save_dark_signal()

    d2 = create_device(tmp_path)
    assert not d2.is_configured
    d2.set_config(
        dark_signal_path=dark_signal_path,
        wavelength_calibration_path=profile_path
    )
    assert d2.is_configured
    d2.open()
    d2.close()
    

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
    device.open()
    s = device.read(force=True)
    assert s.wavelength is None
    device.close()


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
    device.open()
    device.read_raw()  # should not fail
    device.close()
    with pytest.raises(RuntimeError):
        device.read_raw()


def test_slices():
    data = Data(
        exposure=1,
        intensity=np.array([[10,11,12], [11,23,13], [14,15,16]]),
        clipped=np.array([[0,0,0], [0,0,0], [0,0,0]])
    )
    assert np.array_equal(data[1:].intensity, [[11,23,13], [14,15,16]])
    assert np.array_equal(data[1:,1:2].intensity, np.array([[23], [15]]))

    data = Spectrum(
        exposure=1,
        intensity=np.array([[10,11,12], [11,23,13], [14,15,16]]),
        clipped=np.array([[0,0,0], [0,0,0], [0,0,0]]),
        wavelength=np.array([100, 101, 102])
    )

    assert np.array_equal(data[1:].intensity, [[11,23,13], [14,15,16]])
    assert np.array_equal(data[1:,1:2].intensity, np.array([[23], [15]]))
    assert np.array_equal(data[1:].wavelength, data.wavelength)
    assert np.array_equal(data[:,1:].wavelength, np.array([101, 102]))


def test_non_block_read(device: Spectrometer, tmp_path):
    profile_path = str(tmp_path / 'profile.json')
    dark_signal_path = str(tmp_path / 'dark')
    wls = np.arange(0, 10, 1)
    write_calibration_data(profile_path, wls.tolist())
    device.set_config(dark_signal_path=dark_signal_path, wavelength_calibration_path=profile_path)
    device.read_dark_signal()

    frames_read = 0
    def callback(spectrum):
        nonlocal frames_read
        frames_read +=1
        assert isinstance(spectrum, Spectrum)


    device.read_non_block(callback, frames_to_read=5, frames_interval=1)  # Read 5 frames, 1 at time
    assert frames_read == 5

    frames_read = 0
    device.read_non_block(callback, frames_to_read=6, frames_interval=2)  # Read 6 frames, 2 at time
    assert frames_read == 6