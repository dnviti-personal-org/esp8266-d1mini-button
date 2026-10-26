# ESP8266 D1 mini MQTT button

A big, battery powered push button with a microphone for Home Assistant. A
Wemos/LOLIN D1 mini (ESP8266) sleeps in a 3D-printed box; pressing the key cap
wakes it, it joins Wi-Fi, publishes the press over MQTT (with Home Assistant
auto-discovery), records a voice message from an I2S microphone and streams it
to Home Assistant, then goes back to sleep. Every board identifies itself with
its MAC address, so any number of buttons can share one broker.

Designed for an elderly user: one Ø52 mm domed key cap, low actuation force,
nothing else to operate.

```
  press ─► RST ─► boot ─► Wi-Fi (fast reconnect, ≈1.3 s) ─► MQTT: button ON + "recording" JSON
        ─► HA downloads http://<ip>/rec.wav while the ESP records (live WAV stream) ─► deep sleep
```

## Repository layout

| Path | Content |
|---|---|
| `src/` | Firmware (PlatformIO, Arduino framework) |
| `src/logic/` | Hardware independent logic: debouncer, command parser, settings + CRC |
| `test/test_logic/` | Unity tests of `src/logic`, run on the host (`pio test -e native`) |
| `hardware/DESIGN.md` | Electrical and mechanical design decisions, BOM, perfboard placement |
| `hardware/schematic/` | Schematic and perfboard layout (CADCraft: DXF, SVG, PDF, PNG) |
| `hardware/enclosure/` | 3D printable enclosure and key cap (SolidCraft: STEP, STL, renders) |
| `hardware/BOM.md` | Bill of materials and netlist |
| `homeassistant/` | Automations and setup notes for the Home Assistant side |
| `docs/superpowers/specs/` | Firmware design spec |

## Firmware

### Build, test, flash

```bash
pip install -U platformio          # or: uv tool install platformio
pio test -e native                 # host unit tests
pio run -e d1_mini                 # build
pio run -e d1_mini -t upload       # flash (auto-detects the port; or --upload-port /dev/ttyUSB0)
pio device monitor -b 115200       # serial console
```

The D1 mini uses a CH340 USB-UART. Windows 10/11 installs the driver through
Windows Update; if the board shows up without a COM port, install the CH341SER
driver from WCH. From WSL2 the board is reached with
[usbipd-win](https://github.com/dorssel/usbipd-win):

```powershell
winget install dorssel.usbipd-win
usbipd list                        # find the BUSID of "USB-SERIAL CH340"
usbipd bind --busid <BUSID>        # once, as administrator
usbipd attach --wsl --busid <BUSID>
```

### Serial configuration menu (115200 baud)

Settings live in the EEPROM emulation of the flash. Change them any time
without reflashing:

```
help                 list commands
show                 print settings (passwords masked)
status               device id, Wi-Fi/MQTT state, topics, battery voltage
scan                 list nearby 2.4 GHz networks
set <key> <value>    keys: ssid pass mqtt_host mqtt_port mqtt_user mqtt_pass
                           prefix ha_prefix power_mode awake_seconds
                           record_seconds (0 = no audio) mic_gain (1..64)
save                 persist to flash
reboot | factory     restart / erase everything and restart
stay | sleep         battery mode: keep the menu open / deep sleep now
record [seconds]     start a recording now (bench test); stop ends it early
```

Values may contain spaces (`set ssid My Home WiFi`). After power-on or a
flash, battery mode keeps the console open for `awake_seconds` (default 60 s,
15 min while Wi-Fi/MQTT are not configured); any keystroke extends the window,
`stay` cancels the timer.

### Power modes

| `power_mode` | Behaviour |
|---|---|
| `battery` (default) | Deep sleep between presses. A press pulls RST (JP1 closed); the wake itself is the event. The firmware publishes `ON`, records for `record_seconds` while streaming to HA, then sleeps. No availability topic: the device is offline by design. HA turns the button sensor off after 2 s (`off_delay`). A second press during a recording restarts the board and starts a new recording. |
| `always_on` | For USB power with JP1 open. GPIO5 is debounced (50 ms) and both `ON` and `OFF` edges are published, retained, with an `online`/`offline` availability topic (LWT). A press starts a recording, a press during a recording stops it early. |

The battery path caches the access point's channel and BSSID in RTC memory,
so the reconnect skips the Wi-Fi scan: measured wake-to-online ≈ 1.3 s.

### Audio

- INMP441 I2S MEMS microphone on the ESP8266's fixed I2S pins (SD = D6,
  SCK = D7, WS = D5), powered from D2 so it draws nothing while sleeping.
- 16 kHz I2S frames decimated to **8 kHz, 16-bit mono WAV**, digital gain
  `mic_gain` (default ×8). Up to 600 s per press (`record_seconds`, default 120).
- The ESP keeps 1 s of pre-roll in RAM and serves the file at
  `http://<ip>/rec.wav` as a fixed-length WAV **while it records**; nothing is
  written to flash. If no client connects within 15 s the recording is dropped.
- Why not the round electret capsule + the on-chip ADC: the ESP8266's single
  ADC is read through the Wi-Fi PHY (`system_adc_read`, ~100–220 µs per
  sample, code in flash). Sampling it from a timer interrupt crashed the chip
  (Exception 0 in the ISR) as soon as TCP traffic flowed, and minutes of audio
  do not fit in RAM or survive the flash erase stalls. The I2S peripheral is
  filled by DMA and touches none of that.

### MQTT topics

`<mac>` is the lowercase station MAC without colons (for example
`cc50e3c76323`), `<prefix>` defaults to `esp8266button`.

| Topic | Payload |
|---|---|
| `<prefix>/<mac>/state` | `ON` / `OFF` |
| `<prefix>/<mac>/recording_state` | `ON` while the microphone is live, retained |
| `<prefix>/<mac>/recording` | `{"url":"http://<ip>/rec.wav","seconds":120,"bytes":1920044,"rate":8000,"bits":16,"mac":"<mac>"}` |
| `<prefix>/<mac>/charging` | `ON` / `OFF` from the TP4056, retained |
| `<prefix>/<mac>/availability` | `online` / `offline` (always_on mode only) |
| `homeassistant/{binary_sensor,sensor}/<mac>/*/config` | HA discovery for button, recording, charging, last_recording (retained) |

Home Assistant (with the MQTT integration and discovery enabled) creates a
device "ESP8266 Button <mac>" with three binary sensors and a "Last recording"
sensor automatically. The automations in [`homeassistant/`](homeassistant/)
download each recording into `www/recordings/` and notify you.

## Hardware

Full details, numbers and reasoning in [`hardware/DESIGN.md`](hardware/DESIGN.md).

- **LiPo 3.7 V 1000 mAh** under the perfboard, **TP4056 USB-C charger module**
  with protection, slide switch, Schottky diode into the D1 mini's 5V pin (so
  USB programming can be plugged at any time without back-feeding the cell).
- Button: 12 × 12 mm low force tactile switch to GND on D1/GPIO5, with a
  10 kΩ pull-up, 100 nF filter and jumper JP1 to RST for deep-sleep wake.
- INMP441 microphone breakout in a pocket under the lid, 6 wires to a header
  on the board; charger CHRG pin to D0 with a 10 kΩ pull-up.
- Everything on a 70 × 50 mm perfboard inside an 84 × 60 × 28 mm printed box
  with a Ø52 mm domed key cap, a USB-C charging slot and a charge-LED window.

### Why not the CR2032 of the first revision

Minutes of recording mean the ESP8266 and its radio stay on at ≈ 75 mA for
minutes: ≈ 4 mAh per 3-minute press. A coin cell cannot source that current
and holds only ≈ 220 mAh. The 1000 mAh LiPo gives **≈ 250 three-minute
recordings per charge** and **≈ 4 months of standby** (the D1 mini's LDO and
CH340 leak ≈ 0.25 mA in deep sleep; a bare ESP-12F would sleep at 20 µA).

## License

MIT, see [LICENSE](LICENSE).
