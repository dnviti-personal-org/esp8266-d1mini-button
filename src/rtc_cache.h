#pragma once
#include <cstdint>

// Wi-Fi association cache kept in RTC user memory across deep sleep:
// reconnecting with a known channel and BSSID skips the scan (~1 s, ~80 mAs).
struct WifiCache {
    uint8_t channel;
    uint8_t bssid[6];
};

bool rtcCacheValid();
bool rtcCacheLoad(WifiCache& out);
void rtcCacheSave(const WifiCache& c);
void rtcCacheClear();
