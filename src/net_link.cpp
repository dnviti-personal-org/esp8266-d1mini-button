#include "net_link.h"
#include "rtc_cache.h"
#include "audio_recorder.h"

namespace {
constexpr uint32_t WIFI_RETRY_MS = 10000;
constexpr uint32_t WIFI_FAST_TIMEOUT_MS = 4000;  // fast connect (saved BSSID/channel) budget
constexpr uint32_t MQTT_RETRY_MS = 5000;
constexpr uint16_t MQTT_BUFFER = 768;
}

void NetLink::begin(const Settings& settings, const String& deviceId) {
    settings_ = &settings;
    deviceId_ = deviceId;
    startedAtMs_ = millis();
    WiFi.persistent(false);
    WiFi.setAutoReconnect(false);
    WiFi.mode(WIFI_STA);
    WiFi.hostname(String(settings.topic_prefix) + "-" + deviceId);
    mqtt_.setBufferSize(MQTT_BUFFER);
    mqtt_.setServer(settings.mqtt_host, settings.mqtt_port);
    mqtt_.setSocketTimeout(5);
    if (!settingsWifiConfigured(settings)) { state_ = State::NoConfig; return; }
    startWifi();
}

void NetLink::startWifi() {
    const Settings& s = *settings_;
    WifiCache cache;
    if (!fastConnectTried_ && rtcCacheLoad(cache) && cache.channel > 0) {
        fastConnectTried_ = true;
        WiFi.begin(s.wifi_ssid, s.wifi_pass, cache.channel, cache.bssid, true);
    } else {
        fastConnectTried_ = true;
        WiFi.begin(s.wifi_ssid, s.wifi_pass);
    }
    wifiStartedMs_ = millis();
    state_ = State::WifiConnecting;
}

void NetLink::loop(uint32_t now) {
    switch (state_) {
    case State::NoConfig:
        return;
    case State::WifiConnecting:
        if (WiFi.status() == WL_CONNECTED) {
            WifiCache cache{};
            cache.channel = WiFi.channel();
            memcpy(cache.bssid, WiFi.BSSID(), 6);
            rtcCacheSave(cache);
            state_ = settingsMqttConfigured(*settings_) ? State::MqttConnecting : State::WifiUp;
            lastAttemptMs_ = 0;
        } else if ((uint32_t)(now - wifiStartedMs_) > WIFI_FAST_TIMEOUT_MS && WiFi.status() != WL_CONNECTED
                   && rtcCacheValid()) {
            rtcCacheClear();          // stale BSSID/channel: fall back to a full scan
            WiFi.disconnect();
            WiFi.begin(settings_->wifi_ssid, settings_->wifi_pass);
            wifiStartedMs_ = now;
        } else if ((uint32_t)(now - wifiStartedMs_) > WIFI_RETRY_MS) {
            WiFi.disconnect();
            WiFi.begin(settings_->wifi_ssid, settings_->wifi_pass);
            wifiStartedMs_ = now;
        }
        return;
    case State::WifiUp:
        if (WiFi.status() != WL_CONNECTED) startWifi();
        return;
    case State::MqttConnecting:
        if (WiFi.status() != WL_CONNECTED) { startWifi(); return; }
        if (lastAttemptMs_ == 0 || (uint32_t)(now - lastAttemptMs_) > MQTT_RETRY_MS) {
            lastAttemptMs_ = now;
            if (tryMqtt()) {
                state_ = State::Online;
                onlineAtMs_ = millis();
                if (settings_->power_mode == POWER_ALWAYS_ON)
                    mqtt_.publish(topicAvailability().c_str(), "online", true);
                publishDiscovery();
                if (settings_->power_mode == POWER_ALWAYS_ON) publishButton(lastButton_);
                mqtt_.publish(topicRecordingState().c_str(), lastRecording_ ? "ON" : "OFF", true);
                if (chargingKnown_) mqtt_.publish(topicCharging().c_str(), lastCharging_ ? "ON" : "OFF", true);
            }
        }
        return;
    case State::Online:
        if (WiFi.status() != WL_CONNECTED) { mqtt_.disconnect(); startWifi(); return; }
        if (!mqtt_.loop()) { state_ = State::MqttConnecting; lastAttemptMs_ = 0; }
        return;
    }
}

bool NetLink::tryMqtt() {
    const Settings& s = *settings_;
    String clientId = String(s.topic_prefix) + "-" + deviceId_;
    const char* user = s.mqtt_user[0] ? s.mqtt_user : nullptr;
    const char* pass = s.mqtt_user[0] ? s.mqtt_pass : nullptr;
    if (s.power_mode == POWER_ALWAYS_ON) {
        String avail = topicAvailability();
        return mqtt_.connect(clientId.c_str(), user, pass, avail.c_str(), 0, true, "offline");
    }
    // Battery mode: no LWT, the device is offline by design most of the time.
    return mqtt_.connect(clientId.c_str(), user, pass);
}

const char* NetLink::stateName() const {
    switch (state_) {
    case State::NoConfig: return "no wifi config";
    case State::WifiConnecting: return "wifi connecting";
    case State::WifiUp: return "wifi up, mqtt not configured";
    case State::MqttConnecting: return "mqtt connecting";
    case State::Online: return "online";
    }
    return "?";
}

String NetLink::topicBase() const { return String(settings_->topic_prefix) + "/" + deviceId_; }
String NetLink::topicDiscovery(const char* component, const char* object) const {
    return String(settings_->ha_prefix) + "/" + component + "/" + deviceId_ + "/" + object + "/config";
}
String NetLink::topicDiscoveryButton() const { return topicDiscovery("binary_sensor", "button"); }

String NetLink::deviceJson() const {
    return String("\"dev\":{\"ids\":[\"") + deviceId_ + "\"],\"name\":\"ESP8266 Button " + deviceId_ +
           "\",\"mf\":\"dnviti\",\"mdl\":\"D1 mini audio button\",\"sw\":\"" FW_VERSION "\"}";
}

bool NetLink::publishEntity(const char* component, const char* object, const String& body) {
    const bool battery = settings_->power_mode == POWER_BATTERY;
    String json = String("{\"~\":\"") + topicBase() + "\",\"uniq_id\":\"" + deviceId_ + "_" + object + "\"," + body;
    if (!battery) json += ",\"avty_t\":\"~/availability\"";
    json += "," + deviceJson() + "}";
    return mqtt_.publish(topicDiscovery(component, object).c_str(), json.c_str(), true);
}

void NetLink::publishDiscovery() {
    const bool battery = settings_->power_mode == POWER_BATTERY;
    String btn = "\"name\":\"Button\",\"stat_t\":\"~/state\",\"pl_on\":\"ON\",\"pl_off\":\"OFF\"";
    if (battery) btn += ",\"off_delay\":2";
    publishEntity("binary_sensor", "button", btn);
    publishEntity("binary_sensor", "recording",
                  "\"name\":\"Recording\",\"stat_t\":\"~/recording_state\",\"pl_on\":\"ON\",\"pl_off\":\"OFF\","
                  "\"dev_cla\":\"running\",\"icon\":\"mdi:microphone\"");
    publishEntity("binary_sensor", "charging",
                  "\"name\":\"Charging\",\"stat_t\":\"~/charging\",\"pl_on\":\"ON\",\"pl_off\":\"OFF\","
                  "\"dev_cla\":\"battery_charging\",\"ent_cat\":\"diagnostic\"");
    publishEntity("sensor", "last_recording",
                  "\"name\":\"Last recording\",\"stat_t\":\"~/recording\",\"val_tpl\":\"{{ value_json.url }}\","
                  "\"json_attr_t\":\"~/recording\",\"icon\":\"mdi:file-music\"");
}

bool NetLink::publishButton(bool pressed) {
    lastButton_ = pressed;
    if (!online()) return false;
    const bool retain = settings_->power_mode == POWER_ALWAYS_ON;
    return mqtt_.publish(topicState().c_str(), pressed ? "ON" : "OFF", retain);
}

bool NetLink::publishRecordingState(bool recording) {
    lastRecording_ = recording;
    if (!online()) return false;
    return mqtt_.publish(topicRecordingState().c_str(), recording ? "ON" : "OFF", true);
}

bool NetLink::publishCharging(bool charging) {
    lastCharging_ = charging;
    chargingKnown_ = true;
    if (!online()) return false;
    return mqtt_.publish(topicCharging().c_str(), charging ? "ON" : "OFF", true);
}

bool NetLink::publishRecording(const String& url, uint32_t seconds, uint32_t bytes) {
    if (!online()) return false;
    String json = String("{\"url\":\"") + url + "\",\"seconds\":" + seconds + ",\"bytes\":" + bytes +
                  ",\"rate\":" + AUDIO_SAMPLE_RATE + ",\"bits\":" + AUDIO_BITS + ",\"mac\":\"" + deviceId_ + "\"}";
    return mqtt_.publish(topicRecording().c_str(), json.c_str(), false);
}

void NetLink::flush() {
    for (int i = 0; i < 5; ++i) { mqtt_.loop(); tcp_.flush(); delay(20); }
}

void NetLink::disconnect() {
    if (mqtt_.connected()) mqtt_.disconnect();
    delay(10);
}
