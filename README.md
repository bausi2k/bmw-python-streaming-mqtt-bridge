
# BMW CarData Streaming MQTT Bridge (v1.1)

🇬🇧 [English Version below](#english) | 🇦🇹 [Deutsche Version unten](#deutsch)

---

<a name="english"></a>
## 🇬🇧 BMW CarData Streaming MQTT Bridge

This project acts as a robust, long-running bridge service connecting the official **BMW CarData Streaming API** with your local MQTT broker. It receives real-time vehicle data (Push/Streaming) and forwards it to your home automation system (e.g., Node-RED, Home Assistant, Grafana).

It handles the entire OAuth2 authentication lifecycle, including automatic token refreshing, ensuring a maintenance-free operation.

### ✨ Features
* **Real-time Streaming:** Connects to BMW's MQTT interface via WebSockets/MQTT.
* **Robust Authentication:** Implements the OAuth2 Device Code Flow.
* **Auto-Healing:** Automatically refreshes access tokens before they expire and reconnects on network loss.
* **Watchdog:** Monitors data traffic and restarts connections if the stream stalls.
* **Dockerized:** Runs as a lightweight, isolated container using Docker Compose.
* **Dynamic Topics:** Flattens complex JSON data into clean MQTT topics (e.g., `home/bmw/live/vehicle/mileage`).

### ⚠️ Acknowledgements & Credits

**This project is built upon the foundational work of:**
👉 **[whi-tw/bmw-cardata-streaming-poc](https://github.com/whi-tw/bmw-cardata-streaming-poc)**

The core Python client logic (`lib/bmw_cardata.py`) responsible for the protocol implementation and authentication flow is taken from that repository. A huge thank you to the author for reverse-engineering the API!

---

### 🚀 Installation (Docker Compose)

#### 1. Prerequisites & Credentials

To use this bridge, you need specific credentials from the BMW Developer Portal.

* **Client ID:** You can find instructions on how to register and obtain your Client ID here:  
    [BMW CarData - Technical Registration](https://bmw-cardata.bmwgroup.com/customer/public/api-documentation/Id-Technical-registration)
* **MQTT Username:** You can find your specific MQTT Username in the Streaming documentation here:  
    [BMW CarData - Streaming Documentation](https://bmw-cardata.bmwgroup.com/customer/public/api-documentation/Id-Streaming)

#### 2. Configuration Files

Create the following files in your project directory:

**`.env`** (Configuration)
```ini
# BMW Config
# Insert the credentials obtained from the BMW Portal links above
CLIENT_ID=YOUR_BMW_CLIENT_ID
MQTT_USERNAME=YOUR_BMW_MQTT_USERNAME

# Local MQTT Broker
LOCAL_MQTT_URL=192.168.1.xxx
LOCAL_MQTT_PORT=1883
LOCAL_MQTT_USER=your_local_user
LOCAL_MQTT_PASS=your_local_password

# Logs
LOG_LEVEL=INFO
````

**`vehicle.json`** (Your car's VIN)

```json
{
  "vin": "WBA............."
}
```

**Initialize empty files** (Required for Docker mounting):

```bash
echo "{}" > bmw_tokens.json
touch bmw_bridge.log
```

#### 3\. Start the Container

```bash
docker compose up -d --build
```

#### 4\. First Run (Authentication)

1.  Check the logs immediately after starting: `docker compose logs -f`
2.  You will see a URL provided by BMW.
3.  Open the URL in your browser and log in with your BMW ID to authorize the application.
4.  The script will automatically receive the tokens, save them, and start streaming.

-----

-----

<a name="deutsch"></a>

## 🇦🇹 BMW CarData Streaming MQTT Bridge (v1.1)

Dieses Projekt dient als stabile Brücke zwischen der offiziellen **BMW CarData Streaming API** und deinem lokalen MQTT-Broker. Es empfängt Fahrzeugdaten in Echtzeit (Push/Streaming) und leitet sie an dein Smart Home System weiter (z.B. Node-RED, Home Assistant, Grafana).

Der Service kümmert sich vollautomatisch um die OAuth2-Authentifizierung und das Erneuern der Tokens, sodass ein wartungsfreier Dauerbetrieb möglich ist.

### ✨ Funktionen

  * **Echtzeit-Streaming:** Verbindet sich via WebSockets/MQTT direkt mit dem BMW-Server.
  * **Robuste Authentifizierung:** Nutzt den offiziellen OAuth2 Device Code Flow.
  * **Selbstheilung:** Erneuert Tokens automatisch im Hintergrund, bevor sie ablaufen, und verbindet sich bei Fehlern neu.
  * **Watchdog:** Überwacht den Datenfluss und startet die Verbindung neu, falls keine Daten mehr ankommen.
  * **Docker:** Läuft als isolierter Container (Docker Compose).
  * **Strukturierte Daten:** Wandelt komplexe JSON-Objekte in saubere MQTT-Topics um (z.B. `home/bmw/live/vehicle/mileage`).

### ⚠️ Danksagung & Credits

**Dieses Projekt basiert maßgeblich auf der Arbeit von:**
👉 **[whi-tw/bmw-cardata-streaming-poc](https://github.com/whi-tw/bmw-cardata-streaming-poc)**

Der Kern-Client (`lib/bmw_cardata.py`), der für die Protokoll-Implementierung und den Anmeldeprozess zuständig ist, stammt aus diesem Repository. Ein großes Dankeschön an den Autor für das Reverse-Engineering der API\!

-----

### 🚀 Installation (Docker Compose)

#### 1\. Voraussetzungen & Zugangsdaten

Um diese Brücke zu nutzen, benötigen Sie spezifische Zugangsdaten aus dem BMW Developer Portal.

  * **Client ID:** Anweisungen zur Registrierung und zum Erhalt der Client ID finden Sie hier:  
    [BMW CarData - Technische Registrierung](https://bmw-cardata.bmwgroup.com/customer/public/api-documentation/Id-Technical-registration)
  * **MQTT Username:** Ihren spezifischen MQTT-Benutzernamen finden Sie in der Streaming-Dokumentation hier:  
    [BMW CarData - Streaming Dokumentation](https://bmw-cardata.bmwgroup.com/customer/public/api-documentation/Id-Streaming)

#### 2\. Konfigurationsdateien

Erstellen Sie die folgenden Dateien in Ihrem Projektverzeichnis:

**`.env`** (Konfiguration)

```ini
# BMW Konfiguration
# Fügen Sie hier die Daten aus den oben verlinkten BMW-Portalen ein
CLIENT_ID=IHRE_BMW_CLIENT_ID
MQTT_USERNAME=IHR_BMW_MQTT_USERNAME

# Lokaler MQTT Broker
LOCAL_MQTT_URL=192.168.1.xxx
LOCAL_MQTT_PORT=1883
LOCAL_MQTT_USER=dein_lokaler_user
LOCAL_MQTT_PASS=dein_lokales_passwort

# Logs
LOG_LEVEL=INFO
```

**`vehicle.json`** (Deine Fahrgestellnummer/VIN)

```json
{
  "vin": "WBA............."
}
```

**Leere Dateien initialisieren** (Wichtig für Docker Mounts):

```bash
echo "{}" > bmw_tokens.json
touch bmw_bridge.log
```

#### 3\. Container starten

```bash
docker compose up -d --build
```

#### 4\. Erster Start (Anmeldung)

1.  Öffne sofort die Logs: `docker compose logs -f`
2.  Dort wird ein Link zur BMW-Webseite angezeigt.
3.  Öffne den Link im Browser und melde dich mit deiner BMW ID an, um den Zugriff zu genehmigen.
4.  Das Skript empfängt die Tokens automatisch, speichert sie und beginnt mit dem Streaming.

<!-- end list -->
