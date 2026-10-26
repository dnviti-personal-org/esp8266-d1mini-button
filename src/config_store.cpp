#include "config_store.h"
#include <EEPROM.h>

namespace { constexpr size_t EEPROM_SIZE = 512; }

void ConfigStore::begin() { EEPROM.begin(EEPROM_SIZE); }

bool ConfigStore::load(Settings& out) {
    SettingsBlob blob;
    EEPROM.get(0, blob);
    if (settingsDecode(blob, out)) return true;
    out = settingsDefaults();
    return false;
}

bool ConfigStore::save(const Settings& s) {
    SettingsBlob blob;
    settingsEncode(s, blob);
    EEPROM.put(0, blob);
    return EEPROM.commit();
}

void ConfigStore::erase() {
    for (size_t i = 0; i < sizeof(SettingsBlob); ++i) EEPROM.write(i, 0xFF);
    EEPROM.commit();
}
