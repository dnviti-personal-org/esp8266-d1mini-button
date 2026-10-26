#pragma once
#include <Arduino.h>

// I2S MEMS microphone (INMP441 class) capture: the I2S peripheral + DMA fill
// the core's buffers with no CPU work; loop() drains them into a RAM ring as
// 16-bit mono PCM at AUDIO_SAMPLE_RATE. Nothing here touches the flash, the
// ADC or the Wi-Fi PHY.
constexpr uint32_t AUDIO_SAMPLE_RATE = 8000;   // output rate (WAV)
constexpr uint32_t I2S_RATE = 16000;           // I2S frame rate: SCK = 32 * 16 kHz = 512 kHz, in the INMP441 range
constexpr uint16_t AUDIO_BITS = 16;
constexpr size_t AUDIO_RING_SIZE = 16384;      // bytes: 1 s of pre-roll, power of two

class AudioRecorder {
public:
    void begin(uint8_t micPowerPin);
    void start(uint32_t seconds, uint8_t gain);  // powers the mic, starts I2S RX
    void stop();                                 // stops I2S, powers the mic down
    void loop();                                 // drain the DMA buffers into the ring
    bool sampling() const { return active_ && produced_ < targetBytes_; }
    bool active() const { return active_; }
    uint32_t targetBytes() const { return targetBytes_; }
    uint32_t producedBytes() const { return produced_; }
    uint32_t overruns() const { return overruns_; }
    int16_t peak() const { return peak_; }
    size_t available() const { return (head_ - tail_) & (AUDIO_RING_SIZE - 1); }
    size_t read(uint8_t* dst, size_t maxLen);

private:
    void push16(int16_t v);

    uint8_t micPin_ = 0;
    uint8_t gain_ = 1;
    uint32_t targetBytes_ = 0;
    uint32_t produced_ = 0;
    uint32_t overruns_ = 0;
    int16_t peak_ = 0;
    bool active_ = false;
    bool haveFirst_ = false;
    int32_t firstL_ = 0, firstR_ = 0;
    int8_t channel_ = -1;   // -1 undecided, 0 = "left" half, 1 = "right" half
    uint32_t absL_ = 0, absR_ = 0, probe_ = 0;
    size_t head_ = 0, tail_ = 0;
};
