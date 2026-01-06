#!/bin/bash

set -e

echo "=== Arbeitsanweisungen System Startup ==="

# Warten auf die Datenbank
echo "Warte auf PostgreSQL..."
MAX_TRIES=30
TRIES=0
while ! nc -z db 5432; do
  TRIES=$((TRIES+1))
  if [ $TRIES -eq $MAX_TRIES ]; then
    echo "FEHLER: PostgreSQL nicht erreichbar nach $MAX_TRIES Versuchen"
    exit 1
  fi
  echo "PostgreSQL ist noch nicht bereit - warte... (Versuch $TRIES/$MAX_TRIES)"
  sleep 2
done
echo "✓ PostgreSQL ist bereit!"

# Zusätzliche Wartezeit
sleep 3

# Django Check
echo "Führe Django System Check aus..."
python manage.py check

# Migrationen ausführen
echo "Führe Migrationen aus..."
python manage.py migrate --noinput
echo "✓ Migrationen abgeschlossen"


# Superuser erstellen (mit Python-Script)
echo "Prüfe Superuser..."
python -c "
from django.contrib.auth import get_user_model
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✓ Superuser erstellt: admin / admin123')
else:
    print('✓ Superuser existiert bereits')
"

echo "=== System bereit ==="
echo "Starte Gunicorn auf 0.0.0.0:8000..."

# Gunicorn starten
exec gunicorn app.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output