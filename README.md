
---

# Libspectrum
![](https://img.shields.io/pypi/v/vmk-spectrum)
![](https://img.shields.io/github/actions/workflow/status/leadpogrommer/libspectrum/release.yml)

[Documentation](https://leadpogrommer.ru/libspectrum/)

**Description:**
Library for interfacing with VMK made spectrometers.

---

## Repository Structure

The following explains the main directories and files in this repository.

```plaintext
.
├── docs/
│   ├── examples
│   ├── index.md
│   ├── installation.md
│   └── reference.md
│
├── examples/
│   ├── data/
│   │   ├── heat_2200
│   │   ├── lamp2
│   │   └── profile.json
│   ├── .gitignore
│   ├── aproximations.py
│   ├── colorimeter_data.py
│   ├── colorimeter.ipynb
│   ├── colorimeter.py
│   ├── exposure_setting.py
│   ├── led_calculator.py
│   ├── led_parameters.ipynb
│   ├── pyrometer.ipynb
│   ├── pyrometer.py
│   ├── realtime_graph.py
│   ├── record_spectrum.ipynb
│   └── simple_notebook.ipynb
│
├── pyspectrum/
│   ├── __init__.py
│   ├── data.py
│   ├── device_factory.py
│   ├── errors.py
│   ├── ethernet_device.py
│   └── spectrometer.py
│
├── src/
│   ├── main.ccp
│   ├── pymodule.cpp
│   ├── RawSpectrometer.h
│   ├── RawSpectrum.h
│   ├── UsbContext.cpp
│   ├── UsbContext.h
│   ├── UsbContextD2XX.cpp
│   ├── UsbContextLibFTDI.cpp
│   ├── UsbRawSpectrometer.cpp
│   └── UsbRawSpectrometer.h
│
├── tests/
│   ├── __init__.py
│   └── test_spectrometer.py
│
├── thirdparty/
│   └── pybind11/
│
├── utils/
│   ├── convert.py
│   └── format.sh
│
├── .clang-format
├── .gitignore
├── .gitmodules
├── CMakeLists.txt
├── mkdocs.yml
├── pyproject.toml
├── README.md
└── setup.py
```

### Directories and Files Overview

- **`docs/`**: Contains the project's documentation.
  - `examples/`: Example notebooks or scripts demonstrating usage.
  - `index.md`: Main documentation index.
  - `installation.md`: Instructions for installing the project.
  - `reference.md`: Technical reference for the project.

- **`examples/`**: Example scripts, notebooks, and data files for demonstrating and testing functionalities.
  - `data/`: Sample datasets (`heat_2200`, `lamp2`, `profile.json`).
  - `.gitignore`: Gitignore.
  - `aproximations.py`: Script containing approximation-related values.
  - `colorimeter_data.py`: Processed data values from colorimeter.
  - `colorimeter.py`: Calorimeter class implementation.
  - `colorimeter.ipynb`: Jupyter notebook example using Colorimeter class.
  - `exposure_setting.py`: Exposure's values definitions.
  - `led_calculator.py`: LedParameters class implementation.
  - `led_parameters.ipynb`: Jupyter notebook example using LedParameters class.
  - `pyrometer.py`: Pyrometer class implementation.
  - `pyrometer.ipynb`: Jupyter notebook example using Pyrometer class.
  - `realtime_graph.py`: Showing graph from ethernet device.
  - `record_spectrum.ipynb`: Writing spectrum data in file.
  - `simple_notebook.ipynb`: Just library work example in Jypyter.

- **`pyspectrum/`**: Core Python library for interacting with spectrometers.
  - `__init__.py`: Initializes the `pyspectrum` module.
  - `data.py`: Handles data management within the library.
  - `device_factory.py`: Handles of USB device management.
  - `errors.py`: Custom exceptions and error handling.
  - `ethernet_device.py`: Module for managing Ethernet-connected devices.
  - `spectrometer.py`: Main class for interfacing with spectrometers.

- **`src/`**: Driver's source C++ code, for device interaction.
  - `main.cpp`: Main entry point for the C++ components.
  - `pymodule.cpp`: Python bindings for the C++ code.
  - `UsbContext.*`: Files related to USB device context management.
  - `RawSpectrometer.*`: Code handling raw spectrometer interactions.

- **`tests/`**: Contains unit tests to validate functionality of wrapper.
  - `__init__.py`: Initializes the `tests` package.
  - `test_spectrometer.py`: Test cases for spectrometer functionality.

- **`thirdparty/`**: External libraries or modules used in project.
  - `pybind11/`: Contains link the Pybind11 rep used for creating Python bindings for C++.

- **`utils/`**: Utility scripts for other tasks.
  - `convert.py`: A script for converting file formats.
  - `format.sh`: A shell script for formatting files with clang-format.

- **Other files**:
  - `.clang-format`: Configuration for C++ code formatting.
  - `.gitignore`: Gitgnore.
  - `.gitmodules`: Git submodules.
  - `CMakeLists.txt`: CMake build configuration file.
  - `mkdocs.yml`: Configuration for MkDocs, used to generate documentation.
  - `pyproject.toml`: Project metadata and configuration for Python packaging.
  - `README.md`: Overview and instructions for the project.
  - `setup.py`: Script for installing Python package.

---

### Installation

#### INSTALLATION EXPLAIN

### Usage

#### USAGE EXPLAIN

### Running Tests

#### To run python-wrapper tests :

```bash
# To run tests
python3.10 tests/test_spectrometer.py
```

---

### Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m 'Add feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

---
