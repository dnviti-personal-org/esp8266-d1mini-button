#pragma once
#include <cstddef>

// Parses one line typed on the serial console into a command.
struct Command {
    enum class Type { Empty, Unknown, Help, Show, Status, Set, Save, Reboot, Factory, Sleep, Stay };
    Type type = Type::Empty;
    char key[32] = {0};     // for Set
    char value[128] = {0};  // for Set: everything after the key, trimmed
};

Command parseCommand(const char* line);
const char* commandHelpText();
