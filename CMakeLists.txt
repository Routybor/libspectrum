cmake_minimum_required(VERSION 3.22)

project(c_test)

set(CMAKE_CXX_STANDARD 20)
set(PYMODULE_NAME _pyspectrum)

add_subdirectory(thirdparty/pybind11)
pybind11_add_module(${PYMODULE_NAME})

if(WIN32)
  include(ExternalProject)
  ExternalProject_Add(d2xx
    URL https://ftdichip.com/wp-content/uploads/2023/09/CDM-v2.12.36.4-WHQL-Certified.zip
    SOURCE_DIR thirdparty/ftd2xx
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND "")
  add_dependencies(${PYMODULE_NAME} d2xx)
  target_include_directories(${PYMODULE_NAME} PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/thirdparty/ftd2xx)
  target_link_directories(${PYMODULE_NAME} PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/thirdparty/ftd2xx/amd64)
  target_link_libraries(${PYMODULE_NAME} PRIVATE ftd2xx)
  add_compile_definitions(PYSPECTRUM_USE_D2XX)
else()
  find_package(LibFTDI1 REQUIRED)
  include(${LIBFTDI_USE_FILE})
  target_link_libraries(${PYMODULE_NAME} PRIVATE ${LIBFTDIPP_LIBRARIES})
  add_compile_definitions(PYSPECTRUM_USE_LIBFTDI)
endif()

target_sources(${PYMODULE_NAME} PRIVATE
  src/UsbRawSpectrometer.cpp
  src/UsbContext.cpp
  src/pymodule.cpp)

target_compile_definitions(${PYMODULE_NAME} PRIVATE
  VERSION_INFO=${VERSION_INFO}
  PYMODULE_NAME=${PYMODULE_NAME})
