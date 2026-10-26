#include "wav.h"
#include <cstring>

namespace {
void put32(uint8_t* p, uint32_t v) { p[0] = v; p[1] = v >> 8; p[2] = v >> 16; p[3] = v >> 24; }
void put16(uint8_t* p, uint16_t v) { p[0] = v; p[1] = v >> 8; }
}

void wavHeaderMono(uint8_t out[WAV_HEADER_SIZE], uint32_t sampleRate, uint16_t bitsPerSample, uint32_t dataBytes) {
    const uint16_t blockAlign = bitsPerSample / 8;
    memcpy(out, "RIFF", 4);
    put32(out + 4, 36 + dataBytes);
    memcpy(out + 8, "WAVE", 4);
    memcpy(out + 12, "fmt ", 4);
    put32(out + 16, 16);                      // fmt chunk size
    put16(out + 20, 1);                       // PCM
    put16(out + 22, 1);                       // mono
    put32(out + 24, sampleRate);
    put32(out + 28, sampleRate * blockAlign); // byte rate
    put16(out + 32, blockAlign);
    put16(out + 34, bitsPerSample);
    memcpy(out + 36, "data", 4);
    put32(out + 40, dataBytes);
}
