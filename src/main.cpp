// ESP8266 D1 mini MQTT button — see README.md and hardware/DESIGN.md
//
// Battery mode (default): the board deep-sleeps; a press pulls RST (JP1 closed),
// the chip boots, publishes ON (+ battery voltage) and sleeps again.
// Always-on mode: GPIO5 is debounced continuously and ON/OFF edges are published.

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <user_interface.h>

#include "button.h"
#include "config_store.h"
#include "net_link.h"
#include "serial_menu.h"
#include "settings.h"

ADC_MODE(ADC_VCC);  // ESP.getVcc() measures the 3V3 rail; A0 must stay unconnected

namespace {
constexpr uint8_t PIN_BUTTON = D1;    // GPIO5, active low
constexpr uint8_t PIN_LED = LED_BUILTIN;  // GPIO2, active low
constexpr uint32_t PRESS_PUBLISH_TIMEOUT_MS = 20000;  // give up and sleep if the network is unreachable
constexpr uint32_t SLEEP_GRACE_MS = 300;              // let the TCP stack drain before sleeping

Settings settings;
ConfigStore store;
NetLink net;
SerialMenu menu(settings, store, net);
Button button(50);

bool batteryMode = false;
bool pendingPress = false;   // battery mode: a press woke us and has to be published
bool woke = false;           // battery mode: woken from deep sleep (sleep right after publishing)
uint32_t awakeDeadline = 0;  // battery mode: when to go back to sleep
uint32_t sleepAt = 0;        // battery mode: scheduled sleep time after a publish
uint32_t ledOffAt = 0;

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
    net.disconnect();
    digitalWrite(PIN_LED, HIGH);
    ESP.deepSleep(0, WAKE_RF_DEFAULT);  // wake only through RST
    delay(100);
}

void extendAwake(uint32_t ms) {
    uint32_t t = millis() + ms;
    if ((int32_t)(t - awakeDeadline) > 0) awakeDeadline = t;
}
}  // namespace

void setup() {
    pinMode(PIN_LED, OUTPUT);
    digitalWrite(PIN_LED, HIGH);
    pinMode(PIN_BUTTON, INPUT_PULLUP);

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
}

void loop() {
    const uint32_t now = millis();

    if (menu.loop() && batteryMode) extendAwake(60000);
    net.loop(now);

    if (ledOffAt && (int32_t)(now - ledOffAt) >= 0) { digitalWrite(PIN_LED, HIGH); ledOffAt = 0; }

    static NetLink::State lastState = NetLink::State::NoConfig;
    if (net.state() != lastState) {
        lastState = net.state();
        Serial.printf("[net] %s", net.stateName());
        if (net.online()) Serial.printf(" after %u ms, ip %s", net.connectDurationMs(), WiFi.localIP().toString().c_str());
        Serial.println();
    }

    if (!batteryMode) {
        Button::Event ev = button.update(digitalRead(PIN_BUTTON) == LOW, now);
        if (ev != Button::Event::None) {
            bool pressed = ev == Button::Event::Pressed;
            bool sent = net.publishButton(pressed);
            Serial.printf("[button] %s -> %s\n", pressed ? "pressed" : "released", sent ? "published" : "offline, queued");
            if (sent && pressed) net.publishVcc(ESP.getVcc() / 1024.0f);
            ledBlink(50);
        }
        // steady LED when online, slow blink otherwise
        static uint32_t lastBlink = 0;
        if (net.online()) { if (!ledOffAt) digitalWrite(PIN_LED, LOW); }
        else if ((uint32_t)(now - lastBlink) > 1000) { lastBlink = now; ledBlink(100); }
        return;
    }

    // ---- battery mode ----
    if (pendingPress && net.online()) {
        bool sent = net.publishButton(true);
        net.publishVcc(ESP.getVcc() / 1024.0f);
        Serial.printf("[button] press published: %s (%.2f V)\n", sent ? "ok" : "failed", ESP.getVcc() / 1024.0f);
        pendingPress = false;
        ledBlink(50);
        if (woke) sleepAt = now + SLEEP_GRACE_MS;
    }
    if (menu.stayAwakeRequested()) return;
    if (menu.sleepRequested()) { net.flush(); goToSleep("requested"); }
    if (sleepAt && (int32_t)(now - sleepAt) >= 0) { net.flush(); goToSleep("press published"); }
    if ((int32_t)(now - awakeDeadline) >= 0) {
        if (pendingPress) Serial.println(F("[button] press lost: network unreachable"));
        goToSleep("awake window elapsed");
    }
}
