import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.widgets import Button, TextBox
from os import path
from typing import List
from matplotlib.ticker import AutoMinorLocator
import sys

from pyspectrum import Spectrometer, FactoryConfig
from pyspectrum.data import Spectrum

import matplotlib.style as mplstyle
mplstyle.use('fast')

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# Spectrometer initialization (USB) - replace with your IDs
VENDOR_ID = 0x0403
PRODUCT_ID = 0x6014
spectrometer = Spectrometer(vendor=VENDOR_ID, product=PRODUCT_ID, factory_config=FactoryConfig(2050, 3850, True, 1.0))

matplotlib.use("Qt5agg")

spectrum_figure, intensity_ax = plt.subplots(nrows=1, ncols=1)
spectrum_figure.subplots_adjust(bottom=0.3)

is_running = True
dark_signal_frames = 1000
frames_interval = 100
spectrum_line, = intensity_ax.plot([], [], color='black', linewidth=0.8)

plt.show(block=False)

def close_application(_):
    global is_running
    is_running = False
    spectrometer.stop_reading()
    plt.close(spectrum_figure)

spectrum_figure.canvas.mpl_connect('close_event', close_application)

# --- Input boxes ---
def update_dark_frames(text):
    global dark_signal_frames
    try:
        dark_signal_frames = int(text)
        eprint(f"Setting dark signal frames to {dark_signal_frames}")
    except ValueError:
        eprint(f"Invalid value: {text} Using default dark frames: {dark_signal_frames}")


def update_frames_interval(text):
    global frames_interval
    try:
        frames_interval = int(text)
        eprint(f"Setting frames interval to {frames_interval}")
    except ValueError:
       eprint(f"Invalid value: {text} Using default frames interval: {frames_interval}")


dark_frames_input_box_ax = spectrum_figure.add_axes([0.2, 0.15, 0.15, 0.04]) # Adjusted y position
frames_interval_input_box_ax = spectrum_figure.add_axes([0.60, 0.15, 0.15, 0.04]) # Adjusted y position

dark_frames_input_box = TextBox(dark_frames_input_box_ax, "Dark frames:", initial=str(dark_signal_frames))
frames_interval_input_box = TextBox(frames_interval_input_box_ax, "Frames Interval:", initial=str(frames_interval))

dark_frames_input_box.on_submit(update_dark_frames)
frames_interval_input_box.on_submit(update_frames_interval)


# --- Buttons ---
dark_signal_button_ax = spectrum_figure.add_axes([0.5, 0.05, 0.2, 0.075])
load_profile_button_ax = spectrum_figure.add_axes([0.71, 0.05, 0.2, 0.075])

dark_signal_button = Button(dark_signal_button_ax, 'Read Dark Signal')

def capture_and_save_dark_signal(_):
    eprint("Capturing dark signal...")
    spectrometer.read_dark_signal(n_times=dark_signal_frames)
    eprint("Dark signal captured!")

dark_signal_button.on_clicked(capture_and_save_dark_signal)


load_profile_button = Button(load_profile_button_ax, 'Load Profile Data')
profile_path = path.join(path.dirname(path.realpath(__file__)), 'data/profile.json')


def load_profile(_):
    spectrometer.set_config(wavelength_calibration_path=profile_path)
    eprint("Wavelength profile loaded!")

load_profile_button.on_clicked(load_profile)

acquisition_times = 100
exposure_time_ms = 1
spectrometer.set_config(n_times=acquisition_times, exposure=exposure_time_ms)


def update_spectrum_plot(spectrum):
    global spectrum_line
    if spectrum.intensity.size == 0:
       spectrum_line.set_data([],[])
       return

    wavelengths = spectrum.wavelength
    intensities = np.mean(spectrum.intensity, axis=0)

    spectrum_line.set_data(wavelengths,intensities)

    intensity_ax.set_xlabel("Wavelength")
    intensity_ax.set_ylabel("Intensity")
    intensity_ax.set_title("Spectrum graph:")
    intensity_ax.relim()
    intensity_ax.autoscale_view(True,True,True)
    intensity_ax.xaxis.set_minor_locator(AutoMinorLocator())
    intensity_ax.yaxis.set_minor_locator(AutoMinorLocator())

    intensity_ax.draw_artist(intensity_ax.patch)
    intensity_ax.draw_artist(spectrum_line)
    spectrum_figure.canvas.update()

def start_spectrum_acquisition(_):
    if spectrometer.is_configured:
        update_spectrum_plot(spectrometer.read())
        spectrometer.read_non_stop(update_spectrum_plot, frames_interval)
        eprint("Started spectrum read")


def stop_spectrum_read(_):
    spectrometer.stop_reading()
    eprint("Stopped spectrum read")


start_read_button_ax = spectrum_figure.add_axes([0.05, 0.05, 0.2, 0.075])
stop_read_button_ax = spectrum_figure.add_axes([0.26, 0.05, 0.2, 0.075])

start_read_button = Button(start_read_button_ax, 'Start Read')
start_read_button.on_clicked(start_spectrum_acquisition)

stop_read_button = Button(stop_read_button_ax, 'Stop Read')
stop_read_button.on_clicked(stop_spectrum_read)

update_spectrum_plot(Spectrum(intensity = np.array([]), clipped=np.array([]), wavelength = np.array([]), exposure = 0))
spectrum_figure.canvas.draw()

plt.show()