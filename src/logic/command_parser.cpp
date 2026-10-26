#include "command_parser.h"
#include <cctype>
#include <cstring>

namespace {

const char* skipSpaces(const char* p) {
    while (*p && isspace((unsigned char)*p)) ++p;
    return p;
}

// Copies the next word of p into out (lower-cased), returns pointer after it.
const char* readWord(const char* p, char* out, size_t outSize) {
    size_t n = 0;
    while (*p && !isspace((unsigned char)*p)) {
        if (n + 1 < outSize) out[n++] = (char)tolower((unsigned char)*p);
        ++p;
    }
    out[n] = 0;
    return p;
}

void copyTrimmed(const char* p, char* out, size_t outSize) {
    p = skipSpaces(p);
    size_t len = strlen(p);
    while (len > 0 && isspace((unsigned char)p[len - 1])) --len;
    if (len >= outSize) len = outSize - 1;
    memcpy(out, p, len);
    out[len] = 0;
}

}  // namespace

Command parseCommand(const char* line) {
    Command cmd;
    if (!line) return cmd;
    const char* p = skipSpaces(line);
    if (!*p) return cmd;

    char word[16];
    p = readWord(p, word, sizeof(word));

    struct Entry { const char* name; Command::Type type; };
    static const Entry table[] = {
        {"help", Command::Type::Help},     {"?", Command::Type::Help},
        {"show", Command::Type::Show},     {"status", Command::Type::Status},
        {"set", Command::Type::Set},       {"save", Command::Type::Save},
        {"reboot", Command::Type::Reboot}, {"factory", Command::Type::Factory},
        {"sleep", Command::Type::Sleep},   {"stay", Command::Type::Stay},
        {"record", Command::Type::Record}, {"stop", Command::Type::Stop},
        {"scan", Command::Type::Scan},
    };
    cmd.type = Command::Type::Unknown;
    for (const Entry& e : table) {
        if (strcmp(word, e.name) == 0) { cmd.type = e.type; break; }
    }
    if (cmd.type == Command::Type::Set) {
        p = skipSpaces(p);
        p = readWord(p, cmd.key, sizeof(cmd.key));
        copyTrimmed(p, cmd.value, sizeof(cmd.value));
        if (cmd.key[0] == 0) cmd.type = Command::Type::Unknown;
    } else if (cmd.type == Command::Type::Record) {
        copyTrimmed(p, cmd.value, sizeof(cmd.value));
    }
    return cmd;
}

const char* commandHelpText() {
    return
        "Commands:\n"
        "  help                 this text\n"
        "  show                 print settings (passwords masked)\n"
        "  status               device id, network and MQTT state, topics\n"
        "  scan                 list nearby Wi-Fi networks (2.4 GHz only)\n"
        "  set <key> <value>    change a setting (in RAM until 'save')\n"
        "     keys: ssid pass mqtt_host mqtt_port mqtt_user mqtt_pass\n"
        "           prefix ha_prefix power_mode (battery|always_on) awake_seconds\n"
        "           record_seconds (0 = no audio) mic_gain (1..64)\n"
        "     example: set ssid My Home WiFi\n"
        "  save                 write settings to flash\n"
        "  reboot               restart the board\n"
        "  factory              erase settings and restart\n"
        "  stay                 battery mode: do not deep-sleep until reboot\n"
        "  sleep                battery mode: deep-sleep now\n"
        "  record [seconds]     start an audio recording (served at http://<ip>/rec.wav)\n"
        "  stop                 stop the current recording early\n";
}
