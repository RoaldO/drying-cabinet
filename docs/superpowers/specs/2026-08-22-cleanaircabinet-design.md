# Clean Air Cabinet — ESP32 Fan Controller Design

Datum: 2026-08-22

## Doel

Aansturing van een clean air cabinet voor geverfde werkstukken: fan aan/uit en snelheid
regelen, uitlezen/bedienen via Home Assistant. Later uit te breiden met temperatuur,
relatieve luchtvochtigheid en luchtkwaliteit sensoren (lagere prio, niet in MVP).

## Architectuur

ESPHome firmware op de ESP32, verbonden via WiFi. Home Assistant integratie via de
ESPHome native API (encrypted, auto-discovery) — geen MQTT-broker nodig.

## Hardware

- **MCU**: AZDelivery ESP-32 Dev Kit C V4 — ESP32-WROOM-32 module, 512KB RAM.
  ESPHome board type: `esp32dev`.
- **Fan**: Arctic P8 Max, 4-pin PWM (GND, 12V, PWM-in, Tach-out).
- **Voeding**: breadboard PSU, 6.5–12V in, 3.3V/5V uit.

## Bekabeling

| Signaal | Van | Naar | Opmerking |
|---|---|---|---|
| Fan 12V+ / GND | 12V bron | Fan | Rechtstreeks, niet via ESP32 |
| Fan PWM-in | ESP32 GPIO25 | Fan | LEDC output, 25kHz |
| Fan Tach-out | Fan | ESP32 GPIO26 | Open-collector, interne pull-up in ESPHome |
| ESP32 5V/GND | Breadboard PSU 5V-uitgang | ESP32 VIN/5V | |

**Aanname te verifiëren**: Arctic-fans specificeren het PWM-signaal doorgaans op 5V
logic; ESP32 GPIO's zijn 3.3V. De meeste fans triggeren nog betrouwbaar op 3.3V high,
maar dit moet bij de eerste opstart getest worden. Zo niet: level-shifter (NPN-transistor
of 74HCT-buffer) tussen GPIO25 en de fan's PWM-pin.

## Home Assistant integratie

Native API. Verwachte entities:
- `fan.cleanaircabinet` — on/off + snelheid (%)
- `sensor.cleanaircabinet_fan_speed` — RPM (afgeleid van tach-pulsen, 2 pulsen/omwenteling
  aangenomen — standaard voor de meeste PC/case fans)

WiFi-credentials, API encryption key en OTA-wachtwoord staan in `secrets.yaml`
(gitignored). Template: `secrets.yaml.example`.

## Repo structuur

```
cleanaircabinet/
  cleanaircabinet.yaml       # ESPHome config
  secrets.yaml.example       # template
  secrets.yaml                # gitignored, echte waarden
  .gitignore
  README.md
  docs/superpowers/specs/     # dit document
```

## Testen

1. Eerste flash via USB: `esphome run cleanaircabinet.yaml`.
2. Verifiëren dat het device in Home Assistant verschijnt (ESPHome discovery).
3. Fan speed control testen (0–100%).
4. Tacho-sensor testen: RPM-waarde plausibel vergelijken met Arctic P8 Max datasheet
   (typisch 200–2200 RPM range).
5. Daarna OTA-updates voor verdere iteratie.

## Buiten scope (later, lagere prio)

- Temperatuur/RH-sensor (bv. SHT31 of BME280, I2C)
- Luchtkwaliteitssensor (bv. BME680, SGP30, of PMS5003)
- Lokale fysieke bediening (knop/potmeter op de cabinet) — nu bewust MVP-only via HA

Deze worden later toegevoegd als extra ESPHome componenten in dezelfde YAML, op een
gedeelde I2C-bus, in een aparte iteratie met eigen review.
