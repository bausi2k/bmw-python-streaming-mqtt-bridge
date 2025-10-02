# 1. Basis-Image: Ein schlankes, offizielles Python 3.11 Image
FROM python:3.11-slim

# 2. Arbeitsverzeichnis im Container festlegen
WORKDIR /app

# 3. Abhängigkeiten installieren (dieser Schritt wird gecached, um Builds zu beschleunigen)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Den restlichen Code der Anwendung in den Container kopieren
COPY . .

# 5. Den Port freigeben, auf dem unser Service lauscht
EXPOSE 8000

# 6. Der Befehl, der beim Starten des Containers ausgeführt wird
# Wir binden den Server an 0.0.0.0, damit er von außerhalb des Containers erreichbar ist
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]