#pragma once
#include <cstdint>

// Software debouncer for one active-low push button.
// Pure logic: feed it the raw pin level and the current time.
class Button {
public:
    enum class Event : uint8_t { None, Pressed, Released };

    explicit Button(uint32_t debounceMs = 50) : debounceMs_(debounceMs) {}

    // rawPressed: true when the pin reads "pressed" (LOW with pull-up).
    Event update(bool rawPressed, uint32_t nowMs);

    bool isPressed() const { return stable_; }

private:
    uint32_t debounceMs_;
    bool stable_ = false;      // debounced state
    bool candidate_ = false;   // last raw reading
    uint32_t candidateSince_ = 0;
    bool primed_ = false;
};
