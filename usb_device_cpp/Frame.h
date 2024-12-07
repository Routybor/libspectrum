#pragma once
#include <vector>
#include "pybind11/pybind11.h"
#include "pybind11/numpy.h"
#include <iostream>

struct Frame {
    unsigned int n_samples;
    unsigned int n_measures;
    std::vector<int> samples;
    std::vector<uint8_t> clipped;

    pybind11::array_t<int> pyGetSamples() {
        return pybind11::array_t<int>({n_measures, n_samples},
                                {n_samples * sizeof(int), sizeof(int)},
                                samples.data());
    }

    pybind11::array_t<uint8_t> pyGetClipped() {
        return pybind11::array_t<uint8_t>(
            {n_measures, n_samples},
            {n_samples * sizeof(uint8_t), sizeof(uint8_t)}, clipped.data());
    }
};
