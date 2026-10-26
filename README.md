# ESP8266 D1 mini MQTT button

A big, battery powered push button for Home Assistant. A Wemos/LOLIN D1 mini
(ESP8266) sleeps in a 3D-printed box; pressing the key cap wakes it, it joins
Wi-Fi, publishes the press over MQTT (with Home Assistant auto-discovery) and
goes back to sleep. Every board identifies itself with its MAC address, so any
number of buttons can share one broker.

Designed for an elderly user: one Ø52 mm domed key cap, low actuation force,
nothing else to operate.

```
  press ─► RST ─► boot ─► Wi-Fi (fast reconnect) ─► MQTT ─► publish ON + battery V ─► deep sleep
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
set <key> <value>    keys: ssid pass mqtt_host mqtt_port mqtt_user mqtt_pass
                           prefix ha_prefix power_mode awake_seconds
save                 persist to flash
reboot | factory     restart / erase everything and restart
stay | sleep         battery mode: keep the menu open / deep sleep now
```

Values may contain spaces (`set ssid My Home WiFi`). After power-on or a
flash, battery mode keeps the console open for `awake_seconds` (default 60 s,
15 min while Wi-Fi/MQTT are not configured); any keystroke extends the window,
`stay` cancels the timer.

### Power modes

| `power_mode` | Behaviour |
|---|---|
| `battery` (default) | Deep sleep between presses. A press pulls RST (JP1 closed); the wake itself is the event. The firmware publishes `ON` and the supply voltage, then sleeps. No availability topic: the device is offline by design. HA turns the sensor off after 2 s (`off_delay`). |
| `always_on` | For USB power with JP1 open. GPIO5 is debounced (50 ms) and both `ON` and `OFF` edges are published, retained, with an `online`/`offline` availability topic (LWT). |

The battery path caches the access point's channel and BSSID in RTC memory,
so the reconnect skips the Wi-Fi scan and the whole press costs ≈ 2–3 s of
radio time.

### MQTT topics

`<mac>` is the lowercase station MAC without colons (for example
`cc50e3c76323`), `<prefix>` defaults to `esp8266button`.

| Topic | Payload |
|---|---|
| `<prefix>/<mac>/state` | `ON` / `OFF` |
| `<prefix>/<mac>/vcc` | supply voltage, e.g. `2.97` |
| `<prefix>/<mac>/availability` | `online` / `offline` (always_on mode only) |
| `homeassistant/binary_sensor/<mac>/button/config` | HA discovery, retained |
| `homeassistant/sensor/<mac>/vcc/config` | HA discovery, retained |

Home Assistant (with the MQTT integration and discovery enabled) creates a
device "ESP8266 Button <mac>" with a `binary_sensor` and a diagnostic voltage
sensor automatically.

## Hardware

Full details, numbers and reasoning in [`hardware/DESIGN.md`](hardware/DESIGN.md).

- D1 mini fed directly on its 3V3 pin from a **CR2032**, through a 68 Ω resistor
  into a **1.65 F supercapacitor bank** (2 × 2.7 V 3.3 F in series) that
  delivers the Wi-Fi current bursts the coin cell cannot.
- Button: 12 × 12 mm low force tactile switch to GND on D1/GPIO5, with a
  10 kΩ pull-up, 100 nF filter and jumper JP1 to RST for deep-sleep wake.
- Slide switch on the battery line. **Switch it off before plugging USB**: the
  USB regulator would otherwise push current into the lithium cell.
- Everything on a 70 × 50 mm perfboard inside an 84 × 60 × 21 mm printed box
  with a Ø52 mm domed key cap.

### Battery life, honestly

A D1 mini powered this way draws ≈ 0.2–0.3 mA in deep sleep (LDO back-feed and
CH340 leakage), roughly ten times a bare ESP module. With a 220 mAh CR2032 that
is **about 4–6 weeks**, dominated by standby, not by presses (a press costs
≈ 0.07 mAh). For a longer life use a CR123A or 2 × AAA, or replace the D1 mini
with a bare ESP-12F.

## License

MIT, see [LICENSE](LICENSE).
