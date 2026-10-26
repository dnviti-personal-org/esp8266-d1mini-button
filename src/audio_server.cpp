#include "audio_server.h"
#include "wav.h"

namespace { constexpr size_t CHUNK = 1024; }

void AudioServer::begin(AudioRecorder& rec, const String& deviceId) {
    rec_ = &rec;
    deviceId_ = deviceId;
    server_.begin();
    server_.setNoDelay(true);
}

void AudioServer::loop() {
    if (phase_ == Phase::Streaming) { pump(); return; }
    WiFiClient c = server_.accept();
    if (!c) return;
    c.setTimeout(500);
    handleRequest(c);
}

void AudioServer::handleRequest(WiFiClient& c) {
    String line = c.readStringUntil('\n');
    while (c.connected() && c.available()) {  // drain headers
        String h = c.readStringUntil('\n');
        if (h.length() <= 1) break;
    }
    bool wantWav = line.startsWith("GET /rec.wav");
    if (wantWav && rec_->active()) {
        uint8_t hdr[WAV_HEADER_SIZE];
        uint32_t data = rec_->targetBytes();
        wavHeaderMono(hdr, AUDIO_SAMPLE_RATE, AUDIO_BITS, data);
        c.print(F("HTTP/1.1 200 OK\r\nContent-Type: audio/wav\r\nConnection: close\r\nCache-Control: no-store\r\n"));
        c.printf("Content-Disposition: attachment; filename=\"rec-%s.wav\"\r\nContent-Length: %u\r\n\r\n",
                 deviceId_.c_str(), (unsigned)(WAV_HEADER_SIZE + data));
        c.write(hdr, WAV_HEADER_SIZE);
        client_ = c;
        sent_ = 0;
        phase_ = Phase::Streaming;
        return;
    }
    if (wantWav) {
        c.print(F("HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\nno recording in progress\n"));
    } else {
        c.print(F("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n"));
        c.printf("esp8266 button %s\nrecording: %s\nGET /rec.wav streams the current recording\n",
                 deviceId_.c_str(), rec_->active() ? "yes" : "no");
    }
    c.stop();
}

void AudioServer::pump() {
    if (!client_.connected()) {  // client went away: abort
        client_.stop();
        phase_ = Phase::Done;
        return;
    }
    uint8_t buf[CHUNK];
    uint32_t remaining = dataBytes() - sent_;
    // Real samples first ...
    while (remaining > 0 && rec_->available() > 0 && client_.availableForWrite() >= (int)CHUNK) {
        size_t n = rec_->read(buf, min(sizeof(buf), (size_t)remaining));
        size_t w = client_.write(buf, n);
        sent_ += w;
        remaining -= w;
        if (w < n) break;
    }
    // ... then, when the recorder has stopped, silence up to the declared length.
    if (remaining > 0 && !rec_->sampling() && rec_->available() == 0) {
        memset(buf, 0x00, sizeof(buf));  // 16-bit silence
        while (remaining > 0 && client_.availableForWrite() >= (int)CHUNK) {
            size_t w = client_.write(buf, min(sizeof(buf), (size_t)remaining));
            if (w == 0) break;
            sent_ += w;
            remaining -= w;
        }
    }
    if (remaining == 0) {
        client_.flush();
        delay(10);
        client_.stop();
        phase_ = Phase::Done;
    }
}
