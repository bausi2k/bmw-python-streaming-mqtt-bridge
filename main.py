import os
import sys
import json
import time
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import logging
from logging.handlers import TimedRotatingFileHandler
import signal
import threading
import requests

# --- VERSION ---
__version__ = "1.2.1"

# --- Lade Konfiguration aus .env-Datei ---
load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# --- Logging Konfiguration mit zeitbasierter Rotation ---
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# NEU: Wir nutzen einen Unterordner für Logs
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "bmw_bridge.log")

# Rotiert das Logfile jeden Tag um Mitternacht...
# (Der Rest bleibt gleich)

# Rotiert das Logfile jeden Tag um Mitternacht und behält 7 alte Versionen
file_handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=7, encoding='utf-8')
file_handler.setFormatter(log_formatter)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# --- LOKALEN IMPORT ERMÖGLICHEN ---
script_dir = os.path.dirname(os.path.abspath(__file__))
library_path = os.path.join(script_dir, 'lib')
sys.path.append(library_path)

try:
    from bmw_cardata import BMWCarDataClient
except ImportError:
    logging.error(f"❌ Fehler: Konnte 'bmw_cardata.py' im Ordner '{library_path}' nicht finden.")
    logging.error("Stelle sicher, dass die Datei 'bmw_cardata.py' im 'lib'-Unterverzeichnis liegt.")
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
AUTH_BASE_URL = 'https://customer.bmwgroup.com'
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
last_bmw_message_timestamp = time.time()

# --- Callback-Funktionen ---
def on_bmw_connect():
    logging.info("✅ Erfolgreich mit dem BMW Streaming-Server verbunden!")
    logging.info("Warte auf Live-Daten... 📡")

def on_bmw_message(topic: str, data: dict):
    global last_bmw_message_timestamp
    last_bmw_message_timestamp = time.time()
    logging.debug(f"--- 🔴 BMW-Daten empfangen ---")
    base_topic = "home/bmw/live"
    data_points = data.get('data', {})

    if not data_points:
        logging.warning("  -> BMW-Nachricht hatte kein 'data'-Feld, überspringe.")
        return

    for metric_name, metric_data in data_points.items():
        try:
            metric_base_topic = f"{base_topic}/{metric_name.replace('.', '/')}"
            
            if isinstance(metric_data, (dict, list)):
                full_payload = json.dumps(metric_data)
                if local_client_global and local_client_global.is_connected():
                    result = local_client_global.publish(metric_base_topic, full_payload, retain=True)
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        logging.debug(f'  -> {metric_base_topic:<90} | {full_payload}')
                    else:
                        logging.warning(f'  -> Fehler beim Senden an {metric_base_topic}. Code: {result.rc}')
            
            if isinstance(metric_data, dict):
                for key, value in metric_data.items():
                    final_topic = f"{metric_base_topic}/{key}"
                    final_payload = str(value)

                    if local_client_global and local_client_global.is_connected():
                        result = local_client_global.publish(final_topic, final_payload, retain=True)
                        if result.rc == mqtt.MQTT_ERR_SUCCESS:
                            logging.debug(f'  -> {final_topic:<90} | {final_payload}')
                        else:
                            logging.warning(f'  -> Fehler beim Senden an {final_topic}. Code: {result.rc}')

        except Exception as e:
            logging.error(f"Fehler bei der Verarbeitung der Nachricht für Metrik {metric_name}: {e}")

def graceful_shutdown(signum, frame):
    logging.info("Shutdown-Signal empfangen, beende...")
    shutdown_flag.set()

# --- Hintergrund-Threads ---
def token_refresh_loop(client: BMWCarDataClient, stop_event: threading.Event):
    logging.info("Token-Refresh-Thread gestartet. Prüfung alle 15 Minuten.")
    while not stop_event.is_set():
        stop_event.wait(900) 
        if stop_event.is_set():
            break
        
        logging.info("Führe periodischen Token-Refresh-Check durch...")
        try:
            old_id_token = client.tokens.get('id_token') if client.tokens else None
            if client.authenticate():
                new_id_token = client.tokens.get('id_token') if client.tokens else None
                if old_id_token and new_id_token and old_id_token != new_id_token:
                    logging.info("Token wurde erfolgreich erneuert. Starte MQTT-Client neu, um neuen Token zu verwenden.")
                    client.disconnect_mqtt()
                    time.sleep(5)
                    client.connect_mqtt()
                else:
                    logging.info("Token-Check abgeschlossen. Token ist weiterhin gültig.")
            else:
                logging.warning("Periodischer Token-Check/Refresh ist fehlgeschlagen.")
        except Exception as e:
            logging.error(f"Fehler im Token-Refresh-Thread: {e}", exc_info=True)

def watchdog_thread(stop_event: threading.Event):
    logging.info("Watchdog-Thread gestartet. Prüfung alle 60 Minuten.")
    while not stop_event.is_set():
        stop_event.wait(3600)
        if stop_event.is_set():
            break
        
        if time.time() - last_bmw_message_timestamp > 3 * 3600:
            logging.warning("Watchdog: Seit über 3 Stunden keine Nachricht von BMW empfangen! Verbindung könnte 'stale' sein.")

# --- Haupt-Logik ---
if __name__ == "__main__":
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    # Prüfe, ob eine Token-Datei existiert
    if not os.path.exists(TOKEN_FILE_PATH):
        # ------ MODUS 1: ERSTANMELDUNG ------
        logging.info(f"Keine Token-Datei ('{TOKEN_FILE_PATH}') gefunden. Starte einmaligen Anmeldeprozess.")
        
        bmw_client = BMWCarDataClient(client_id=CLIENT_ID, vin=VIN)
        
        if bmw_client.authenticate():
            logging.info("✅ Erstanmeldung erfolgreich! Die Token-Datei wurde erstellt.")
            logging.info("Bitte starte das Skript erneut, um den normalen Service-Betrieb zu beginnen.")
        else:
            logging.error("❌ Erstanmeldung fehlgeschlagen.")
        
        exit()

    # ------ MODUS 2: NORMALER SERVICE-BETRIEB ------
    logging.info("Token-Datei gefunden. Starte den normalen Service-Betrieb.")

    # Wir nutzen explizit Version 1 (Legacy), damit der restliche Code kompatibel bleibt
    local_client_global = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
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

    bmw_client_global = BMWCarDataClient(client_id=CLIENT_ID, vin=VIN)
    bmw_client_global.set_connect_callback(on_bmw_connect)
    bmw_client_global.set_message_callback(on_bmw_message)

    if bmw_client_global.authenticate():
        logging.info("✅ Authentifizierung mit bestehenden Tokens erfolgreich!")
        
        shutdown_event_refresh = threading.Event()
        refresh_thread = threading.Thread(target=token_refresh_loop, args=(bmw_client_global, shutdown_event_refresh))
        refresh_thread.start()

        shutdown_event_watchdog = threading.Event()
        watchdog = threading.Thread(target=watchdog_thread, args=(shutdown_event_watchdog,))
        watchdog.start()

        bmw_client_global.connect_mqtt()
        
        shutdown_flag.wait()

        shutdown_event_refresh.set()
        shutdown_event_watchdog.set()
        refresh_thread.join()
        watchdog.join()

    else:
        logging.error("❌ Authentifizierung mit bestehenden Tokens fehlgeschlagen. Token-Datei könnte korrupt sein.")
        logging.error(f"Versuche, '{TOKEN_FILE_PATH}' zu löschen und das Skript neu zu starten.")

    logging.info("Beende Skript und trenne Verbindungen...")
    if bmw_client_global:
        bmw_client_global.disconnect_mqtt()
    if local_client_global:
        local_client_global.loop_stop()
        local_client_global.disconnect()
    logging.info("Verbindungen getrennt. Auf Wiedersehen!")