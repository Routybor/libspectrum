#pragma once

#include <memory>

class UsbContext {
    public:
        UsbContext();
        ~UsbContext();
        void open(int vendor, int product);
        void close();
        void setBitmode(unsigned char mask, unsigned char enable);
        void setTimeouts(int readTimeoutMillis, int writeTimeoutMillis);
        int read(unsigned char *buf, int size);
        int write(unsigned char *buf, int size);

    private:
        struct Private;
        std::unique_ptr<Private> p;
};
