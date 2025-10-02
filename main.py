import os
import sys
import json
import time
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import logging
import signal
import threading
import requests

# --- Lade Konfiguration aus .env-Datei ---
load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# --- Logging Konfiguration ---
# Loggt in die Datei "bmw_bridge.log" und zusätzlich in die Konsole
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bmw_bridge.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


# Fügt das geklonte Repo zum Python-Pfad hinzu
# --- LOKALEN IMPORT ERMÖGLICHEN ---
script_dir = os.path.dirname(os.path.abspath(__file__))
library_path = os.path.join(script_dir, 'lib') # NEUER PFAD
sys.path.append(library_path)
try:
    from bmw_cardata import BMWCarDataClient
except ImportError:
    logging.error(f"❌ Fehler: Konnte 'bmw_cardata.py' im Ordner '{library_path}' nicht finden.")
    logging.error("Stelle sicher, dass das Git-Repo 'bmw-cardata-streaming-poc' in diesem Verzeichnis liegt.")
    exit()

# --- Globale Konstanten aus .env laden ---
CLIENT_ID = os.getenv("CLIENT_ID")
LOCAL_MQTT_URL = os.getenv("LOCAL_MQTT_URL")
LOCAL_MQTT_PORT = int(os.getenv("LOCAL_MQTT_PORT"))
LOCAL_MQTT_USER = os.getenv("LOCAL_MQTT_USER")
LOCAL_MQTT_PASS = os.getenv("LOCAL_MQTT_PASS")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")

# Feste Konstanten
TOKEN_FILE_PATH = "bmw_tokens.json"
VEHICLE_CONFIG_PATH = "vehicle.json"
MQTT_URL = 'mqtts://customer.streaming-cardata.bmwgroup.com'
MQTT_PORT = 9000

try:
    with open("vehicle.json", "r") as f:
        VIN = json.load(f)["vin"]
except (FileNotFoundError, KeyError):
    logging.error("❌ Fehler: vehicle.json nicht gefunden oder VIN fehlt.")
    exit()

# --- Globale Objekte für Clients und Shutdown ---
shutdown_flag = threading.Event()
bmw_client_global = None
local_client_global = None

# --- Hilfs- & Callback-Funktionen ---
def on_bmw_connect():
    logging.info("✅ Erfolgreich mit dem BMW Streaming-Server verbunden!")
    logging.info("Warte auf Live-Daten... 📡")

def on_bmw_message(topic: str, data: dict):
    logging.debug(f"--- 🔴 BMW-Daten empfangen ---")
    base_topic = "home/bmw/live"
    data_points = data.get('data', {})

    if not data_points:
        logging.warning("  -> BMW-Nachricht hatte kein 'data'-Feld, überspringe.")
        return

    for metric_name, metric_data in data_points.items():
        try:
            sub_topic = metric_name.replace('.', '/')
            full_topic = f"{base_topic}/{sub_topic}"
            
            if isinstance(metric_data, (dict, list)):
                payload = json.dumps(metric_data)
            else:
                payload = str(metric_data)

            if local_client_global and local_client_global.is_connected():
                result = local_client_global.publish(full_topic, payload, retain=True)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logging.debug(f'  -> Gesendet an: {full_topic}')
                else:
                    logging.warning(f'  -> Fehler beim Senden an {full_topic}. Code: {result.rc}')
            else:
                logging.warning("Lokaler MQTT-Client nicht verbunden, kann Nachricht nicht weiterleiten.")

        except Exception as e:
            logging.error(f"Fehler bei der Verarbeitung der Nachricht für Metrik {metric_name}: {e}")

def graceful_shutdown(signum, frame):
    logging.info("Shutdown-Signal empfangen, beende...")
    shutdown_flag.set()

# --- Haupt-Logik ---
if __name__ == "__main__":
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    # --- Setup für den lokalen MQTT-Broker mit Retry-Logik ---
    local_client_global = mqtt.Client()
    local_client_global.username_pw_set(LOCAL_MQTT_USER, LOCAL_MQTT_PASS)
    
    def on_local_disconnect(client, userdata, rc):
        if rc != 0:
            logging.warning(f"Unerwartete Trennung vom lokalen MQTT-Broker. Bibliothek versucht automatische Wiederverbindung...")

    local_client_global.on_disconnect = on_local_disconnect

    connected_to_local = False
    for i in range(5):
        try:
            local_client_global.connect(LOCAL_MQTT_URL, LOCAL_MQTT_PORT, 60)
            local_client_global.loop_start()
            logging.info(f"✅ Verbunden mit dem lokalen MQTT-Broker.")
            connected_to_local = True
            break
        except Exception as e:
            logging.warning(f"Versuch {i+1}/5: Verbindung zum lokalen MQTT-Broker fehlgeschlagen: {e}. Nächster Versuch in 10 Sekunden.")
            if not shutdown_flag.is_set():
                time.sleep(10)
    
    if not connected_to_local:
        logging.error("❌ Konnte nach mehreren Versuchen keine Verbindung zum lokalen MQTT-Broker herstellen. Beende.")
        exit()

    # --- Setup für den BMW-Client ---
    logging.info("Starte BMW CarData Client...")
    bmw_client_global = BMWCarDataClient(client_id=CLIENT_ID, vin=VIN)
    bmw_client_global.set_connect_callback(on_bmw_connect)
    bmw_client_global.set_message_callback(on_bmw_message)

    logging.info("Starte Authentifizierung... Bitte den Anweisungen im Terminal folgen.")
    if bmw_client_global.authenticate():
        logging.info("✅ Authentifizierung erfolgreich!")
        
        bmw_client_global.connect_mqtt()
        
        while not shutdown_flag.is_set():
            # Die Hauptschleife wartet hier einfach auf das Shutdown-Signal
            time.sleep(1)

    else:
        logging.error("❌ Authentifizierung fehlgeschlagen.")

    # --- Aufräumen beim Beenden ---
    logging.info("Beende Skript und trenne Verbindungen...")
    if bmw_client_global:
        bmw_client_global.disconnect_mqtt()
    if local_client_global:
        local_client_global.loop_stop()
        local_client_global.disconnect()
    logging.info("Verbindungen getrennt. Auf Wiedersehen!")