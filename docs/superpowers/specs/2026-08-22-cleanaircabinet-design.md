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
- **Voeding**: gescheiden voedingen i.p.v. gedeelde breadboard PSU (die bleek 15V/9V/5V,
  geen 12V) — ESP32 op USB, fan op generieke laptopvoeding 12.25V/1A (gemeten, zakt
  onbelast/belast nauwelijks: 12.25V → 12.22V). GND's van beide voedingen verbonden.

## Bekabeling

| Signaal | Van | Naar | Opmerking |
|---|---|---|---|
| Fan 12V+ / GND | 12V bron | Fan | Rechtstreeks, niet via ESP32 |
| Fan PWM-in | ESP32 GPIO18 | Fan | LEDC output, 25kHz |
| Fan Tach-out | Fan | ESP32 GPIO19 | Open-collector, interne pull-up in ESPHome |
| ESP32 | USB | ESP32 | ESP32 en 12V-fanvoeding zijn gescheiden voedingen; GND's onderling verbonden |

GPIO25/26 (oorspronkelijk gepland) zaten fysiek onbereikbaar op de breadboard-opstelling
(board is bijna zo breed als de breadboard, alleen één pinrij is bereikbaar). Op die
bereikbare rij: **CLK, D0, D1, CMD zijn de interne SPI-flash pins (GPIO6/7/8/11) — nooit
gebruiken**, en RX/TX zijn de USB-serial pins — ook vermijden. GPIO2/15 zijn
boot-strapping pins, kunnen wel maar liever vermeden. Vrije bruikbare pins op die rij:
4, 16, 17, 5, 18, 19, 21, 22, 23 — GPIO18 (PWM) en GPIO19 (tach) gekozen.

**Bevestigd (POC breadboard test)**: 3.3V ESP32-logic stuurt de fan's PWM-ingang prima
aan, geen level-shifter nodig. On/off en variabele snelheid werken beide via HA. Tach
geeft ~5000 RPM op volle snelheid, consistent met de Arctic P8 MAX-datasheet (de
high-speed variant, i.t.t. de ~2000 RPM standaard P8).

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
