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
LOG_FILE="$BACKEND_DIR/logs/mischomat_start.log"

echo "[$(date)] Starte Mischomat..." | tee -a "$LOG_FILE"


# Prüfen ob venv vorhanden ist
if [ ! -f "$PYTHON" ]; then
    echo "[$(date)] FEHLER: Virtual Environment nicht gefunden: $VENV_DIR" | tee -a "$LOG_FILE"
    echo "[$(date)] Bitte zuerst install.sh ausführen." | tee -a "$LOG_FILE"
    exit 1
fi

echo "[$(date)] Python (venv): $($PYTHON --version)" | tee -a "$LOG_FILE"

BACKEND_URL="http://localhost:5000"
BACKEND_PID=""
STARTED_BACKEND=0

# Backend nur starten, wenn noch nicht erreichbar (z. B. schon von anderem Terminal / Dienst)
if curl -s --head "$BACKEND_URL" > /dev/null 2>&1; then
    echo "[$(date)] Backend läuft bereits ($BACKEND_URL). Überspringe Start, öffne nur Browser." | tee -a "$LOG_FILE"
else
    echo "[$(date)] Starte Backend (server.py) mit ENV=production..." | tee -a "$LOG_FILE"
    ENV=production "$PYTHON" "$BACKEND_DIR/server.py" >> "$LOG_FILE" 2>&1 &
    BACKEND_PID=$!
    STARTED_BACKEND=1
    echo "[$(date)] Backend PID: $BACKEND_PID" | tee -a "$LOG_FILE"

    echo "[$(date)] Warte auf Backend ($BACKEND_URL)..." | tee -a "$LOG_FILE"
    MAX_WAIT=60
    WAITED=0
    until curl -s --head "$BACKEND_URL" > /dev/null 2>&1; do
        if [ "$WAITED" -ge "$MAX_WAIT" ]; then
            echo "[$(date)] FEHLER: Backend nach ${MAX_WAIT}s nicht erreichbar. Abbruch." | tee -a "$LOG_FILE"
            kill "$BACKEND_PID" 2>/dev/null
            exit 1
        fi
        sleep 1
        WAITED=$((WAITED + 1))
    done
    echo "[$(date)] Backend ist bereit (nach ${WAITED}s)." | tee -a "$LOG_FILE"
fi

# Chromium: auf Raspberry Pi OS oft "chromium", ältere Images "chromium-browser"
if command -v chromium >/dev/null 2>&1; then
    CHROMIUM_BIN=chromium
elif command -v chromium-browser >/dev/null 2>&1; then
    CHROMIUM_BIN=chromium-browser
else
    echo "[$(date)] FEHLER: Weder 'chromium' noch 'chromium-browser' im PATH. Installieren: sudo apt install chromium" | tee -a "$LOG_FILE"
    exit 1
fi

echo "[$(date)] Starte Browser ($CHROMIUM_BIN)..." | tee -a "$LOG_FILE"

"$CHROMIUM_BIN" \
    --kiosk \
    --touch-events=enabled \
    --disable-features=BackForwardCache,OverscrollHistoryNavigation,ScrollAnchoring \
    --noerrdialogs \
    --disable-infobars \
    "$BACKEND_URL" >> "$LOG_FILE" 2>&1

if [ "$STARTED_BACKEND" -eq 1 ]; then
    echo "[$(date)] Browser beendet. Stoppe von uns gestartetes Backend (PID $BACKEND_PID)..." | tee -a "$LOG_FILE"
    kill "$BACKEND_PID" 2>/dev/null
else
    echo "[$(date)] Browser beendet. Backend lief schon vorher – kein Stop." | tee -a "$LOG_FILE"
fi