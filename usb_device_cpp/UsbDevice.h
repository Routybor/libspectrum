#pragma once

#include "UsbContext.h"
#include "Frame.h"

#define COMMAND_WRITE_CR 0x01
#define COMMAND_WRITE_TIMER 0x02
#define COMMAND_WRITE_PIXEL_NUMBER 0x0c
#define COMMAND_READ_ERRORS 0x92
#define COMMAND_READ_VERSION 0x91
#define COMMAND_READ_FRAME 0x05

#pragma pack(push, 1)

struct DeviceCommand
{
    char magic[4];
    uint8_t code;
    uint8_t length;
    uint16_t sequenceNumber;
    uint32_t data;
};

struct DeviceReply
{
    char magic[4];
    char code;
    uint8_t length;
    uint16_t sequenceNumber;
    uint16_t data;
};

struct DeviceDataHeader
{
    char magic[4];
    uint16_t length;
};

#pragma pack(pop)

class UsbDevice {
    public:
        UsbDevice(int vendor, int product, int64_t read_timeout);
        void set_timer(unsigned long millis);
        unsigned int get_pixel_count();
        Frame read_frame(int n_times);
        void close();
        bool is_opened();

    private:
        int64_t read_timeout;
        const int pixel_number = 0x1006;
        uint16_t sequenceNumber = 1;
        UsbContext context;
        bool opened = true;

        void read_exactly(uint8_t *buff, int amount);
        DeviceReply send_command(uint8_t code, uint32_t data);
        void read_data(uint8_t *buffer, size_t amount);
};
