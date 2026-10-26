#pragma once
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include "audio_recorder.h"

// Minimal HTTP server: GET /rec.wav streams the recording as it is captured
// (fixed-length WAV, padded with silence if the recorder stops early).
class AudioServer {
public:
    enum class Phase : uint8_t { Idle, Streaming, Done };

    void begin(AudioRecorder& rec, const String& deviceId);
    void loop();
    void reset() { phase_ = Phase::Idle; sent_ = 0; }  // call when a new recording starts

    Phase phase() const { return phase_; }
    uint32_t bytesSent() const { return sent_; }
    uint32_t dataBytes() const { return rec_ ? rec_->targetBytes() : 0; }
    bool clientConnected() const { return phase_ == Phase::Streaming; }
    bool served() const { return phase_ == Phase::Done; }

private:
    void handleRequest(WiFiClient& c);
    void pump();

    WiFiServer server_{80};
    WiFiClient client_;
    AudioRecorder* rec_ = nullptr;
    String deviceId_;
    Phase phase_ = Phase::Idle;
    uint32_t sent_ = 0;
};
