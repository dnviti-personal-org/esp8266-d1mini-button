#pragma once
#include <Arduino.h>
#include "command_parser.h"
#include "settings.h"

class ConfigStore;
class NetLink;

// Line-oriented configuration console on Serial.
class SerialMenu {
public:
    SerialMenu(Settings& settings, ConfigStore& store, NetLink& net) : settings_(settings), store_(store), net_(net) {}

    void begin(const String& deviceId, const char* resetReason);
    // Returns true when at least one byte arrived (used to extend the awake window).
    bool loop();

    bool stayAwakeRequested() const { return stayAwake_; }
    bool sleepRequested() const { return sleepNow_; }
    void printStatus();

private:
    void handle(const Command& cmd);
    void printShow();

    Settings& settings_;
    ConfigStore& store_;
    NetLink& net_;
    String deviceId_;
    char line_[192];
    size_t len_ = 0;
    bool dirty_ = false;
    bool stayAwake_ = false;
    bool sleepNow_ = false;
};
