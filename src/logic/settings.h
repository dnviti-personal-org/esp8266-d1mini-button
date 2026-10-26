#pragma once
#include <cstddef>
#include <cstdint>

// Persistent settings. Fixed-size so the struct can be stored as-is.
struct Settings {
    char wifi_ssid[33];
    char wifi_pass[65];
    char mqtt_host[65];
    uint16_t mqtt_port;
    char mqtt_user[33];
    char mqtt_pass[65];
    char topic_prefix[33];
    char ha_prefix[33];
    uint8_t power_mode;      // PowerMode
    uint16_t awake_seconds;  // battery mode: config window after power-on / reset
    uint16_t record_seconds; // audio recording length per press, 0 = disabled
    uint8_t mic_gain;        // digital gain applied to the I2S samples, 1..64
};

enum PowerMode : uint8_t { POWER_BATTERY = 0, POWER_ALWAYS_ON = 1 };

// Stored image: header + settings + CRC. Exactly what goes to EEPROM.
struct SettingsBlob {
    uint32_t magic;
    uint8_t version;
    uint8_t reserved[3];
    Settings settings;
    uint32_t crc;
};

constexpr uint32_t SETTINGS_MAGIC = 0x314E5442;  // "BTN1"
constexpr uint8_t SETTINGS_VERSION = 3;  // v2: record_seconds, v3: mic_gain

struct SetResult {
    bool ok;
    const char* message;  // human readable error or nullptr
};

Settings settingsDefaults();
bool settingsWifiConfigured(const Settings& s);
bool settingsMqttConfigured(const Settings& s);
SetResult settingsSet(Settings& s, const char* key, const char* value);
const char* powerModeName(uint8_t mode);

uint32_t crc32(const void* data, size_t len);
void settingsEncode(const Settings& s, SettingsBlob& out);
// Returns false when the blob is invalid (bad magic/version/CRC); out untouched.
bool settingsDecode(const SettingsBlob& blob, Settings& out);
