# Clean Air Cabinet

ESP32-aangestuurde ventilatie voor een clean air cabinet voor geverfde werkstukken.
Firmware: [ESPHome](https://esphome.io/), geïntegreerd met Home Assistant via de native API.

## Hardware
- AZDelivery ESP-32 Dev Kit C V4 (ESP32-WROOM-32, board `esp32dev`)
- Arctic P8 Max, 4-pin PWM fan (12V, PWM speed control + tach RPM feedback)
- Eén 12V-voeding voedt alles: PTC-polyfuse (Bourns MF-R110) in de +12V-lijn → splitst naar
  de fan (direct 12V) en een Recom R-78B5.0-1.5 step-down → 5V naar de ESP32 `5V`-pin. Eén massa.
- USB alleen voor de eerste flash; koppel dan de buck-5V los (geen scheidingsdiode op het
  board). Daarna alles via OTA.

Zie `docs/superpowers/specs/2026-08-22-cleanaircabinet-design.md` voor het volledige ontwerp
(bekabeling, GPIO-toewijzing, aannames).

## Setup
```bash
cp secrets.yaml.example secrets.yaml
# vul wifi_ssid, wifi_password, api_encryption_key, ota_password in
esphome run cleanaircabinet.yaml   # eerste flash via USB
```

Na de eerste flash verschijnt het apparaat automatisch in Home Assistant (ESPHome integratie).

## Status
MVP: fan on/off + speed via HA, RPM readback. Temperatuur/RH/luchtkwaliteit sensoren zijn
uitgesteld: oplosmiddel-damp en verf-aerosol beschadigen de kandidaat-sensoren (RH-drift,
MOX-vergiftiging, optische vervuiling). Toevoegen kan pas met sensoren buiten de cabine en
gefilterde meetpunten — zie de design-spec.
