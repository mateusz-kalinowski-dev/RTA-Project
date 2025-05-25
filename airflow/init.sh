#!/bin/bash
set -e

# Instalacja zależności
if [ -e "/opt/airflow/scripts/requirements.txt" ]; then
    echo "$(date +'%F %T') 📦 Instalacja zależności z requirements.txt"
    pip install --no-cache-dir -r "/opt/airflow/scripts/requirements.txt"
fi

# Sprawdzenie migracji
echo "$(date +'%F %T') 🔍 Sprawdzanie, czy baza wymaga migracji..."

# Próba sprawdzenia migracji (z obsługą błędu i timeoutu)
if MIGRATION_STATUS=$(airflow db check-migrations --migration-wait-timeout 30 2>&1); then
    echo "$MIGRATION_STATUS"
    if echo "$MIGRATION_STATUS" | grep -q "Waiting for migrations"; then
        echo "$(date +'%F %T') ⚠️  Baza danych wymaga migracji"
        airflow db migrate
    else
        echo "$(date +'%F %T') ✅ Baza danych nie wymaga migracji"
    fi
else
    echo "$(date +'%F %T') ❌ Błąd podczas sprawdzania migracji (prawdopodobnie timeout). Wymuszam migrację."
    airflow db migrate
fi

# Uruchomienie głównego procesu Airflow (np. webserver/scheduler)
exec airflow "$@"
