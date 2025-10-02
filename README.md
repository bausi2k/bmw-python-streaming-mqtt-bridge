Ja, selbstverständlich. Wir ersetzen den Docker-Teil im `README.md` durch die Anleitung für die Einrichtung als `systemd`-Service. Das passt perfekt für den Betrieb auf einem Raspberry Pi.

Hier ist die aktualisierte `README.md`-Datei.

-----

````markdown
# BMW Python Streaming MQTT Bridge

This project acts as a stable, long-running bridge service that connects to the official BMW CarData Streaming API, authenticates, and forwards vehicle data in real-time to a local MQTT broker.

It is designed to be a robust, set-and-forget solution, perfect for running on a low-power device like a Raspberry Pi to integrate your vehicle's live data into home automation systems (like Node-RED, Home Assistant) or data logging platforms (like Grafana).

## Features

-   **Robust Authentication:** Uses the OAuth2 Device Code Flow to securely authenticate with the BMW CarData API.
-   **Automatic Token Management:** Automatically saves and refreshes access tokens to ensure long-term, uninterrupted operation.
-   **Real-time Data Streaming:** Connects directly to BMW's MQTT server to receive live data pushes from the vehicle.
-   **Local MQTT Bridge:** Re-publishes all received data to a local MQTT broker, making it easily accessible for other services on your network.
-   **Dynamic Topic Creation:** Automatically structures the data on the local broker by creating a hierarchical topic for each individual metric (e.g., `home/bmw/live/vehicle/mileage`).
-   **Fail-Safe Design:** Built to be resilient against network interruptions and includes configurable logging for easy monitoring.

## Setup

This service is designed to be run directly via Python on a host system (like a Raspberry Pi).

### 1. Prerequisites

Before you start, you need to prepare three configuration files in the root directory of the project.

**A. `.env` file:**
Create a `.env` file to store your credentials and configuration.

```ini
# Your BMW CarData Credentials & Config
CLIENT_ID=YOUR_CLIENT_ID 			# provided, when creating an application in the BMW Portal
MQTT_USERNAME=BMW_MQTT_USERNAME 	# provided in the BMW Portal, when creating a REaltime Datapoint

# Your Local MQTT Broker Details
LOCAL_MQTT_URL=192.168.1.100
LOCAL_MQTT_PORT=1883
LOCAL_MQTT_USER=your_local_username
LOCAL_MQTT_PASS=your_local_password

# Logging Level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
````

**B. `vehicle.json` file:**
Create a `vehicle.json` file containing your car's 17-character Vehicle Identification Number (VIN).

```json
{
  "vin": "YOUR_VEHICLE_VIN_HERE"
}
```

**C. `bmw_cardata.py` Client:**
This project relies on the Python client found within the `bmw-cardata-streaming-poc` repository. As per the project structure, place the `bmw_cardata.py` file in a `lib/` subdirectory.

### 2\. Installation

1.  Clone this repository to your Raspberry Pi (e.g., in `/home/pi/bmw-python-bridge`).
2.  Create a Python virtual environment:
    ```bash
    cd /path/to/your/project
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### 3\. First Run & Authentication

On the very first run, you will need to authenticate the application with your BMW account.

1.  Run the script manually from the terminal:
    ```bash
    python main.py
    ```
2.  The script will start the "Device Code Flow" and open a URL in your browser.
3.  Log in with your BMW account credentials and grant the application access.
4.  Once approved, the script will automatically obtain the necessary tokens, save them to `bmw_tokens.json`, and start the MQTT bridge. You can stop the script with `Ctrl+C` once you see it's working.

## Usage (as a systemd Service on Raspberry Pi)

To ensure the script starts automatically on boot and restarts if it crashes, we register it as a `systemd` user service.

### 1\. Create the Service File

Create a new service definition file:

```bash
nano ~/.config/systemd/user/bmw-bridge.service
```

Paste the following content into the file. **Important:** You must replace the paths for `WorkingDirectory` and `ExecStart` with the actual path to your project directory.

```ini
[Unit]
Description=BMW CarData MQTT Bridge
# Make sure the service only starts after the network is available
After=network-online.target

[Service]
Type=simple

# !!! IMPORTANT: Replace this path with the full path to your project folder !!!
WorkingDirectory=/home/pi/bmw-python-streaming-mqtt-bridge

# !!! IMPORTANT: Make sure this path to your venv's python is correct !!!
ExecStart=/home/pi/bmw-python-streaming-mqtt-bridge/venv/bin/python main.py

# Automatically restart the service if it fails
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
```

> **Tip:** To find the correct full path, navigate to your project folder and run the `pwd` command.

Save and close the file (`Ctrl+X`, then `Y`, then `Enter`).

### 2\. Enable and Start the Service

Run the following commands in order:

```bash
# Allow the service to start at boot, even if you are not logged in (crucial step!)
loginctl enable-linger $(whoami)

# Tell systemd to read the new service file
systemctl --user daemon-reload

# Enable the service to start automatically on every boot
systemctl --user enable bmw-bridge.service

# Start the service right now
systemctl --user start bmw-bridge.service
```

### 3\. Managing the Service

Here are the most common commands to manage your new background service:

  - **Check the status and see the latest logs:**
    ```bash
    systemctl --user status bmw-bridge.service
    ```
  - **Follow the live log output:**
    ```bash
    journalctl --user -u bmw-bridge.service -f
    ```
  - **Stop the service:**
    ```bash
    systemctl --user stop bmw-bridge.service
    ```
  - **Restart the service:**
    ```bash
    systemctl --user restart bmw-bridge.service
    ```

## Acknowledgements

This project would not be possible without the foundational work done on the Python client for the BMW CarData API. The core `bmw_cardata.py` client used in this project originates from the following repository:

  - **[whi-tw/bmw-cardata-streaming-poc](https://github.com/whi-tw/bmw-cardata-streaming-poc)**

A huge thank you to the author for reverse-engineering the API and providing a functional client.

```
```