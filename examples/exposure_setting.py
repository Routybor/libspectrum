from pyspectrum import Spectrometer
from time import time

exposures = [1, 2, 3, 4, 5, 10, 20, 50, 100, 200, 250, 500]
d = Spectrometer()
d.open()

for exposure in exposures:
    n = int(min(500, 10 / (exposure / 1000)))
    d.set_config(exposure=exposure, n_times=n)

    print(f'{exposure=} {n=} ...')
    t_start= time()
    d.read_raw()
    t = time() - t_start

    print(f'{t/n*1000} real exposure, {t} s total\n')

d.close()
