#!/bin/bash
# =============================================================
#  start.sh – Startet Backend (server.py) + Chromium Kiosk
#  Ablageort: /backend/scripts/start.sh
# =============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/.venv"
PYTHON="$VENV_DIR/bin/python3"
LOG_FILE="$SCRIPT_DIR/mischomat.log"

echo "[$(date)] Starte Mischomat..." | tee -a "$LOG_FILE"


# Prüfen ob venv vorhanden ist
if [ ! -f "$PYTHON" ]; then
    echo "[$(date)] FEHLER: Virtual Environment nicht gefunden: $VENV_DIR" | tee -a "$LOG_FILE"
    echo "[$(date)] Bitte zuerst install.sh ausführen." | tee -a "$LOG_FILE"
    exit 1
fi

echo "[$(date)] Python (venv): $($PYTHON --version)" | tee -a "$LOG_FILE"


# Backend starten
echo "[$(date)] Starte Backend (server.py) mit ENV=production..." | tee -a "$LOG_FILE"

ENV=production "$PYTHON" "$BACKEND_DIR/server.py" >> "$LOG_FILE" 2>&1 &
BACKEND_PID=$!
echo "[$(date)] Backend PID: $BACKEND_PID" | tee -a "$LOG_FILE"


# Warten bis Backend erreichbar ist (max. 30 Sek.)
echo "[$(date)] Warte auf Backend (http://localhost:5000)..." | tee -a "$LOG_FILE"

MAX_WAIT=30
WAITED=0
until curl -s --head http://localhost:5000 > /dev/null 2>&1; do
    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        echo "[$(date)] FEHLER: Backend nach ${MAX_WAIT}s nicht erreichbar. Abbruch." | tee -a "$LOG_FILE"
        kill "$BACKEND_PID" 2>/dev/null
        exit 1
    fi
    sleep 1
    WAITED=$((WAITED + 1))
done

echo "[$(date)] Backend ist bereit (nach ${WAITED}s). Starte Browser..." | tee -a "$LOG_FILE"


# Chromium im Kiosk-Modus starten
chromium-browser \
    --kiosk \
    --touch-events=enabled \
    --disable-features=BackForwardCache,OverscrollHistoryNavigation,ScrollAnchoring \
    --noerrdialogs \
    --disable-infobars \
    http://localhost:5000 >> "$LOG_FILE" 2>&1

echo "[$(date)] Chromium beendet. Stoppe Backend (PID $BACKEND_PID)..." | tee -a "$LOG_FILE"
kill "$BACKEND_PID" 2>/dev/null