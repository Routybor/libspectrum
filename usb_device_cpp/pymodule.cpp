#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "UsbDevice.h"

PYBIND11_MODULE(PYMODULE_NAME, m)
{
    pybind11::class_<UsbDevice>(m, "UsbDevice")
        .def(pybind11::init<int, int, int>())
        .def("read_frame", &UsbDevice::read_frame)
        .def("get_pixel_count", &UsbDevice::get_pixel_count)
        .def("set_timer", &UsbDevice::set_timer)
        .def("close", &UsbDevice::close)
        .def_property_readonly("is_opened", &UsbDevice::is_opened);

    pybind11::class_<Frame>(m, "Frame")
        .def_property_readonly("samples", &Frame::pyGetSamples)
        .def_property_readonly("clipped", &Frame::pyGetClipped);
}