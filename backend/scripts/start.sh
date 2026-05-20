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

# XDG_RUNTIME_DIR / Wayland für Pi OS Bookworm+ (labwc) – oft nicht gesetzt bei systemd/SSH
setup_graphics_env() {
    local uid
    uid="$(id -u)"
    if [ -z "${XDG_RUNTIME_DIR:-}" ] && [ -d "/run/user/${uid}" ]; then
        export XDG_RUNTIME_DIR="/run/user/${uid}"
    fi
    if [ -z "${WAYLAND_DISPLAY:-}" ] && [ -n "${XDG_RUNTIME_DIR:-}" ]; then
        local sock
        for sock in "${XDG_RUNTIME_DIR}"/wayland-*; do
            if [ -S "$sock" ]; then
                export WAYLAND_DISPLAY="${sock##*/}"
                break
            fi
        done
    fi
    if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
        export DISPLAY=:0
    fi
}

# Grafik verfügbar? (SSH ohne Session / Headless → kein Chromium)
has_display() {
    setup_graphics_env
    if [ -n "${WAYLAND_DISPLAY:-}" ] && [ -n "${XDG_RUNTIME_DIR:-}" ] \
        && [ -S "${XDG_RUNTIME_DIR}/${WAYLAND_DISPLAY}" ]; then
        return 0
    fi
    if [ -n "${DISPLAY:-}" ]; then
        if command -v xdpyinfo >/dev/null 2>&1; then
            xdpyinfo -display "$DISPLAY" >/dev/null 2>&1 && return 0
        else
            return 0
        fi
    fi
    return 1
}

# Chromium-Flags je nach Wayland (Pi OS Bookworm+) oder X11
chromium_graphics_flags() {
    setup_graphics_env
    if [ -n "${WAYLAND_DISPLAY:-}" ] && [ -S "${XDG_RUNTIME_DIR:-/nonexistent}/${WAYLAND_DISPLAY}" ]; then
        echo --ozone-platform=wayland --start-maximized
    else
        echo --ozone-platform=x11 --use-gl=egl
    fi
}

BACKEND_URL="http://localhost:5000"
BACKEND_PID=""
STARTED_BACKEND=0

# Backend nur starten, wenn noch nicht erreichbar (z. B. schon von anderem Terminal / Dienst)
if curl -s --head "$BACKEND_URL" > /dev/null 2>&1; then
    echo "[$(date)] Backend läuft bereits ($BACKEND_URL). Überspringe Start, öffne nur Browser." | tee -a "$LOG_FILE"
else
    echo "[$(date)] Starte Backend (server.py) mit ENV=production..." | tee -a "$LOG_FILE"
    (cd "$BACKEND_DIR" && ENV=production "$PYTHON" server.py) >> "$LOG_FILE" 2>&1 &
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

if ! has_display; then
    echo "[$(date)] Kein grafisches Display (z. B. SSH ohne X11, DISPLAY nicht gesetzt)." | tee -a "$LOG_FILE"
    echo "[$(date)] Browser wird übersprungen – Backend läuft weiter unter $BACKEND_URL" | tee -a "$LOG_FILE"
    echo "[$(date)] UI am Pi: start.sh am Desktop/Kiosk ausführen oder systemctl start mischomat." | tee -a "$LOG_FILE"
    exit 0
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

GRAPHICS_FLAGS=($(chromium_graphics_flags))
echo "[$(date)] Starte Browser ($CHROMIUM_BIN, ${GRAPHICS_FLAGS[*]})..." | tee -a "$LOG_FILE"

"$CHROMIUM_BIN" \
    --kiosk \
    --touch-events=enabled \
    --no-first-run \
    --password-store=basic \
    --check-for-update-interval=31536000 \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --disable-features=BackForwardCache,OverscrollHistoryNavigation,ScrollAnchoring,Translate \
    --noerrdialogs \
    --disable-infobars \
    "${GRAPHICS_FLAGS[@]}" \
    "$BACKEND_URL" >> "$LOG_FILE" 2>&1

if [ "$STARTED_BACKEND" -eq 1 ]; then
    echo "[$(date)] Browser beendet. Stoppe von uns gestartetes Backend (PID $BACKEND_PID)..." | tee -a "$LOG_FILE"
    kill "$BACKEND_PID" 2>/dev/null
else
    echo "[$(date)] Browser beendet. Backend lief schon vorher – kein Stop." | tee -a "$LOG_FILE"
fi