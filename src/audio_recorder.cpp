#include "audio_recorder.h"
#include <core_esp8266_i2s.h>

namespace {
constexpr size_t MASK = AUDIO_RING_SIZE - 1;
constexpr uint32_t PROBE_FRAMES = 800;  // 50 ms at 16 kHz: pick the half-word the mic really drives
uint8_t ring[AUDIO_RING_SIZE];
}

void AudioRecorder::begin(uint8_t micPowerPin) {
    micPin_ = micPowerPin;
    pinMode(micPin_, OUTPUT);
    digitalWrite(micPin_, LOW);
}

void AudioRecorder::start(uint32_t seconds, uint8_t gain) {
    if (active_) stop();
    gain_ = gain ? gain : 1;
    head_ = tail_ = 0;
    produced_ = 0;
    overruns_ = 0;
    peak_ = 0;
    haveFirst_ = false;
    channel_ = -1;
    absL_ = absR_ = probe_ = 0;
    targetBytes_ = seconds * AUDIO_SAMPLE_RATE * (AUDIO_BITS / 8);
    digitalWrite(micPin_, HIGH);
    delay(100);  // INMP441 power-up / settling
    i2s_rxtx_begin(true, false);
    i2s_set_rate(I2S_RATE);
    active_ = targetBytes_ > 0;
    // discard the first frames (mic wake-up transient)
    int16_t l, r;
    for (int i = 0; i < 256; ++i) if (!i2s_read_sample(&l, &r, false)) break;
}

void AudioRecorder::stop() {
    if (active_) i2s_end();
    digitalWrite(micPin_, LOW);
    active_ = false;
}

void AudioRecorder::push16(int16_t v) {
    if (((head_ + 2 - tail_) & MASK) == 0 || ((head_ + 1 - tail_) & MASK) == 0) { ++overruns_; return; }
    ring[head_] = (uint8_t)(v & 0xff);
    ring[(head_ + 1) & MASK] = (uint8_t)((uint16_t)v >> 8);
    head_ = (head_ + 2) & MASK;
}

void AudioRecorder::loop() {
    if (!active_ || produced_ >= targetBytes_) return;
    int16_t l, r;
    int guard = 1024;  // never spin for more than ~64 ms of audio per call
    while (guard-- > 0 && produced_ < targetBytes_ && i2s_read_sample(&l, &r, false)) {
        if (channel_ < 0) {  // probe which half-word carries the microphone
            absL_ += abs(l); absR_ += abs(r);
            if (++probe_ >= PROBE_FRAMES) channel_ = absR_ > absL_ ? 1 : 0;
            continue;
        }
        int32_t v = channel_ ? r : l;
        if (!haveFirst_) { firstL_ = v; haveFirst_ = true; continue; }
        int32_t avg = (firstL_ + v) / 2;  // decimate 16 kHz -> 8 kHz
        haveFirst_ = false;
        avg *= gain_;
        if (avg > 32767) avg = 32767; else if (avg < -32768) avg = -32768;
        int16_t s = (int16_t)avg;
        int16_t a = s < 0 ? -s : s;
        if (a > peak_) peak_ = a;
        push16(s);
        produced_ += 2;
    }
}

size_t AudioRecorder::read(uint8_t* dst, size_t maxLen) {
    size_t n = 0;
    while (n < maxLen && tail_ != head_) {
        dst[n++] = ring[tail_];
        tail_ = (tail_ + 1) & MASK;
    }
    return n;
}
