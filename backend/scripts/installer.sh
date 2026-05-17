#!/bin/bash
# =============================================================
#  install.sh – Misch-O-Mat Installer
#  Ablageort:  /backend/scripts/install.sh
#  Ausführen:  immer aus /backend/scripts/ heraus
# =============================================================

set -e

# Pfade ableiten (Basis: Verzeichnis dieses Skripts)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"
ICON_PATH="$FRONTEND_DIR/public/mischomat.png"
START_SH="$SCRIPT_DIR/start.sh"
VENV_DIR="$BACKEND_DIR/.venv"
SERVICE_NAME="mischomat"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
DESKTOP_FILE="$HOME/Desktop/Mischomat.desktop"

# Farben für Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${YELLOW}=== $1 ===${NC}"; }


# Voraussetzungen prüfen
log_section "Voraussetzungen prüfen"

if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "Frontend-Verzeichnis nicht gefunden: $FRONTEND_DIR"
    exit 1
fi

if [ ! -f "$BACKEND_DIR/server.py" ]; then
    log_error "server.py nicht gefunden: $BACKEND_DIR/server.py"
    exit 1
fi

if [ ! -f "$START_SH" ]; then
    log_error "start.sh nicht gefunden: $START_SH"
    log_warn "Bitte zuerst start.sh in $SCRIPT_DIR ablegen."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    log_error "python3 nicht gefunden – bitte installieren: sudo apt install python3"
    MISSING=1
fi


log_info "Projektverzeichnis : $PROJECT_ROOT"
log_info "Frontend           : $FRONTEND_DIR"
log_info "Backend            : $BACKEND_DIR"
log_info "start.sh           : $START_SH"
log_info "Icon               : $ICON_PATH"
log_info "Python             : $(python3 --version)"
log_info "pip                : $(pip3 --version)"
log_info "npm                : $(npm --version)"



# npm install im Frontend-Verzeichnis

log_section "1/4 – dependencies install"

if ! command -v npm &> /dev/null; then
    log_error "npm nicht gefunden. Bitte Node.js/npm installieren."
    exit 1
fi

log_info "Führe 'npm install' in $FRONTEND_DIR aus..."
cd "$FRONTEND_DIR"
npm install
log_info "npm install erfolgreich abgeschlossen."

# python venv
log_info "Erstelle Python Virtual Environment in $VENV_DIR ..."
python3 -m venv "$VENV_DIR"
log_info "Virtual Environment erstellt."

if [ ! -f "$BACKEND_DIR/requirements.txt" ]; then
    log_warn "requirements.txt nicht gefunden – pip install wird übersprungen."
else
    log_info "Installiere Python-Abhängigkeiten in venv..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
    log_info "Python-Abhängigkeiten erfolgreich installiert."
fi


# Desktop-Verknüpfung erstellen
log_section "2/4 – Desktop-Verknüpfung erstellen"

# Desktop-Ordner anlegen falls nicht vorhanden
mkdir -p "$HOME/Desktop"

# Prüfe ob Icon vorhanden ist
if [ ! -f "$ICON_PATH" ]; then
    log_warn "Icon nicht gefunden: $ICON_PATH – Verknüpfung wird ohne Icon erstellt."
    ICON_PATH=""
fi

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Mischomat
Comment=Mischomat starten
Exec=$START_SH
Icon=$ICON_PATH
Terminal=false
Categories=Application;
StartupNotify=false
EOF

chmod +x "$DESKTOP_FILE"

# Auf Raspberry Pi OS (LXDE) als vertrauenswürdig markieren
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_FILE" "metadata::trusted" true 2>/dev/null \
        && log_info "Desktop-Datei als vertrauenswürdig markiert (gio)." \
        || log_warn "gio set fehlgeschlagen – ggf. manuell als vertrauenswürdig markieren."
fi

log_info "Desktop-Verknüpfung erstellt: $DESKTOP_FILE"


# Systemd Startup-Service erstellen
log_section "3/4 – Systemd Startup-Service erstellen"

# XAUTHORITY-Pfad für den aktuellen Benutzer ermitteln
XAUTH_FILE="/home/${USER}/.Xauthority"

sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Mischomat Kiosk Service
After=network-online.target graphical-session.target
Wants=network-online.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${START_SH}
Restart=on-failure
RestartSec=5

Environment=DISPLAY=:0
Environment=XAUTHORITY=${XAUTH_FILE}

ExecStartPre=/bin/sleep 5

StandardOutput=journal
StandardError=journal
SyslogIdentifier=mischomat

[Install]
WantedBy=graphical-session.target
EOF

log_info "Service-Datei geschrieben: $SERVICE_FILE"

# Systemd neu laden und Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service"
log_info "Service '${SERVICE_NAME}' aktiviert (startet automatisch beim Boot)."

# Service-Status anzeigen
sudo systemctl status "${SERVICE_NAME}.service" --no-pager -l 2>/dev/null || true

# start.sh ausführbar machen und starten
log_section "4/4 – Anwendung starten"

chmod +x "$START_SH"
log_info "start.sh ist ausführbar."

log_info "Starte Mischomat jetzt..."
echo ""
exec "$START_SH"