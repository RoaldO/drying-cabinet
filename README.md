# Clean Air Cabinet

ESP32-aangestuurde ventilatie voor een clean air cabinet voor geverfde werkstukken.
Firmware: [ESPHome](https://esphome.io/), geïntegreerd met Home Assistant via de native API.

## Hardware
- AZDelivery ESP-32 Dev Kit C V4 (ESP32-WROOM-32, board `esp32dev`)
- Arctic P8 Max, 4-pin PWM fan (12V, PWM speed control + tach RPM feedback)
- Breadboard voeding: 6.5–12V in → 3.3V/5V uit (voedt ESP32)

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
MVP: fan on/off + speed via HA, RPM readback. Temperatuur/RH/luchtkwaliteit sensoren volgen later.
