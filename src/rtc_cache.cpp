#include "rtc_cache.h"
#include <Arduino.h>
#include <cstring>

namespace {
constexpr uint32_t CACHE_MAGIC = 0x57494643;  // "WIFC"
constexpr uint32_t RTC_OFFSET = 64;           // 4-byte blocks; 0..63 are reserved by the SDK
struct Image {
    uint32_t magic;
    WifiCache cache;
    uint8_t pad;
    uint32_t check;
};
uint32_t sum(const WifiCache& c) {
    uint32_t s = c.channel;
    for (uint8_t b : c.bssid) s = s * 31 + b;
    return s ^ 0xA5A5A5A5u;
}
}

bool rtcCacheLoad(WifiCache& out) {
    Image img;
    if (!ESP.rtcUserMemoryRead(RTC_OFFSET, reinterpret_cast<uint32_t*>(&img), sizeof(img))) return false;
    if (img.magic != CACHE_MAGIC || img.check != sum(img.cache)) return false;
    out = img.cache;
    return true;
}

bool rtcCacheValid() { WifiCache c; return rtcCacheLoad(c); }

void rtcCacheSave(const WifiCache& c) {
    Image img{};
    img.magic = CACHE_MAGIC;
    img.cache = c;
    img.check = sum(c);
    ESP.rtcUserMemoryWrite(RTC_OFFSET, reinterpret_cast<uint32_t*>(&img), sizeof(img));
}

void rtcCacheClear() {
    Image img{};
    ESP.rtcUserMemoryWrite(RTC_OFFSET, reinterpret_cast<uint32_t*>(&img), sizeof(img));
}
