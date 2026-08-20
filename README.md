# MatrixPortal M4 — Weather + Powerwall Display

A CircuitPython project for the **Adafruit Matrix Portal M4** driving a **64×64 HUB-75 RGB LED matrix**. It started from the official Adafruit OpenWeatherMap example and has been extended to pull real-time energy data from a **Tesla Powerwall** via **Home Assistant**.

---

## What it displays

### Top area
- Current weather icon (from OpenWeatherMap sprite sheet)
- Current temperature (imperial or metric, auto-detected from the onboard jumper)

### Scrolling ticker (middle band)
Weather details cycle across the screen one at a time:
- Weather description (e.g. "Partly cloudy")
- Humidity percentage
- Wind speed

### Bottom panel (alternates every 5 seconds)
- **Power load** — current household consumption in watts, colour-coded:
  - Green: < 5000 W
  - Yellow: 5000–6000 W
  - Red: > 6000 W
- **Powerwall battery charge** — percentage remaining, colour-coded:
  - Blue: > 20 %
  - Yellow: 10–20 %
  - Red: ≤ 10 %

A horizontal progress bar below the value reflects the same reading.

---

## Data sources

| Source | Endpoint | Refresh |
|--------|----------|---------|
| Weather | OpenWeatherMap REST API (`/data/2.5/weather`) | Every 10 min |
| Load power | Home Assistant REST API — `sensor.tesla_power_wall_load_power` | Every 10 s |
| Battery charge | Home Assistant REST API — `sensor.croods_home_charge` | Every 60 s |

Home Assistant requests use a **long-lived access token** passed as a Bearer header.

---

## Hardware

- [Adafruit Matrix Portal M4](https://www.adafruit.com/product/4745) (SAMD51J19, 120 MHz, 192 KB RAM)
- 64×64 HUB-75 RGB LED matrix panel
- CircuitPython 9.2.7

---

## Configuration — `settings.toml`

Copy `settings.toml.example` to `settings.toml` and fill in your values. `settings.toml` is gitignored and must never be committed.

| Key | Description |
|-----|-------------|
| `CIRCUITPY_WIFI_SSID` | Wi-Fi network name |
| `CIRCUITPY_WIFI_PASSWORD` | Wi-Fi password |
| `OPENWEATHER_TOKEN` | API key from [openweathermap.org](https://openweathermap.org/api) |
| `BEARER_TOKEN` | Home Assistant long-lived access token (Settings → Profile → Long-Lived Access Tokens) |
| `AIO_USERNAME` | Adafruit IO username — **not currently used** |
| `AIO_KEY` | Adafruit IO key — **not currently used** |
| `mqtt_broker` | MQTT broker IP — **not currently used** (see note below) |
| `mqtt_user` | MQTT username — **not currently used** |
| `mqtt_password` | MQTT password — **not currently used** |

> **MQTT note**: MQTT support was explored as an alternative transport for Home Assistant data but was never completed. The keys are kept in `settings.toml.example` for reference. The `lib/adafruit_minimqtt/` library is present in the repo but is not imported by `code.py`.

---

## Home Assistant setup

The project reads two entities from the Tesla Powerwall integration:

- `sensor.tesla_power_wall_load_power` — household load in watts
- `sensor.croods_home_charge` — Powerwall state of charge in percent

Your Home Assistant instance must be reachable from the device's local network. Set the IP and port in `code.py`:

```python
DATA_SOURCE_POWER_LOAD    = "http://<HA_IP>:8123/api/states/sensor.tesla_power_wall_load_power"
DATA_SOURCE_POWER_BATTERY = "http://<HA_IP>:8123/api/states/sensor.croods_home_charge"
```

---

## Project structure

```
code.py                   Main entry point and loop
openweather_graphics.py   Display class (weather, power, battery, scrolling)
loading.bmp               Splash screen shown at boot (64×64, 24-bit BMP)
weather-icons.bmp         Weather icon sprite sheet
fonts/                    BDF bitmap fonts (Arial 12, Arial 14)
lib/                      CircuitPython libraries
settings.toml.example     Template for secrets (real file is gitignored)
power.py                  Legacy file — not imported, kept for reference
OLD/                      Original Adafruit example files before migration
```

---

## Based on

[Adafruit Matrix Portal M4 Weather Display](https://learn.adafruit.com/weather-display-matrix) by John Park, MIT License.
