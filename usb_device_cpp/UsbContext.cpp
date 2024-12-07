#include <stdexcept>

#include <ftdi.hpp>

#include "UsbContext.h"

struct UsbContext::Private {
    Ftdi::Context context;
};

UsbContext::UsbContext() : p(new Private) {}
UsbContext::~UsbContext() {}

void UsbContext::open(int vendor, int product) {
    if (p->context.open(vendor, product) < 0) {
        throw std::runtime_error("Failed to open device");
    }
}

void UsbContext::close() {
    if (p->context.close() < 0) {
        throw std::runtime_error("Failed to close device");
    }
}

void UsbContext::setBitmode(unsigned char mask, unsigned char enable) {
    if (p->context.set_bitmode(mask, enable) < 0) {
        throw std::runtime_error("Failed to set bitmode");
    }
}

void UsbContext::setTimeouts(int readTimeoutMillis, int writeTimeoutMillis) {
    p->context.set_usb_read_timeout(readTimeoutMillis);
    p->context.set_usb_write_timeout(writeTimeoutMillis);
}

int UsbContext::read(unsigned char *buf, int size) {
    int res = p->context.read(buf, size);
    if (res < 0) {
        throw std::runtime_error("Device read error");
    }
    return res;
}

int UsbContext::write(unsigned char *buf, int size) {
    int res = p->context.write(buf, size);
    if (res < 0) {
        throw std::runtime_error("Device write error");
    }
    return res;
}