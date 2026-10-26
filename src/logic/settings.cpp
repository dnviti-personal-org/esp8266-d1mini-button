#include "settings.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace {

SetResult copyField(char* dst, size_t dstSize, const char* value, bool allowEmpty) {
    size_t len = strlen(value);
    if (len == 0 && !allowEmpty) return {false, "value required"};
    if (len >= dstSize) return {false, "value too long"};
    memcpy(dst, value, len + 1);
    return {true, nullptr};
}

bool parseUint(const char* value, long min, long max, long& out) {
    char* end = nullptr;
    long v = strtol(value, &end, 10);
    if (end == value || *end != 0) return false;
    if (v < min || v > max) return false;
    out = v;
    return true;
}

}  // namespace

Settings settingsDefaults() {
    Settings s;
    memset(&s, 0, sizeof(s));
    s.mqtt_port = 1883;
    strcpy(s.topic_prefix, "esp8266button");
    strcpy(s.ha_prefix, "homeassistant");
    s.power_mode = POWER_BATTERY;
    s.awake_seconds = 60;
    return s;
}

bool settingsWifiConfigured(const Settings& s) { return s.wifi_ssid[0] != 0; }
bool settingsMqttConfigured(const Settings& s) { return s.mqtt_host[0] != 0 && s.mqtt_port != 0; }

const char* powerModeName(uint8_t mode) {
    return mode == POWER_ALWAYS_ON ? "always_on" : "battery";
}

SetResult settingsSet(Settings& s, const char* key, const char* value) {
    if (!key || !value) return {false, "missing key"};
    if (strcmp(key, "ssid") == 0) return copyField(s.wifi_ssid, sizeof(s.wifi_ssid), value, false);
    if (strcmp(key, "pass") == 0) return copyField(s.wifi_pass, sizeof(s.wifi_pass), value, true);
    if (strcmp(key, "mqtt_host") == 0) return copyField(s.mqtt_host, sizeof(s.mqtt_host), value, false);
    if (strcmp(key, "mqtt_user") == 0) return copyField(s.mqtt_user, sizeof(s.mqtt_user), value, true);
    if (strcmp(key, "mqtt_pass") == 0) return copyField(s.mqtt_pass, sizeof(s.mqtt_pass), value, true);
    if (strcmp(key, "prefix") == 0) {
        if (strchr(value, '/') || strchr(value, '#') || strchr(value, '+') || strchr(value, ' '))
            return {false, "prefix must not contain / # + or spaces"};
        return copyField(s.topic_prefix, sizeof(s.topic_prefix), value, false);
    }
    if (strcmp(key, "ha_prefix") == 0) {
        if (strchr(value, '#') || strchr(value, '+') || strchr(value, ' '))
            return {false, "ha_prefix must not contain # + or spaces"};
        return copyField(s.ha_prefix, sizeof(s.ha_prefix), value, false);
    }
    if (strcmp(key, "mqtt_port") == 0) {
        long v;
        if (!parseUint(value, 1, 65535, v)) return {false, "port must be 1..65535"};
        s.mqtt_port = (uint16_t)v;
        return {true, nullptr};
    }
    if (strcmp(key, "awake_seconds") == 0) {
        long v;
        if (!parseUint(value, 5, 3600, v)) return {false, "awake_seconds must be 5..3600"};
        s.awake_seconds = (uint16_t)v;
        return {true, nullptr};
    }
    if (strcmp(key, "power_mode") == 0) {
        if (strcmp(value, "battery") == 0) { s.power_mode = POWER_BATTERY; return {true, nullptr}; }
        if (strcmp(value, "always_on") == 0) { s.power_mode = POWER_ALWAYS_ON; return {true, nullptr}; }
        return {false, "power_mode must be battery or always_on"};
    }
    return {false, "unknown key (see help)"};
}

uint32_t crc32(const void* data, size_t len) {
    const uint8_t* p = static_cast<const uint8_t*>(data);
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; ++i) {
        crc ^= p[i];
        for (int b = 0; b < 8; ++b) crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

void settingsEncode(const Settings& s, SettingsBlob& out) {
    memset(&out, 0, sizeof(out));
    out.magic = SETTINGS_MAGIC;
    out.version = SETTINGS_VERSION;
    out.settings = s;
    out.crc = crc32(&out.settings, sizeof(out.settings));
}

bool settingsDecode(const SettingsBlob& blob, Settings& out) {
    if (blob.magic != SETTINGS_MAGIC || blob.version != SETTINGS_VERSION) return false;
    if (crc32(&blob.settings, sizeof(blob.settings)) != blob.crc) return false;
    out = blob.settings;
    // Guarantee NUL termination even if flash held garbage with a valid CRC.
    out.wifi_ssid[sizeof(out.wifi_ssid) - 1] = 0;
    out.wifi_pass[sizeof(out.wifi_pass) - 1] = 0;
    out.mqtt_host[sizeof(out.mqtt_host) - 1] = 0;
    out.mqtt_user[sizeof(out.mqtt_user) - 1] = 0;
    out.mqtt_pass[sizeof(out.mqtt_pass) - 1] = 0;
    out.topic_prefix[sizeof(out.topic_prefix) - 1] = 0;
    out.ha_prefix[sizeof(out.ha_prefix) - 1] = 0;
    return true;
}
