#pragma once
#include <cstddef>
#include <cstdint>

constexpr size_t WAV_HEADER_SIZE = 44;

// Canonical 44-byte RIFF/WAVE header for mono PCM (8 or 16 bits per sample).
void wavHeaderMono(uint8_t out[WAV_HEADER_SIZE], uint32_t sampleRate, uint16_t bitsPerSample, uint32_t dataBytes);
