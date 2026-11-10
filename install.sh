#!/usr/bin/env bash
# OpenCode Voice Local — installer.
#
# Copies the voice-hub server into ~/.config/opencode, creates the Python venv
# for Silero, installs the Piper CLI and the systemd user unit, and copies the
# GUI plugin. It never touches your opencode.jsonc: plugin registration is a
# manual step documented in README.md.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OC_DIR="$HOME/.config/opencode"
SERVER_DIR="$OC_DIR/piper-tts"
SILERO_DIR="$OC_DIR/silero-tts"
PLUGIN_DIR="$OC_DIR/voice-local-plugin"
UNIT_DIR="$HOME/.config/systemd/user"

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

say "Python"
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
python3 --version

say "Server files"
mkdir -p "$SERVER_DIR" "$SILERO_DIR"
install -m 755 "$ROOT/server/server.py" "$SERVER_DIR/server.py"
install -m 755 "$ROOT/server/synth.py" "$SILERO_DIR/synth.py"

say "Silero venv"
if [ ! -x "$SILERO_DIR/venv/bin/python" ]; then
  python3 -m venv "$SILERO_DIR/venv"
  "$SILERO_DIR/venv/bin/python" -m pip install --upgrade pip
  "$SILERO_DIR/venv/bin/python" -m pip install \
    torch --index-url https://download.pytorch.org/whl/cpu
  "$SILERO_DIR/venv/bin/python" -m pip install numpy scipy silero
else
  echo "already present: $SILERO_DIR/venv"
fi

say "Piper CLI"
if [ -x "$HOME/.local/bin/piper" ]; then
  echo "already present: $HOME/.local/bin/piper"
elif command -v uv >/dev/null; then
  uv tool install piper-tts
elif command -v pipx >/dev/null; then
  pipx install piper-tts
else
  python3 -m pip install --user piper-tts
fi

say "systemd unit"
mkdir -p "$UNIT_DIR"
install -m 644 "$ROOT/systemd/voice-hub.service" "$UNIT_DIR/voice-hub.service"
systemctl --user daemon-reload
systemctl --user enable --now voice-hub.service

say "GUI plugin"
mkdir -p "$PLUGIN_DIR"
install -m 644 "$ROOT/plugin/package.json" "$PLUGIN_DIR/package.json"
install -m 644 "$ROOT/plugin/gui.cjs" "$PLUGIN_DIR/gui.cjs"

say "Done"
cat <<EOF
voice-hub:  http://127.0.0.1:8095
plugin:     $PLUGIN_DIR

Next steps:
  1. Add the plugin path to "plugins" in $OC_DIR/opencode.jsonc:
       "$PLUGIN_DIR"
  2. Point your TTS plugin at apiUrl http://127.0.0.1:8095 (engine "openai").
  3. Restart OpenCode Desktop and open Settings -> "Голоса (локальный TTS)".

Check the server:  curl http://127.0.0.1:8095/health
Server logs:       journalctl --user -u voice-hub -f
EOF
