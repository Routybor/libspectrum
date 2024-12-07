#include "UsbDevice.h"
#include <chrono>

UsbDevice::UsbDevice(int vendor, int product, int64_t read_timeout)
    : read_timeout(read_timeout)
{
    context.open(vendor, product);
    context.setBitmode(0x40, 0x40);
    context.setTimeouts(300, 300);
    send_command(COMMAND_WRITE_CR, 0);
    send_command(COMMAND_WRITE_TIMER, 0x03e8);
    send_command(COMMAND_WRITE_PIXEL_NUMBER, pixel_number);
}

// 10 bits for significand
// 2 bits for exponent
void UsbDevice::set_timer(unsigned long millis)
{
    millis *= 10;
    int exponent = 0;
    while (millis >= (1 << 10))
    {
        exponent++;
        millis /= 10;
    }
    if (exponent >= 4)
    {
        throw std::overflow_error("Exposure is to big");
    }
    uint32_t command_data = millis | (exponent << 16);

    send_command(COMMAND_WRITE_TIMER, command_data);
}

unsigned int UsbDevice::get_pixel_count() { return pixel_number; }

Frame UsbDevice::read_frame(int n_times)
{
    Frame ret{
        get_pixel_count(),
        static_cast<unsigned int>(n_times),
        std::vector<int>(n_times * pixel_number),
        std::vector<uint8_t>(n_times * pixel_number),
    };
    std::vector<uint16_t> data(pixel_number * n_times);

    send_command(COMMAND_READ_FRAME, n_times);
    read_data(reinterpret_cast<uint8_t *>(data.data()),
              pixel_number * n_times * 2);

    std::transform(data.begin(), data.end(), ret.samples.begin(),
                   [](uint16_t n)
                   { return n ^ (1 << 15); });
    std::transform(ret.samples.begin(), ret.samples.end(), ret.clipped.begin(),
                   [](uint16_t n)
                   { return n == UINT16_MAX; });

    return ret;
}

DeviceReply UsbDevice::send_command(uint8_t code, uint32_t data)
{
    DeviceCommand command = {
        {'#', 'C', 'M', 'D'}, code, 4, sequenceNumber++, data};
    context.write(reinterpret_cast<unsigned char *>(&command),
                  sizeof(DeviceCommand));
    DeviceReply reply{};
    read_exactly(reinterpret_cast<unsigned char *>(&reply), sizeof(DeviceReply));
    if (memcmp(reply.magic, "#ANS", 4) != 0)
    {
        throw std::runtime_error("Received bad #ANS magic from device");
    }
    return reply;
}

void UsbDevice::read_data(uint8_t *buffer, size_t amount)
{
    size_t dataRead = 0;
    while (dataRead < amount)
    {
        DeviceDataHeader header{};
        read_exactly(reinterpret_cast<unsigned char *>(&header), sizeof(header));
        if (memcmp(header.magic, "#DAT", 4) != 0)
        {
            throw std::runtime_error("Received bad #DAT magic from device");
        }
        if (header.length > (amount - dataRead))
        {
            throw std::overflow_error("Trying to read more data than expected");
        }
        read_exactly(buffer + dataRead, header.length);
        dataRead += header.length;
    }
}

static int64_t get_current_time()
{
    return std::chrono::duration_cast<std::chrono::milliseconds>(
               std::chrono::system_clock::now().time_since_epoch())
        .count();
}

void UsbDevice::read_exactly(uint8_t *buff, int amount)
{
    int wasRead = 0;
    int64_t lastSuccessfulRead = get_current_time();
    while (wasRead != amount)
    {
        int chunkSize = context.read(buff + wasRead, amount - wasRead);
        wasRead += chunkSize;
        int64_t currentTime = get_current_time();
        if (currentTime - lastSuccessfulRead > read_timeout)
        {
            throw std::runtime_error("Device read timeout");
        }
    }
}

void UsbDevice::close()
{
    context.close();
    opened = false;
}
bool UsbDevice::is_opened()
{
    return opened;
}
