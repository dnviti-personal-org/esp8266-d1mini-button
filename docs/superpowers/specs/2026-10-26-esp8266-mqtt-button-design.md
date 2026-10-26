# ESP8266 D1 mini MQTT Button — Design

Date: 2026-10-26

## Goal

Firmware for a Wemos/LOLIN D1 mini (ESP8266) that exposes one push button to
Home Assistant over MQTT as a binary sensor. Each board identifies itself by
its Wi-Fi MAC address, so several boards can share one broker without
collisions. Wi-Fi and MQTT settings are editable from a serial menu and
persisted in flash, so a network change never requires reflashing.

## Decisions (defaults chosen for autonomy)

| Topic | Choice |
|---|---|
| Toolchain | PlatformIO, `espressif8266` platform, Arduino framework, board `d1_mini` |
| Button wiring | Button between **D1 (GPIO5)** and **GND**, internal pull-up. Pressed = LOW |
| Debounce | 50 ms, software, non-blocking |
| Status LED | Built-in LED (GPIO2, active low): blinking = not connected, steady on = MQTT connected |
| MQTT library | knolleary/PubSubClient |
| Device id | lowercase MAC without colons, e.g. `a4cf12ab34cd` |
| Topics | `<prefix>/<mac>/state` → `ON`/`OFF` (retained)<br>`<prefix>/<mac>/availability` → `online`/`offline` (retained, LWT) |
| HA discovery | `homeassistant/binary_sensor/<mac>/config` retained JSON with `unique_id`, `device` block, `availability_topic` |
| Default prefix | `esp8266button` (configurable) |
| Persistence | EEPROM emulation, fixed struct with magic + version + CRC32 |
| Serial | 115200 baud, line-based command menu |

## Architecture

```
main.cpp ─┬─ ConfigStore   (config.h/.cpp)      load/save/validate settings in EEPROM
          ├─ SerialMenu    (serial_menu.h/.cpp) parse lines, mutate ConfigStore, print status
          ├─ Button        (button.h/.cpp)      debounce, edge detection (pure logic)
          ├─ NetLink       (net_link.h/.cpp)    Wi-Fi + MQTT state machine, HA discovery
          └─ loop()        wires them together, drives status LED
```

`Button` and the command parser in `SerialMenu` are hardware-independent and
unit-tested with Unity on the `native` environment. Hardware-bound code
(`NetLink`, EEPROM I/O) is kept thin.

### ConfigStore

```c++
struct Settings {
  char wifi_ssid[33];  char wifi_pass[65];
  char mqtt_host[65];  uint16_t mqtt_port;
  char mqtt_user[33];  char mqtt_pass[65];
  char topic_prefix[33];
  char ha_prefix[33];
};
```
Stored as `{magic, version, Settings, crc32}`. On boot: load; if magic/CRC
mismatch → defaults (`mqtt_port=1883`, `topic_prefix="esp8266button"`,
`ha_prefix="homeassistant"`, everything else empty). `isWifiConfigured()` and
`isMqttConfigured()` tell the state machine whether to try.

### SerialMenu commands

```
help                      list commands
show                      print settings (passwords masked)
status                    device id, IP, Wi-Fi/MQTT state, topics
set <key> <value>         keys: ssid pass mqtt_host mqtt_port mqtt_user mqtt_pass prefix ha_prefix
save                      write to EEPROM
reboot                    restart
factory                   erase settings and restart
```
`set` edits an in-RAM copy; `save` persists. Values may contain spaces
(everything after the key is the value). Boot prints a banner with the device
id and `type 'help'`.

### NetLink state machine (non-blocking, runs every loop)

```
NO_CONFIG → WIFI_CONNECTING → WIFI_UP → MQTT_CONNECTING → ONLINE
```
- Wi-Fi: `WiFi.begin` once, poll `WiFi.status()`; on loss go back to
  WIFI_CONNECTING, retry every 10 s.
- MQTT: try `connect()` every 5 s with client id `<prefix>-<mac>`, LWT on the
  availability topic. On connect: publish `online`, HA discovery config, and
  the current button state (retained).
- `publishState(bool pressed)` is a no-op when offline; the state is re-sent on
  the next successful connect so HA converges.

### Button

`Button::update(bool rawPressed, uint32_t nowMs)` returns an event
(`None`, `Pressed`, `Released`) after a 50 ms stable period. Pure logic,
tested natively.

## Error handling

- Missing config: firmware stays in `NO_CONFIG`, serial menu fully usable, LED
  blinks fast.
- Broker unreachable: retry forever with fixed 5 s interval, serial `status`
  shows last PubSubClient `state()` code.
- Corrupt EEPROM: fall back to defaults, log on serial.

## Testing

- `pio test -e native`: Button debounce, command parsing, settings
  validation/CRC round trip (EEPROM mocked with a RAM buffer).
- `pio run -e d1_mini`: firmware builds.
- Manual: `pio device monitor`, configure via menu, observe HA auto-discovery.

## Out of scope

OTA updates, web UI, multiple buttons, TLS to the broker.
