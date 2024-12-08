cmake_minimum_required(VERSION 3.22)

project(usb_device)

set(CMAKE_CXX_STANDARD 20)
set(PYMODULE_NAME usb_device)

find_package(Python 3.7 COMPONENTS Interpreter Development REQUIRED)
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE pybind11_ROOT)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(${PYMODULE_NAME})

find_package(LibFTDI1 REQUIRED)
include(${LIBFTDI_USE_FILE})
target_link_libraries(${PYMODULE_NAME} PRIVATE ${LIBFTDIPP_LIBRARIES})
add_compile_definitions(PYSPECTRUM_USE_LIBFTDI)

target_sources(${PYMODULE_NAME} PRIVATE
  usb_device_cpp/UsbDevice.cpp
  usb_device_cpp/UsbContext.cpp
  usb_device_cpp/pymodule.cpp)

target_compile_definitions(${PYMODULE_NAME} PRIVATE
  VERSION_INFO=${VERSION_INFO}
  PYMODULE_NAME=${PYMODULE_NAME})