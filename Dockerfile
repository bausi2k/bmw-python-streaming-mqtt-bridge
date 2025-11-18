# Wir nutzen ein schlankes Python 3.11 Image als Basis
FROM python:3.11-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die Requirements-Datei und installiere Abhängigkeiten
# Wir machen das ZUERST, damit Docker diesen Schritt cachen kann
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den restlichen Code (main.py, lib/, etc.)
COPY . .

# Definiere den Startbefehl
# -u (unbuffered) ist wichtig, damit Logs sofort in Docker angezeigt werden
CMD ["python", "-u", "main.py"]