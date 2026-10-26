#pragma once
#include "settings.h"

// Loads/saves Settings in the EEPROM emulation of the ESP8266.
class ConfigStore {
public:
    void begin();
    // true when valid settings were found; otherwise defaults are loaded.
    bool load(Settings& out);
    bool save(const Settings& s);
    void erase();
};
