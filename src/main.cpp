// ESP8266 D1 mini MQTT button with audio — see README.md and hardware/DESIGN.md
//
// Battery mode (default): the board deep-sleeps; a press pulls RST (JP1 closed),
// the chip boots, publishes ON, records audio from the microphone and streams it
// over HTTP to Home Assistant (which downloads it), then sleeps again.
// Always-on mode: GPIO5 is debounced continuously; a press starts a recording,
// a press during a recording stops it early.

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <user_interface.h>

#include "audio_recorder.h"
#include "audio_server.h"
#include "button.h"
#include "config_store.h"
#include "net_link.h"
#include "serial_menu.h"
#include "settings.h"
#include "wav.h"

namespace {
constexpr uint8_t PIN_BUTTON = D1;       // GPIO5, active low
constexpr uint8_t PIN_LED = LED_BUILTIN; // GPIO2, active low
constexpr uint8_t PIN_MIC_PWR = D2;      // GPIO4 -> INMP441 VDD (I2S uses GPIO12/13/14 = D6/D7/D5)
constexpr uint8_t PIN_CHRG = D0;         // GPIO16 <- TP4056 CHRG (open drain, low = charging, external 10k pull-up)
constexpr uint32_t PRESS_PUBLISH_TIMEOUT_MS = 20000;  // give up and sleep if the network is unreachable
constexpr uint32_t CLIENT_WAIT_MS = 15000;            // HA must start downloading within this time
constexpr uint32_t SLEEP_GRACE_MS = 300;              // let the TCP stack drain before sleeping

Settings settings;
ConfigStore store;
NetLink net;
SerialMenu menu(settings, store, net);
Button button(50);
AudioRecorder recorder;
AudioServer audioServer;

bool batteryMode = false;
bool pendingPress = false;   // battery mode: a press woke us and has to be published
bool woke = false;           // battery mode: woken from deep sleep (sleep right after the work)
uint32_t awakeDeadline = 0;  // battery mode: when to go back to sleep
uint32_t sleepAt = 0;        // battery mode: scheduled sleep time
uint32_t ledOffAt = 0;

enum class Rec : uint8_t { Idle, Announcing, Running };
Rec rec = Rec::Idle;
uint32_t recStartedMs = 0;
uint32_t recSeconds = 0;

String deviceId() {
    uint8_t mac[6];
    WiFi.macAddress(mac);
    char buf[13];
    snprintf(buf, sizeof(buf), "%02x%02x%02x%02x%02x%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    return String(buf);
}

const char* resetReasonName(uint32_t r) {
    switch (r) {
    case REASON_DEFAULT_RST: return "power-on";
    case REASON_WDT_RST: return "hw watchdog";
    case REASON_EXCEPTION_RST: return "exception";
    case REASON_SOFT_WDT_RST: return "sw watchdog";
    case REASON_SOFT_RESTART: return "soft restart";
    case REASON_DEEP_SLEEP_AWAKE: return "deep-sleep wake (button)";
    case REASON_EXT_SYS_RST: return "external reset (button / flash)";
    }
    return "unknown";
}

void ledBlink(uint32_t ms) {
    digitalWrite(PIN_LED, LOW);
    ledOffAt = millis() + ms;
}

void goToSleep(const char* why) {
    Serial.printf("deep sleep: %s\n", why);
    Serial.flush();
    recorder.stop();
    net.disconnect();
    digitalWrite(PIN_LED, HIGH);
    ESP.deepSleep(0, WAKE_RF_DEFAULT);  // wake only through RST
    delay(100);
}

void extendAwake(uint32_t ms) {
    uint32_t t = millis() + ms;
    if ((int32_t)(t - awakeDeadline) > 0) awakeDeadline = t;
}

bool charging() { return digitalRead(PIN_CHRG) == LOW; }

void startRecording(uint32_t seconds) {
    recSeconds = seconds;
    audioServer.reset();
    recorder.start(seconds, settings.mic_gain);
    recStartedMs = millis();
    rec = Rec::Announcing;
    digitalWrite(PIN_LED, LOW);
    Serial.printf("[audio] recording %u s, stream at http://%s/rec.wav\n", (unsigned)seconds,
                  WiFi.localIP().toString().c_str());
    if (batteryMode) extendAwake(seconds * 1000u + CLIENT_WAIT_MS + 10000u);
}

void finishRecording(const char* why) {
    recorder.stop();
    digitalWrite(PIN_LED, HIGH);
    Serial.printf("[audio] finished: %s (%u/%u bytes captured, %u ring overruns, peak %d, sent %u bytes)\n", why,
                  (unsigned)recorder.producedBytes(), (unsigned)recorder.targetBytes(), (unsigned)recorder.overruns(),
                  (int)recorder.peak(), (unsigned)audioServer.bytesSent());
    net.publishRecordingState(false);
    rec = Rec::Idle;
    if (batteryMode && woke) sleepAt = millis() + SLEEP_GRACE_MS;
}

void recordingLoop(uint32_t now) {
    recorder.loop();
    audioServer.loop();
    switch (rec) {
    case Rec::Idle:
        return;
    case Rec::Announcing:
        if (net.online()) {
            String url = String("http://") + WiFi.localIP().toString() + "/rec.wav";
            net.publishRecordingState(true);
            net.publishRecording(url, recSeconds, WAV_HEADER_SIZE + recorder.targetBytes());
            rec = Rec::Running;
        } else if ((uint32_t)(now - recStartedMs) > CLIENT_WAIT_MS && !menu.stayAwakeRequested()) {
            finishRecording("network not available");
        }
        return;
    case Rec::Running:
        if (audioServer.served()) { finishRecording("streamed"); return; }
        if (!audioServer.clientConnected() && (uint32_t)(now - recStartedMs) > CLIENT_WAIT_MS) {
            finishRecording("no client fetched the stream");
            return;
        }
        if (!recorder.sampling() && audioServer.phase() == AudioServer::Phase::Idle) {
            finishRecording("recorder done, nobody listened");
        }
        return;
    }
}
}  // namespace

void setup() {
    pinMode(PIN_LED, OUTPUT);
    digitalWrite(PIN_LED, HIGH);
    pinMode(PIN_BUTTON, INPUT_PULLUP);
    pinMode(PIN_CHRG, INPUT);  // GPIO16 has no internal pull-up: R3 on the board
    recorder.begin(PIN_MIC_PWR);

    Serial.begin(115200);
    store.begin();
    bool hadConfig = store.load(settings);

    const uint32_t reason = ESP.getResetInfoPtr()->reason;
    const String id = deviceId();
    menu.begin(id, resetReasonName(reason));
    if (!hadConfig) Serial.println(F("no valid settings in flash: using defaults. Configure with 'set ... ' then 'save'."));

    batteryMode = settings.power_mode == POWER_BATTERY;
    if (batteryMode) {
        woke = reason == REASON_DEEP_SLEEP_AWAKE;
        pendingPress = woke || reason == REASON_EXT_SYS_RST;
        if (woke) {
            awakeDeadline = millis() + PRESS_PUBLISH_TIMEOUT_MS;
            Serial.println(F("battery mode: publishing the press, then back to sleep. Type 'stay' to keep the menu."));
        } else {
            awakeDeadline = millis() + (uint32_t)settings.awake_seconds * 1000u;
            Serial.printf("battery mode: configuration window of %u s before deep sleep ('stay' to cancel).\n",
                          settings.awake_seconds);
        }
        if (!settingsWifiConfigured(settings) || !settingsMqttConfigured(settings)) {
            Serial.println(F("wifi/mqtt not configured: staying awake for configuration."));
            awakeDeadline = millis() + 15u * 60u * 1000u;
            pendingPress = false;
        }
    } else {
        Serial.println(F("always-on mode."));
    }

    net.begin(settings, id);
    net.publishCharging(charging());  // remembered, sent on connect
    audioServer.begin(recorder, id);
}

void loop() {
    const uint32_t now = millis();

    if (menu.loop() && batteryMode) extendAwake(60000);
    net.loop(now);
    recordingLoop(now);

    if (ledOffAt && (int32_t)(now - ledOffAt) >= 0 && rec == Rec::Idle) { digitalWrite(PIN_LED, HIGH); ledOffAt = 0; }

    static NetLink::State lastState = NetLink::State::NoConfig;
    if (net.state() != lastState) {
        lastState = net.state();
        Serial.printf("[net] %s", net.stateName());
        if (net.online()) Serial.printf(" after %u ms, ip %s", net.connectDurationMs(), WiFi.localIP().toString().c_str());
        Serial.println();
    }

    // console requests (work in both modes, also without network for bench tests)
    uint32_t secs;
    if (menu.takeRecordRequest(secs)) {
        if (rec != Rec::Idle) finishRecording("restarted from console");
        startRecording(secs);
    }
    if (menu.takeStopRequest() && rec != Rec::Idle) finishRecording("stopped from console");

    // charging state (always-on: on change; battery: once at connect)
    static bool lastChg = charging();
    static bool chgSent = false;
    bool chg = charging();
    if (net.online() && (!chgSent || chg != lastChg)) { net.publishCharging(chg); lastChg = chg; chgSent = true; }

    if (!batteryMode) {
        Button::Event ev = button.update(digitalRead(PIN_BUTTON) == LOW, now);
        if (ev != Button::Event::None) {
            bool pressed = ev == Button::Event::Pressed;
            bool sent = net.publishButton(pressed);
            Serial.printf("[button] %s -> %s\n", pressed ? "pressed" : "released", sent ? "published" : "offline, queued");
            if (pressed) {
                if (rec == Rec::Idle && settings.record_seconds > 0) startRecording(settings.record_seconds);
                else if (rec != Rec::Idle) finishRecording("stopped by button");
            }
            ledBlink(50);
        }
        static uint32_t lastBlink = 0;
        if (rec != Rec::Idle) { /* LED steady on while recording */ }
        else if (net.online()) { if (!ledOffAt) digitalWrite(PIN_LED, LOW); }
        else if ((uint32_t)(now - lastBlink) > 1000) { lastBlink = now; ledBlink(100); }
        return;
    }

    // ---- battery mode ----
    if (pendingPress && net.online()) {
        bool sent = net.publishButton(true);
        Serial.printf("[button] press published: %s\n", sent ? "ok" : "failed");
        pendingPress = false;
        ledBlink(50);
        if (settings.record_seconds > 0) startRecording(settings.record_seconds);
        else if (woke) sleepAt = now + SLEEP_GRACE_MS;
    }
    if (menu.stayAwakeRequested()) return;
    if (menu.sleepRequested()) { net.flush(); goToSleep("requested"); }
    if (sleepAt && (int32_t)(now - sleepAt) >= 0) { net.flush(); goToSleep("work done"); }
    if ((int32_t)(now - awakeDeadline) >= 0) {
        if (pendingPress) Serial.println(F("[button] press lost: network unreachable"));
        goToSleep("awake window elapsed");
    }
}
