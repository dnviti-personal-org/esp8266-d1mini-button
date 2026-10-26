#include "serial_menu.h"
#include <ESP8266WiFi.h>
#include "config_store.h"
#include "net_link.h"

namespace {
const char* masked(const char* v) { return v[0] ? "********" : "(empty)"; }
const char* orEmpty(const char* v) { return v[0] ? v : "(empty)"; }
}

void SerialMenu::begin(const String& deviceId, const char* resetReason) {
    deviceId_ = deviceId;
    Serial.println();
    Serial.println(F("=== ESP8266 D1 mini MQTT button v" FW_VERSION " ==="));
    Serial.printf("Device id: %s   reset: %s\n", deviceId.c_str(), resetReason);
    Serial.println(F("Type 'help' for the configuration menu."));
    Serial.print(F("> "));
}

bool SerialMenu::loop() {
    bool gotInput = false;
    while (Serial.available()) {
        gotInput = true;
        char c = (char)Serial.read();
        if (c == '\r') continue;
        if (c == '\n') {
            line_[len_] = 0;
            Serial.println();
            handle(parseCommand(line_));
            len_ = 0;
            Serial.print(F("> "));
            continue;
        }
        if ((c == 8 || c == 127) && len_ > 0) { --len_; Serial.print(F("\b \b")); continue; }
        if (len_ + 1 < sizeof(line_) && c >= 32) { line_[len_++] = c; Serial.print(c); }
    }
    return gotInput;
}

void SerialMenu::handle(const Command& cmd) {
    switch (cmd.type) {
    case Command::Type::Empty:
        return;
    case Command::Type::Help:
        Serial.print(commandHelpText());
        return;
    case Command::Type::Show:
        printShow();
        return;
    case Command::Type::Status:
        printStatus();
        return;
    case Command::Type::Set: {
        SetResult r = settingsSet(settings_, cmd.key, cmd.value);
        if (r.ok) { dirty_ = true; Serial.printf("ok: %s set (type 'save' to persist)\n", cmd.key); }
        else Serial.printf("error: %s\n", r.message);
        return;
    }
    case Command::Type::Save:
        if (store_.save(settings_)) { dirty_ = false; Serial.println(F("saved. 'reboot' to apply network settings.")); }
        else Serial.println(F("error: EEPROM write failed"));
        return;
    case Command::Type::Reboot:
        Serial.println(F("rebooting..."));
        Serial.flush();
        delay(100);
        ESP.restart();
        return;
    case Command::Type::Factory:
        store_.erase();
        Serial.println(F("settings erased, rebooting..."));
        Serial.flush();
        delay(100);
        ESP.restart();
        return;
    case Command::Type::Stay:
        stayAwake_ = true;
        Serial.println(F("staying awake until reboot"));
        return;
    case Command::Type::Sleep:
        sleepNow_ = true;
        return;
    case Command::Type::Record: {
        long v = cmd.value[0] ? atol(cmd.value) : settings_.record_seconds;
        if (v <= 0 || v > 600) { Serial.println(F("error: seconds must be 1..600")); return; }
        recordSeconds_ = (uint32_t)v;
        recordRequested_ = true;
        stayAwake_ = true;
        return;
    }
    case Command::Type::Stop:
        stopRequested_ = true;
        return;
    case Command::Type::Scan: {
        Serial.println(F("scanning..."));
        int n = WiFi.scanNetworks();
        for (int i = 0; i < n; ++i)
            Serial.printf("  %-32s ch %2d  %4d dBm  %s\n", WiFi.SSID(i).c_str(), WiFi.channel(i), WiFi.RSSI(i),
                          WiFi.encryptionType(i) == ENC_TYPE_NONE ? "open" : "secured");
        if (n <= 0) Serial.println(F("  no networks found"));
        WiFi.scanDelete();
        return;
    }
    case Command::Type::Unknown:
        Serial.println(F("unknown command, type 'help'"));
        return;
    }
}

bool SerialMenu::takeRecordRequest(uint32_t& seconds) {
    if (!recordRequested_) return false;
    recordRequested_ = false;
    seconds = recordSeconds_;
    return true;
}

bool SerialMenu::takeStopRequest() {
    bool r = stopRequested_;
    stopRequested_ = false;
    return r;
}

void SerialMenu::printShow() {
    const Settings& s = settings_;
    Serial.println(F("Settings:"));
    Serial.printf("  ssid          = %s\n", orEmpty(s.wifi_ssid));
    Serial.printf("  pass          = %s\n", masked(s.wifi_pass));
    Serial.printf("  mqtt_host     = %s\n", orEmpty(s.mqtt_host));
    Serial.printf("  mqtt_port     = %u\n", s.mqtt_port);
    Serial.printf("  mqtt_user     = %s\n", orEmpty(s.mqtt_user));
    Serial.printf("  mqtt_pass     = %s\n", masked(s.mqtt_pass));
    Serial.printf("  prefix        = %s\n", s.topic_prefix);
    Serial.printf("  ha_prefix     = %s\n", s.ha_prefix);
    Serial.printf("  power_mode    = %s\n", powerModeName(s.power_mode));
    Serial.printf("  awake_seconds = %u\n", s.awake_seconds);
    Serial.printf("  record_seconds= %u\n", s.record_seconds);
    Serial.printf("  mic_gain      = %u\n", s.mic_gain);
    if (dirty_) Serial.println(F("  (unsaved changes: type 'save')"));
}

void SerialMenu::printStatus() {
    Serial.println(F("Status:"));
    Serial.printf("  device id   = %s\n", deviceId_.c_str());
    Serial.printf("  mac         = %s\n", WiFi.macAddress().c_str());
    Serial.printf("  state       = %s\n", net_.stateName());
    Serial.printf("  wifi        = %s (status %d) rssi %d dBm ip %s\n",
                  WiFi.status() == WL_CONNECTED ? "connected" : "down", (int)WiFi.status(), WiFi.RSSI(),
                  WiFi.localIP().toString().c_str());
    Serial.printf("  mqtt state  = %d (0 = connected)\n", net_.mqttState());
    Serial.printf("  connect ms  = %u\n", net_.connectDurationMs());
    Serial.printf("  state topic = %s\n", net_.topicState().c_str());
    Serial.printf("  rec topic   = %s\n", net_.topicRecording().c_str());
    Serial.printf("  audio url   = http://%s/rec.wav\n", WiFi.localIP().toString().c_str());
    Serial.printf("  discovery   = %s\n", net_.topicDiscoveryButton().c_str());
    Serial.printf("  free heap   = %u\n", ESP.getFreeHeap());
}
