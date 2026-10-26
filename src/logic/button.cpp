#include "button.h"

Button::Event Button::update(bool rawPressed, uint32_t nowMs) {
    if (!primed_) {
        primed_ = true;
        stable_ = candidate_ = rawPressed;
        candidateSince_ = nowMs;
        return Event::None;
    }
    if (rawPressed != candidate_) {
        candidate_ = rawPressed;
        candidateSince_ = nowMs;
        return Event::None;
    }
    if (candidate_ != stable_ && (uint32_t)(nowMs - candidateSince_) >= debounceMs_) {
        stable_ = candidate_;
        return stable_ ? Event::Pressed : Event::Released;
    }
    return Event::None;
}
