#pragma once
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include "settings.h"

// Wi-Fi + MQTT state machine with Home Assistant MQTT discovery.
class NetLink {
public:
    enum class State : uint8_t { NoConfig, WifiConnecting, WifiUp, MqttConnecting, Online };

    void begin(const Settings& settings, const String& deviceId);
    void loop(uint32_t nowMs);

    State state() const { return state_; }
    const char* stateName() const;
    bool online() const { return state_ == State::Online; }
    int mqttState() { return mqtt_.state(); }
    uint32_t connectDurationMs() const { return onlineAtMs_ ? onlineAtMs_ - startedAtMs_ : 0; }

    // Returns true when the message was handed to the TCP stack.
    bool publishButton(bool pressed);
    bool publishVcc(float volts);
    void flush();              // push pending bytes before sleeping
    void disconnect();

    String topicBase() const;
    String topicState() const { return topicBase() + "/state"; }
    String topicVcc() const { return topicBase() + "/vcc"; }
    String topicAvailability() const { return topicBase() + "/availability"; }
    String topicDiscoveryButton() const;
    String topicDiscoveryVcc() const;

private:
    void startWifi();
    bool tryMqtt();
    void publishDiscovery();
    String deviceJson() const;

    const Settings* settings_ = nullptr;
    String deviceId_;
    WiFiClient tcp_;
    PubSubClient mqtt_{tcp_};
    State state_ = State::NoConfig;
    uint32_t startedAtMs_ = 0;
    uint32_t onlineAtMs_ = 0;
    uint32_t lastAttemptMs_ = 0;
    uint32_t wifiStartedMs_ = 0;
    bool fastConnectTried_ = false;
    bool lastButton_ = false;
};
