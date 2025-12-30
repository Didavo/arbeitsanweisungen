FROM python:3.11-slim

# Umgebungsvariablen
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-openbsd \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies installieren
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Projektdateien kopieren
COPY . /app/

# Data-Verzeichnis erstellen
RUN mkdir -p /app/data && \
    chmod 755 /app/data

# Static Files Verzeichnis erstellen
RUN mkdir -p /app/staticfiles && \
    chmod 755 /app/staticfiles

# Media Files Verzeichnis erstellen
RUN mkdir -p /app/media && \
    chmod 755 /app/media

# Entrypoint-Script ausführbar machen
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]