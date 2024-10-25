#!/bin/bash

# Setze das Verzeichnis auf das Verzeichnis des Skripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Pfad zur virtuellen Umgebung
VENV_DIR="$SCRIPT_DIR/myenv"  # Überprüfe, ob dies der korrekte Name deiner virtuellen Umgebung ist

# Überprüfe, ob die virtuelle Umgebung existiert
if [ -d "$VENV_DIR" ]; then
    echo "Aktiviere die virtuelle Umgebung..."
    source "$VENV_DIR/bin/activate"  # Aktiviere die virtuelle Umgebung
else
    echo "Virtuelle Umgebung nicht gefunden. Stelle sicher, dass sie existiert."
    echo "Erstelle die virtuelle Umgebung mit 'python3 -m venv myenv'."
    exit 1
fi

# Starte den Discord-Bot in einer screen-Sitzung
SESSION_NAME="discord_bot"
echo "Starte den Discord-Bot in einer screen-Sitzung..."
screen -dmS "$SESSION_NAME" python3 "$SCRIPT_DIR/discord_bot.py"  # Verwende den relativen Pfad zu discord_bot.py

echo "Discord-Bot läuft jetzt in der Hintergrund-Sitzung '$SESSION_NAME'."
echo "Du kannst die Sitzung mit 'screen -r $SESSION_NAME' wieder betreten."
