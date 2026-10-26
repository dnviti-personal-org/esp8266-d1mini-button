# Home Assistant side

The button needs no custom component. Everything below uses built-in
integrations: **MQTT** (with discovery enabled, the default) and
**Downloader**.

## 1. Downloader

Add to `configuration.yaml` and restart:

```yaml
downloader:
  download_dir: www/recordings   # served at /local/recordings/<file>
```

(or add the "Downloader" integration from the UI with that directory).

## 2. Automations

`automations.yaml` in this folder contains two automations:

1. **Fetch recording** — triggered by the MQTT message the board publishes on
   `esp8266button/<mac>/recording` the moment it starts recording. It calls
   `downloader.download_file` with the URL in the payload. The ESP streams the
   WAV while it records, so the download lasts as long as the recording.
2. **Notify** — triggered by the `downloader_download_completed` event: it
   creates a persistent notification with a link to the file. Extend it as you
   like (send to a phone with `notify.mobile_app_*`, play it on a speaker with
   `media_player.play_media`, …).

Copy them into your `automations.yaml` (or create them in the UI with the
YAML editor). Nothing is device specific: one copy serves every button.

## 3. Entities created by discovery (per device `ESP8266 Button <mac>`)

| Entity | Topic | Notes |
|---|---|---|
| `binary_sensor.<mac>_button` | `esp8266button/<mac>/state` | `ON` on press; in battery mode HA turns it off after 2 s (`off_delay`) |
| `binary_sensor.<mac>_recording` | `esp8266button/<mac>/recording_state` | on while the microphone is live |
| `binary_sensor.<mac>_charging` | `esp8266button/<mac>/charging` | diagnostic, from the TP4056 CHRG pin |
| `sensor.<mac>_last_recording` | `esp8266button/<mac>/recording` | state = URL, attributes: seconds, bytes, rate, bits, mac |

Timing: the board announces the recording about 1.5 s after the press
(deep-sleep wake + Wi-Fi fast reconnect + MQTT); the automation must start the
download within ~1 s of the announcement (the ESP keeps 1 s of audio
pre-roll in RAM and gives up after 15 s if nobody connects).
