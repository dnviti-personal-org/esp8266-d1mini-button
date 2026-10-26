#include "net_link.h"
#include "rtc_cache.h"

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
String NetLink::topicDiscoveryButton() const {
    return String(settings_->ha_prefix) + "/binary_sensor/" + deviceId_ + "/button/config";
}
String NetLink::topicDiscoveryVcc() const {
    return String(settings_->ha_prefix) + "/sensor/" + deviceId_ + "/vcc/config";
}

String NetLink::deviceJson() const {
    return String("\"dev\":{\"ids\":[\"") + deviceId_ + "\"],\"name\":\"ESP8266 Button " + deviceId_ +
           "\",\"mf\":\"dnviti\",\"mdl\":\"D1 mini CR2032 button\",\"sw\":\"" FW_VERSION "\"}";
}

void NetLink::publishDiscovery() {
    const bool battery = settings_->power_mode == POWER_BATTERY;
    String base = topicBase();
    String btn = String("{\"~\":\"") + base + "\",\"name\":\"Button\",\"uniq_id\":\"" + deviceId_ +
                 "_button\",\"stat_t\":\"~/state\",\"pl_on\":\"ON\",\"pl_off\":\"OFF\"";
    if (battery) btn += ",\"off_delay\":2";
    else btn += ",\"avty_t\":\"~/availability\"";
    btn += "," + deviceJson() + "}";
    mqtt_.publish(topicDiscoveryButton().c_str(), btn.c_str(), true);

    String vcc = String("{\"~\":\"") + base + "\",\"name\":\"Battery voltage\",\"uniq_id\":\"" + deviceId_ +
                 "_vcc\",\"stat_t\":\"~/vcc\",\"unit_of_meas\":\"V\",\"dev_cla\":\"voltage\","
                 "\"stat_cla\":\"measurement\",\"ent_cat\":\"diagnostic\",\"sug_dsp_prc\":2";
    if (!battery) vcc += ",\"avty_t\":\"~/availability\"";
    vcc += "," + deviceJson() + "}";
    mqtt_.publish(topicDiscoveryVcc().c_str(), vcc.c_str(), true);
}

bool NetLink::publishButton(bool pressed) {
    lastButton_ = pressed;
    if (!online()) return false;
    const bool retain = settings_->power_mode == POWER_ALWAYS_ON;
    return mqtt_.publish(topicState().c_str(), pressed ? "ON" : "OFF", retain);
}

bool NetLink::publishVcc(float volts) {
    if (!online()) return false;
    char buf[16];
    snprintf(buf, sizeof(buf), "%.2f", volts);
    return mqtt_.publish(topicVcc().c_str(), buf, true);
}

void NetLink::flush() {
    for (int i = 0; i < 5; ++i) { mqtt_.loop(); tcp_.flush(); delay(20); }
}

void NetLink::disconnect() {
    if (mqtt_.connected()) mqtt_.disconnect();
    delay(10);
}
