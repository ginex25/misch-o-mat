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

# Farben für Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${YELLOW}=== $1 ===${NC}"; }

# Desktop, Alias und Kiosk laufen als normaler Benutzer (z. B. pi), nicht als root
if [ "$(id -u)" -eq 0 ] && [ -z "${SUDO_USER:-}" ]; then
    log_error "Bitte nicht als root starten. Als Benutzer pi: ./installer.sh"
    log_error "(sudo wird nur für apt/systemd verwendet.)"
    exit 1
fi
INSTALL_USER="${SUDO_USER:-$USER}"
INSTALL_HOME="$(getent passwd "$INSTALL_USER" 2>/dev/null | cut -d: -f6)"
[ -n "$INSTALL_HOME" ] || INSTALL_HOME="$HOME"
DESKTOP_FILE="$INSTALL_HOME/Desktop/Mischomat.desktop"

fix_ownership_if_needed() {
    local path="$1"
    [ -e "$path" ] || return 0
    if [ -w "$path" ]; then
        return 0
    fi
    log_warn "Keine Schreibrechte: $path – setze Besitzer auf $INSTALL_USER"
    if [ "$(id -u)" -eq 0 ]; then
        chown "$INSTALL_USER:$INSTALL_USER" "$path"
    elif command -v sudo &>/dev/null; then
        sudo chown "$INSTALL_USER:$INSTALL_USER" "$path"
    else
        log_error "Manuell: sudo chown $INSTALL_USER:$INSTALL_USER '$path'"
        exit 1
    fi
}


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
    exit 1
fi

if ! command -v npm &> /dev/null; then
    log_error "npm nicht gefunden. Bitte Node.js/npm installieren."
    exit 1
fi

log_info "Projektverzeichnis : $PROJECT_ROOT"
log_info "Frontend           : $FRONTEND_DIR"
log_info "Backend            : $BACKEND_DIR"
log_info "start.sh           : $START_SH"
log_info "Icon               : $ICON_PATH"
log_info "Python             : $(python3 --version)"
if command -v pip3 &> /dev/null; then
    log_info "pip (system)       : $(pip3 --version)"
else
    log_info "pip (system)       : nicht im PATH (venv bringt eigenes pip)"
fi
log_info "npm                : $(npm --version)"


log_section "1/4 – dependencies install"

# Systempakete für Kiosk-Start (start.sh): curl für Health-Check, Chromium für Anzeige
if command -v apt-get &> /dev/null; then
    log_info "Installiere Systempakete (curl, Chromium) per apt – sudo erforderlich …"
    sudo apt-get update -qq
    if ! sudo apt-get install -y curl; then
        log_warn "Installation von curl fehlgeschlagen. start.sh benötigt curl zum Prüfen des Backends."
    fi
    if sudo apt-get install -y chromium; then
        log_info "Paket 'chromium' installiert (empfohlen auf aktuellem Raspberry Pi OS)."
    elif sudo apt-get install -y chromium-browser; then
        log_info "Paket 'chromium-browser' installiert (ältere Pi-Images)."
    else
        log_warn "Chromium konnte nicht per apt installiert werden. Manuell: sudo apt install chromium"
    fi
else
    log_warn "apt-get nicht gefunden (z. B. macOS) – curl/Chromium bitte selbst installieren; start.sh erwartet 'chromium' oder 'chromium-browser' im PATH."
fi

# npm install im Frontend-Verzeichnis
log_info "Führe 'npm install' in $FRONTEND_DIR aus..."
cd "$FRONTEND_DIR"
npm install
log_info "npm install erfolgreich abgeschlossen."

# python venv (nur anlegen, wenn noch nicht vorhanden oder unvollständig)
if [ -d "$VENV_DIR" ] && [ -x "$VENV_DIR/bin/python" ]; then
    log_info "Virtual Environment existiert bereits: $VENV_DIR"
else
    if [ -d "$VENV_DIR" ]; then
        log_warn "Unvollständiges venv in $VENV_DIR – wird neu erstellt."
        rm -rf "$VENV_DIR"
    fi
    log_info "Erstelle Python Virtual Environment in $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
    log_info "Virtual Environment erstellt."
fi

if [ ! -f "$BACKEND_DIR/requirements.txt" ]; then
    log_warn "requirements.txt nicht gefunden – pip install wird übersprungen."
else
    log_info "Installiere Python-Abhängigkeiten in venv..."
    "$VENV_DIR/bin/python3" -m pip install --upgrade pip
    "$VENV_DIR/bin/python3" -m pip install -r "$BACKEND_DIR/requirements.txt"
    log_info "Python-Abhängigkeiten erfolgreich installiert."
fi


# Desktop-Verknüpfung erstellen
log_section "2/4 – Desktop-Verknüpfung erstellen"

chmod +x "$START_SH"

# Desktop-Ordner anlegen (Pi: ~/Desktop)
mkdir -p "$INSTALL_HOME/Desktop"
fix_ownership_if_needed "$INSTALL_HOME/Desktop"
fix_ownership_if_needed "$DESKTOP_FILE"

USE_ICON=0
if [ -f "$ICON_PATH" ]; then
    USE_ICON=1
else
    log_warn "Icon nicht gefunden: $ICON_PATH – Verknüpfung ohne Icon-Zeile."
fi

TMP_DESKTOP="$(mktemp "${TMPDIR:-/tmp}/mischomat-desktop.XXXXXX")"
{
    echo "[Desktop Entry]"
    echo "Version=1.0"
    echo "Type=Application"
    echo "Name=Mischomat"
    echo "Comment=Mischomat starten"
    echo "Exec=${START_SH}"
    echo "Path=${SCRIPT_DIR}"
    if [ "$USE_ICON" -eq 1 ]; then
        echo "Icon=${ICON_PATH}"
    fi
    echo "Terminal=false"
    echo "Categories=Utility;"
} > "$TMP_DESKTOP"
mv -f "$TMP_DESKTOP" "$DESKTOP_FILE"
if [ "$(id -u)" -eq 0 ]; then
    chown "$INSTALL_USER:$INSTALL_USER" "$DESKTOP_FILE"
fi
chmod +x "$DESKTOP_FILE"

# Auf Raspberry Pi OS (LXDE) als vertrauenswürdig markieren
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_FILE" "metadata::trusted" true 2>/dev/null \
        && log_info "Desktop-Datei als vertrauenswürdig markiert (gio)." \
        || log_warn "gio set fehlgeschlagen – ggf. manuell als vertrauenswürdig markieren."
fi

if command -v desktop-file-validate &> /dev/null; then
    if desktop-file-validate "$DESKTOP_FILE" 2>&1; then
        log_info "Desktop-Verknüpfung validiert: $DESKTOP_FILE"
    else
        log_warn "desktop-file-validate meldete Fehler – Datei ggf. manuell prüfen."
    fi
else
    log_info "Desktop-Verknüpfung erstellt: $DESKTOP_FILE"
fi


# Shell-Alias mom → start.sh
log_section "Shell-Alias 'mom' einrichten"

MOM_MARKER="# Misch-O-Mat: mom → start.sh (von installer.sh)"
MOM_ALIAS_LINE="alias mom='${START_SH}'"

install_mom_alias_in() {
    local rc_file="$1"
    if [ -z "$rc_file" ]; then
        return 0
    fi
    fix_ownership_if_needed "$rc_file"
    if [ -f "$rc_file" ] && grep -qE '(^|[[:space:]])alias[[:space:]]+mom=' "$rc_file" 2>/dev/null; then
        log_info "Alias 'mom' bereits in $rc_file – überspringe."
        return 0
    fi
    {
        echo ""
        echo "$MOM_MARKER"
        echo "$MOM_ALIAS_LINE"
    } >> "$rc_file"
    log_info "Alias 'mom' in $rc_file eingetragen."
}

# Raspberry Pi OS: Aliase in ~/.bash_aliases (wird von ~/.bashrc geladen)
install_mom_alias_in "$INSTALL_HOME/.bash_aliases"
log_info "Nach Installation: neues Terminal oder 'source ~/.bash_aliases', dann: mom"


# Systemd Startup-Service erstellen
log_section "3/4 – Systemd Startup-Service erstellen"

# Grafik-Umgebung des installierenden Benutzers (nicht root – sonst kein Zugriff auf :0)
XAUTH_FILE="${INSTALL_HOME}/.Xauthority"
INSTALL_UID="$(id -u "$INSTALL_USER")"
XDG_RUNTIME_DIR="/run/user/${INSTALL_UID}"

sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Mischomat Kiosk Service
# Kein network-online – Backend/Chromium laufen nur auf localhost
After=graphical.target display-manager.service
Wants=display-manager.service

[Service]
Type=simple
User=${INSTALL_USER}
Group=${INSTALL_USER}
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${START_SH}
Restart=on-failure
RestartSec=5

Environment=DISPLAY=:0
Environment=XAUTHORITY=${XAUTH_FILE}
Environment=XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR}
Environment=WAYLAND_DISPLAY=wayland-0

# Kurz warten, bis Autologin-Desktop (Wayland/X11) bereit ist
ExecStartPre=/bin/sleep 10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=mischomat

[Install]
WantedBy=graphical.target
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

log_info "start.sh ist ausführbar."

log_info "Starte Mischomat jetzt..."
echo ""
exec "$START_SH"