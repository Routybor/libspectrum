from setuptools import setup, find_packages

setup(
    name="vmk-spectrum",
    version="0.0.10",
    author="name",
    description="Library for communication with VMK spectrometers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/routybor/libspectrum",
    packages=find_packages(),
    python_requires='>=3.10',
    extras_require={"test": ["pytest>=6.0"]},
    install_requires=[
        "numpy",
        "matplotlib",
        "scipy",
        "pylibftdi",
        "ftd2xx",
    ]
)