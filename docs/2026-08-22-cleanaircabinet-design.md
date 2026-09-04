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
- **Voeding**: één 12V-bron voedt alles. Generieke laptopvoeding 12.25V/1A (gemeten, zakt
  onbelast/belast nauwelijks: 12.25V → 12.22V). Vanaf de brick: PTC-polyfuse in de +12V-lijn
  vóór het splitspunt (**Bourns MF-R110**: 1.1A hold / 2.2A trip, 30V, radiaal THT — soldeert
  direct op de print, herstelt na afkoelen). Daarna splitsen naar (a) de fan rechtstreeks
  op 12V en (b) een step-down naar 5V voor de ESP32. Steady-state ~0.45A (fan ~0.2A + buck-in
  ~0.25A), ruim onder de hold-stroom.
  - Step-down: **Recom R-78B5.0-1.5** (7805-pinout, gesealed, kortsluit- + thermische
    beveiliging, in 6.5–18VDC, uit 5V/1.5A). 12.25V-brick zit ruim binnen bereik. Geen
    trimpot om verkeerd te zetten. 5V-uitgang naar de ESP32 `5V`/`VIN`-pin; de onboard
    AMS1117 maakt daar 3.3V van. Meer marge nodig (andere brick later)? R-78B5.0-2.0 —
    2A én 6.5–32V in, zelfde SIP3-footprint.
  - Historie: eerdere opzet was gescheiden voedingen (ESP32 op USB, fan op 12V) omdat de
    breadboard-PSU 15V/9V/5V bleek te geven i.p.v. 12V. Sensoren zijn uitgesteld (zie
    Buiten scope), dus een gescheiden 5V-tak voor sensoren is niet meer nodig en de opzet
    gaat terug naar één voeding.
  - **USB-flashen**: het board heeft geen scheidingsdiode tussen USB-5V en de 5V-pin.
    OTA is draadloos en dus geen probleem; bij een USB-flash eerst de buck-5V loskoppelen
    zodat twee 5V-bronnen niet tegen elkaar werken.
  - Bestellen (beide bij TME, geen minimum orderbedrag):
    - R-78B5.0-1.5: <https://www.tme.eu/en/details/r-78b5.0-1.5/dc-dc-converters/recom/>
    - MF-R110: <https://www.tme.eu/en/details/mf-r110/tht-polymer-fuses/bourns/>

## Bekabeling

| Signaal | Van | Naar | Opmerking |
|---|---|---|---|
| 12V brick + | brick | MF-R110 → splitspunt | PTC-polyfuse Bourns MF-R110 in de +12V-lijn vóór het splitspunt |
| Fan 12V+ / GND | splitspunt | Fan | Rechtstreeks, niet via ESP32 |
| Buck in | splitspunt | Recom R-78B5.0-1.5 (Vin) | 12V |
| Buck uit | Recom R-78B5.0-1.5 (Vout) | ESP32 `5V`/`VIN`-pin | 5V; onboard AMS1117 maakt 3.3V |
| Fan PWM-in | ESP32 GPIO18 | Fan | LEDC output, 25kHz |
| Fan Tach-out | Fan | ESP32 GPIO19 | Open-collector, interne pull-up in ESPHome |
| GND | brick − | fan GND, buck GND, ESP32 GND | Eén gemeenschappelijke massa |

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

- Temperatuur/RH-sensor (bv. SHT4x, I2C)
- Luchtkwaliteitssensor: stofdeeltjes (PMS5003, UART — 3.3V-logic, geen level-shifter) en
  eventueel VOC/oplosmiddelen (SGP40, I2C)
- Lokale fysieke bediening (knop/potmeter op de cabinet) — nu bewust MVP-only via HA

### Waarom sensoren nog uitgesteld zijn

De cabine droogt geverfde en soms gelijmde onderdelen; de lucht bevat oplosmiddel-damp en
tijdens de beginfase verf-aerosol. Dat is een probleem voor elke voorgestelde sensor:

- **RH (SHT4x)**: polymeer-vochtsensoren driften door VOC-blootstelling. SHT4x herstelt
  grotendeels (reversibel + bake-procedure), maar aanhoudende damp degradeert 'm. Vereist
  de PTFE-membraanversie en montage buiten de directe overspray.
- **VOC (SGP40)**: geeft een adaptieve VOC-index (0–500), geen absolute waarde — het
  algoritme her-ijkt naar ~100, dus het meet veranderingen, niet "damp nog aanwezig
  ja/nee". Het MOX-element wordt bovendien permanent vergiftigd door silicoenen (mogelijk
  in lijm/kit). Operating range 0–50°C.
- **PM (PMS5003 / SPS30)**: verf-aerosol slibt de optische kamer en de interne fan dicht.
  Levensduur wordt dan een slijtdeel. Duty-cyclen via de sleep-pin en alleen ná een purge
  meten, of filteren.

Randvoorwaarde die dit oplost: elektronica en sensoren **buiten** de cabine monteren met
alleen gefilterde meetpunten naar binnen — dat dekt meteen het temp-bereik van de SGP40 en
condensatie op de PCB's. Wordt uitgewerkt in een aparte iteratie met eigen review; open
vragen: wordt de cabine verwarmd (en hoe warm), watergedragen of oplosmiddel-verf, en
silicone-houdende lijm ja/nee.

Toevoeging gebeurt als extra ESPHome componenten in dezelfde YAML: I2C-bus op GPIO21/22
(SHT4x 0x44 + SGP40 0x59), PMS5003 op UART1 (RX GPIO16, optioneel TX GPIO17). Sensoren van
de 5V-rail voeden, niet van de 3V3-pin.
