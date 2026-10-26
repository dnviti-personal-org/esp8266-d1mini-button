#include <unity.h>
#include <cstring>
#include "button.h"
#include "command_parser.h"
#include "settings.h"
#include "wav.h"

void setUp() {}
void tearDown() {}

// ---------- Button ----------
void test_button_ignores_short_glitch() {
    Button b(50);
    b.update(false, 0);
    TEST_ASSERT_EQUAL(Button::Event::None, b.update(true, 10));
    TEST_ASSERT_EQUAL(Button::Event::None, b.update(false, 30));   // released before 50 ms
    TEST_ASSERT_EQUAL(Button::Event::None, b.update(false, 200));
    TEST_ASSERT_FALSE(b.isPressed());
}

void test_button_reports_press_and_release_after_debounce() {
    Button b(50);
    b.update(false, 0);
    TEST_ASSERT_EQUAL(Button::Event::None, b.update(true, 100));
    TEST_ASSERT_EQUAL(Button::Event::None, b.update(true, 140));
    TEST_ASSERT_EQUAL(Button::Event::Pressed, b.update(true, 150));
    TEST_ASSERT_TRUE(b.isPressed());
    TEST_ASSERT_EQUAL(Button::Event::None, b.update(true, 1000));  // held: no repeat
    TEST_ASSERT_EQUAL(Button::Event::None, b.update(false, 2000));
    TEST_ASSERT_EQUAL(Button::Event::Released, b.update(false, 2060));
    TEST_ASSERT_FALSE(b.isPressed());
}

void test_button_handles_millis_wraparound() {
    Button b(50);
    b.update(false, 0xFFFFFFF0u);
    b.update(true, 0xFFFFFFF8u);
    TEST_ASSERT_EQUAL(Button::Event::Pressed, b.update(true, 0x00000040u));
}

// ---------- Command parser ----------
void test_parse_empty_and_unknown() {
    TEST_ASSERT_EQUAL(Command::Type::Empty, parseCommand("").type);
    TEST_ASSERT_EQUAL(Command::Type::Empty, parseCommand("   \r").type);
    TEST_ASSERT_EQUAL(Command::Type::Unknown, parseCommand("frobnicate").type);
    TEST_ASSERT_EQUAL(Command::Type::Unknown, parseCommand("set").type);  // no key
}

void test_parse_simple_commands_case_insensitive() {
    TEST_ASSERT_EQUAL(Command::Type::Help, parseCommand("HELP").type);
    TEST_ASSERT_EQUAL(Command::Type::Show, parseCommand("  show  ").type);
    TEST_ASSERT_EQUAL(Command::Type::Save, parseCommand("save\n").type);
    TEST_ASSERT_EQUAL(Command::Type::Factory, parseCommand("factory").type);
    TEST_ASSERT_EQUAL(Command::Type::Stay, parseCommand("stay").type);
    TEST_ASSERT_EQUAL(Command::Type::Sleep, parseCommand("sleep").type);
}

void test_parse_set_keeps_spaces_in_value() {
    Command c = parseCommand("set ssid  My Home WiFi  \r\n");
    TEST_ASSERT_EQUAL(Command::Type::Set, c.type);
    TEST_ASSERT_EQUAL_STRING("ssid", c.key);
    TEST_ASSERT_EQUAL_STRING("My Home WiFi", c.value);
}

void test_parse_set_lowercases_key_not_value() {
    Command c = parseCommand("set PASS Secr3t Pa$$");
    TEST_ASSERT_EQUAL_STRING("pass", c.key);
    TEST_ASSERT_EQUAL_STRING("Secr3t Pa$$", c.value);
}

void test_parse_set_without_value_gives_empty_value() {
    Command c = parseCommand("set pass");
    TEST_ASSERT_EQUAL(Command::Type::Set, c.type);
    TEST_ASSERT_EQUAL_STRING("pass", c.key);
    TEST_ASSERT_EQUAL_STRING("", c.value);
}

// ---------- Settings ----------
void test_defaults() {
    Settings s = settingsDefaults();
    TEST_ASSERT_EQUAL_UINT16(1883, s.mqtt_port);
    TEST_ASSERT_EQUAL_STRING("esp8266button", s.topic_prefix);
    TEST_ASSERT_EQUAL_STRING("homeassistant", s.ha_prefix);
    TEST_ASSERT_EQUAL_UINT8(POWER_BATTERY, s.power_mode);
    TEST_ASSERT_EQUAL_UINT16(60, s.awake_seconds);
    TEST_ASSERT_EQUAL_UINT16(120, s.record_seconds);
    TEST_ASSERT_EQUAL_UINT8(8, s.mic_gain);
    TEST_ASSERT_FALSE(settingsWifiConfigured(s));
    TEST_ASSERT_FALSE(settingsMqttConfigured(s));
}

void test_set_valid_keys() {
    Settings s = settingsDefaults();
    TEST_ASSERT_TRUE(settingsSet(s, "ssid", "Home").ok);
    TEST_ASSERT_TRUE(settingsSet(s, "pass", "").ok);  // open network allowed
    TEST_ASSERT_TRUE(settingsSet(s, "mqtt_host", "192.168.1.10").ok);
    TEST_ASSERT_TRUE(settingsSet(s, "mqtt_port", "8883").ok);
    TEST_ASSERT_TRUE(settingsSet(s, "mqtt_user", "ha").ok);
    TEST_ASSERT_TRUE(settingsSet(s, "mqtt_pass", "x y").ok);
    TEST_ASSERT_TRUE(settingsSet(s, "prefix", "casa").ok);
    TEST_ASSERT_TRUE(settingsSet(s, "ha_prefix", "ha/disc").ok);
    TEST_ASSERT_TRUE(settingsSet(s, "power_mode", "always_on").ok);
    TEST_ASSERT_TRUE(settingsSet(s, "awake_seconds", "120").ok);
    TEST_ASSERT_TRUE(settingsSet(s, "record_seconds", "0").ok);
    TEST_ASSERT_TRUE(settingsSet(s, "mic_gain", "16").ok);
    TEST_ASSERT_EQUAL_UINT8(16, s.mic_gain);
    TEST_ASSERT_EQUAL_UINT16(0, s.record_seconds);
    TEST_ASSERT_EQUAL_UINT16(8883, s.mqtt_port);
    TEST_ASSERT_EQUAL_STRING("casa", s.topic_prefix);
    TEST_ASSERT_EQUAL_UINT8(POWER_ALWAYS_ON, s.power_mode);
    TEST_ASSERT_EQUAL_UINT16(120, s.awake_seconds);
    TEST_ASSERT_TRUE(settingsWifiConfigured(s));
    TEST_ASSERT_TRUE(settingsMqttConfigured(s));
}

void test_set_rejects_invalid() {
    Settings s = settingsDefaults();
    TEST_ASSERT_FALSE(settingsSet(s, "nope", "1").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "ssid", "").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "mqtt_port", "0").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "mqtt_port", "70000").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "mqtt_port", "12ab").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "prefix", "a/b").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "prefix", "a b").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "power_mode", "sometimes").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "awake_seconds", "1").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "record_seconds", "601").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "record_seconds", "-1").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "mic_gain", "0").ok);
    TEST_ASSERT_FALSE(settingsSet(s, "mic_gain", "65").ok);
    char longv[80];
    memset(longv, 'a', sizeof(longv) - 1);
    longv[sizeof(longv) - 1] = 0;
    TEST_ASSERT_FALSE(settingsSet(s, "ssid", longv).ok);
    TEST_ASSERT_EQUAL_UINT16(1883, s.mqtt_port);  // untouched
}

void test_encode_decode_roundtrip() {
    Settings s = settingsDefaults();
    settingsSet(s, "ssid", "Home");
    settingsSet(s, "pass", "secret");
    settingsSet(s, "mqtt_host", "broker.local");
    SettingsBlob blob;
    settingsEncode(s, blob);
    TEST_ASSERT_EQUAL_UINT32(SETTINGS_MAGIC, blob.magic);
    Settings out = settingsDefaults();
    TEST_ASSERT_TRUE(settingsDecode(blob, out));
    TEST_ASSERT_EQUAL_STRING("Home", out.wifi_ssid);
    TEST_ASSERT_EQUAL_STRING("secret", out.wifi_pass);
    TEST_ASSERT_EQUAL_STRING("broker.local", out.mqtt_host);
    TEST_ASSERT_EQUAL_UINT16(1883, out.mqtt_port);
}

void test_decode_rejects_corruption() {
    Settings s = settingsDefaults();
    settingsSet(s, "ssid", "Home");
    SettingsBlob blob;
    settingsEncode(s, blob);
    Settings out = settingsDefaults();

    SettingsBlob bad = blob;
    bad.settings.wifi_ssid[0] = 'X';          // payload changed, CRC stale
    TEST_ASSERT_FALSE(settingsDecode(bad, out));

    bad = blob;
    bad.magic = 0;                            // erased flash
    TEST_ASSERT_FALSE(settingsDecode(bad, out));

    bad = blob;
    bad.version = SETTINGS_VERSION + 1;       // future layout
    TEST_ASSERT_FALSE(settingsDecode(bad, out));

    SettingsBlob erased;
    memset(&erased, 0xFF, sizeof(erased));    // blank EEPROM
    TEST_ASSERT_FALSE(settingsDecode(erased, out));
    TEST_ASSERT_EQUAL_STRING("", out.wifi_ssid);  // untouched
}

void test_parse_record_and_stop() {
    Command c = parseCommand("record 30");
    TEST_ASSERT_EQUAL(Command::Type::Record, c.type);
    TEST_ASSERT_EQUAL_STRING("30", c.value);
    c = parseCommand("RECORD");
    TEST_ASSERT_EQUAL(Command::Type::Record, c.type);
    TEST_ASSERT_EQUAL_STRING("", c.value);
    TEST_ASSERT_EQUAL(Command::Type::Stop, parseCommand("stop").type);
    TEST_ASSERT_EQUAL(Command::Type::Scan, parseCommand("scan").type);
}

void test_wav_header() {
    uint8_t h[WAV_HEADER_SIZE];
    wavHeaderMono(h, 8000, 8, 16000);
    TEST_ASSERT_EQUAL_MEMORY("RIFF", h, 4);
    TEST_ASSERT_EQUAL_MEMORY("WAVEfmt ", h + 8, 8);
    TEST_ASSERT_EQUAL_UINT32(36 + 16000, (uint32_t)h[4] | (uint32_t)h[5] << 8 | (uint32_t)h[6] << 16 | (uint32_t)h[7] << 24);
    TEST_ASSERT_EQUAL_UINT16(1, h[20] | h[21] << 8);     // PCM
    TEST_ASSERT_EQUAL_UINT16(1, h[22] | h[23] << 8);     // mono
    TEST_ASSERT_EQUAL_UINT32(8000, (uint32_t)h[24] | (uint32_t)h[25] << 8 | (uint32_t)h[26] << 16 | (uint32_t)h[27] << 24);
    TEST_ASSERT_EQUAL_UINT32(8000, (uint32_t)h[28] | (uint32_t)h[29] << 8);  // byte rate
    TEST_ASSERT_EQUAL_UINT16(1, h[32] | h[33] << 8);     // block align
    TEST_ASSERT_EQUAL_UINT16(8, h[34] | h[35] << 8);     // bits
    TEST_ASSERT_EQUAL_MEMORY("data", h + 36, 4);
    TEST_ASSERT_EQUAL_UINT32(16000, (uint32_t)h[40] | (uint32_t)h[41] << 8 | (uint32_t)h[42] << 16 | (uint32_t)h[43] << 24);

    wavHeaderMono(h, 8000, 16, 32000);
    TEST_ASSERT_EQUAL_UINT32(16000, (uint32_t)h[28] | (uint32_t)h[29] << 8);  // byte rate = 8000 * 2
    TEST_ASSERT_EQUAL_UINT16(2, h[32] | h[33] << 8);                          // block align
    TEST_ASSERT_EQUAL_UINT16(16, h[34] | h[35] << 8);
    TEST_ASSERT_EQUAL_UINT32(32000, (uint32_t)h[40] | (uint32_t)h[41] << 8 | (uint32_t)h[42] << 16 | (uint32_t)h[43] << 24);
}

void test_crc32_known_vector() {
    TEST_ASSERT_EQUAL_HEX32(0xCBF43926u, crc32("123456789", 9));
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_button_ignores_short_glitch);
    RUN_TEST(test_button_reports_press_and_release_after_debounce);
    RUN_TEST(test_button_handles_millis_wraparound);
    RUN_TEST(test_parse_empty_and_unknown);
    RUN_TEST(test_parse_simple_commands_case_insensitive);
    RUN_TEST(test_parse_set_keeps_spaces_in_value);
    RUN_TEST(test_parse_set_lowercases_key_not_value);
    RUN_TEST(test_parse_set_without_value_gives_empty_value);
    RUN_TEST(test_defaults);
    RUN_TEST(test_set_valid_keys);
    RUN_TEST(test_set_rejects_invalid);
    RUN_TEST(test_encode_decode_roundtrip);
    RUN_TEST(test_decode_rejects_corruption);
    RUN_TEST(test_parse_record_and_stop);
    RUN_TEST(test_wav_header);
    RUN_TEST(test_crc32_known_vector);
    return UNITY_END();
}
