#!/bin/bash

# Funktion zur Anzeige von Nachrichten
function echo_msg() {
    echo -e "\n\033[1;32m$1\033[0m"
}

# Installiere erforderliche Systempakete
function install_system_requirements() {
    echo_msg "Überprüfe, ob python3.11-venv installiert ist..."
    if ! dpkg -l | grep -q python3.11-venv; then
        echo_msg "Installiere python3.11-venv..."
        sudo apt update
        sudo apt install -y python3.11-venv
    else
        echo_msg "python3.11-venv ist bereits installiert."
    fi
}

# Installiere ffmpeg
function install_ffmpeg() {
    echo_msg "Überprüfe, ob ffmpeg installiert ist..."
    if ! command -v ffmpeg &> /dev/null; then
        echo_msg "Installiere ffmpeg..."
        sudo apt update
        sudo apt install -y ffmpeg
    else
        echo_msg "ffmpeg ist bereits installiert."
    fi
}

# Installiere screen
function install_screen() {
    echo_msg "Überprüfe, ob screen installiert ist..."
    if ! command -v screen &> /dev/null; then
        echo_msg "Installiere screen..."
        sudo apt update
        sudo apt install -y screen
    else
        echo_msg "screen ist bereits installiert."
    fi
}

# Installiere die erforderlichen Python-Pakete
function install_python_requirements() {
    echo_msg "Installiere erforderliche Python-Pakete..."
    pip install discord.py yt-dlp spotipy python-dotenv PyNaCl  # Füge PyNaCl hinzu
}

# Erstelle die .env-Datei
function create_env_file() {
    echo_msg "Erstelle .env-Datei im Installationsverzeichnis..."

    read -p "Gib deinen Discord-Token ein: " DISCORD_TOKEN
    read -p "Gib deine Spotify Client ID ein: " SPOTIFY_CLIENT_ID
    read -p "Gib dein Spotify Client Secret ein: " SPOTIFY_CLIENT_SECRET

    {
        echo "DISCORD_TOKEN=$DISCORD_TOKEN"
        echo "SPOTIFY_CLIENT_ID=$SPOTIFY_CLIENT_ID"
        echo "SPOTIFY_CLIENT_SECRET=$SPOTIFY_CLIENT_SECRET"
    } > "$INSTALL_DIR/.env"  # Erstelle die .env-Datei im Installationsverzeichnis

    echo_msg ".env-Datei wurde erstellt."
}

# Richte Auto-Start für Linux ein
function setup_autostart() {
    echo_msg "Richte Auto-Start für Linux ein..."

    AUTOSTART_DIR="$HOME/.config/autostart"
    mkdir -p "$AUTOSTART_DIR"

    AUTOSTART_FILE="$AUTOSTART_DIR/discord_bot.desktop"
    {
        echo "[Desktop Entry]"
        echo "Type=Application"
        echo "Exec=python3 $INSTALL_DIR/bot.py"  # Passe den Skriptnamen an
        echo "Hidden=false"
        echo "NoDisplay=false"
        echo "X-GNOME-Autostart-enabled=true"
        echo "Name=DiscordBot"
    } > "$AUTOSTART_FILE"

    echo_msg "Auto-Start wurde eingerichtet."
}

# Lade die start.sh-Datei von GitHub herunter und gebe die Ausführungsrechte
function download_start_script() {
    echo_msg "Lade start.sh von GitHub herunter..."
    curl -o "$INSTALL_DIR/start.sh" https://raw.githubusercontent.com/csgamingtv2024/Discord_Bots/refs/heads/main/start.sh
    chmod +x "$INSTALL_DIR/start.sh"  # Setze die Berechtigungen für die Ausführung
    echo_msg "start.sh wurde heruntergeladen und ist jetzt ausführbar."
}

# Hauptfunktion
function main() {
    echo_msg "Starte die Installation..."

    # Frage den Benutzer nach dem Installationsverzeichnis
    read -p "Gib das Verzeichnis an, in dem du die Anwendung installieren möchtest: " INSTALL_DIR

    # Überprüfe, ob das Verzeichnis existiert und erstelle es bei Bedarf
    if [ ! -d "$INSTALL_DIR" ]; then
        echo_msg "Verzeichnis existiert nicht. Erstelle es jetzt..."
        mkdir -p "$INSTALL_DIR"
    fi

    # Wechsle in das Installationsverzeichnis
    cd "$INSTALL_DIR" || { echo "Konnte nicht in das Installationsverzeichnis wechseln."; exit 1; }

    install_system_requirements
    install_ffmpeg  # Installiere ffmpeg
    install_screen  # Installiere screen
    echo_msg "Erstelle die virtuelle Umgebung..."
    python3 -m venv myenv  # Erstelle die virtuelle Umgebung
    source myenv/bin/activate  # Aktiviere die virtuelle Umgebung
    install_python_requirements
    create_env_file
    setup_autostart
    download_start_script  # Lade start.sh herunter

    echo_msg "Installation abgeschlossen! Du kannst den Bot mit './start.sh' starten."
}

# Skript ausführen
main
