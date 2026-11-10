# OpenCode Voice Local

**Sprachen:** [English](README.md) · [Русский](README.ru.md) · Deutsch · [Қазақша](README.kk.md) · [Srpski](README.sr.md)

Vollständig offline arbeitende Sprachausgabe (Text-to-Speech) für **OpenCode Desktop**:
neun russische Stimmen, eine Einstellungsseite zu ihrer Verwaltung und ein kompakter
schwebender Player.

Das Projekt besteht aus zwei Teilen:

- **voice-hub** — ein lokaler HTTP-Server mit einer OpenAI-kompatiblen Schnittstelle
  `POST /v1/audio/speech`, der zwei Synthese-Engines kapselt: **Silero v5_ru** (torch)
  und **Piper** (onnx);
- **GUI-Plugin** — eine Einstellungsseite in OpenCode zum Auswählen, Anhören,
  Herunterladen und Löschen von Stimmen, dazu Überschreibungen für den schwebenden
  Player (kompaktes Aussehen, Ziehen, Einrasten an der Ecke).

Nichts verlässt Ihren Rechner: Text und Audio bleiben lokal.

```
OpenCode Desktop
 ├─ TTS-Engine (engine=openai) ──POST /v1/audio/speech──┐
 └─ opencode-voice-local-plugin ──/voices/*─────────────┤
                                                        ▼
                                             voice-hub 127.0.0.1:8095
                                              ├─ Silero v5_ru (torch)
                                              └─ Piper (onnx, ru_RU)
```

## Funktionen

- **Neun russische Stimmen**: 5 integrierte Silero- + 4 herunterladbare Piper-Stimmen.
- **Einstellungsseite** „Голоса (локальный TTS)“ im Design der Anwendung selbst
  (Design-Tokens `--v2-*`, helles und dunkles Thema).
- **Anhören** einer Stimme direkt auf der Seite (kurzes WAV-Beispiel).
- **Herunterladen / Löschen** von Piper-Stimmen per Knopfdruck, ohne manuelle Befehle.
- **Standardstimme** wird auf der Seite gewählt und immer zur Synthese verwendet.
- **Kompakter Player**: ohne Oszilloskop und Timer, per Maus verschiebbar, rastet an
  der nächsten Ecke ein und merkt sich seine Position.
- **OpenAI-kompatible API**: jeder Client, der `/v1/audio/speech` spricht, funktioniert.

## Stimmen

| id | Engine | Beschreibung |
| --- | --- | --- |
| `eugene` | Silero | männlich, tief (Standard) |
| `aidar` | Silero | männlich, neutral |
| `baya` | Silero | männlich, weich |
| `kseniya` | Silero | weiblich, sachlich |
| `xenia` | Silero | weiblich, freundlich |
| `ru_RU-denis-medium` | Piper | männlich; ~63 MB, wird heruntergeladen |
| `ru_RU-dmitri-medium` | Piper | männlich; ~63 MB, wird heruntergeladen |
| `ru_RU-irina-medium` | Piper | weiblich; ~63 MB, wird heruntergeladen |
| `ru_RU-ruslan-medium` | Piper | männlich; ~63 MB, wird heruntergeladen |

Silero-Stimmen sind Teil des Modells und müssen nicht heruntergeladen werden.
Piper-Stimmen stammen von HuggingFace (`rhasspy/piper-voices`) und liegen in
`~/.local/share/piper-voices/`.

## Voraussetzungen

- Linux (getestet auf Ubuntu 26.04, Wayland, KDE).
- OpenCode Desktop 2.2.x.
- Python 3.10+.
- ~1,5 GB Speicherplatz (CPU-torch + Silero-Modell + optionale Piper-Stimmen).
- Internet **nur** bei der Installation und bei der ersten Silero-Synthese
  (torch.hub lädt das Modell `snakers4/silero-models`).

## Installation

```bash
git clone https://github.com/Delobot/OpenCode-Voice-Local.git
cd OpenCode-Voice-Local
./install.sh
```

Das Skript:

1. kopiert den Server nach `~/.config/opencode/piper-tts/server.py` und
   `~/.config/opencode/silero-tts/synth.py` (die vom Server erwarteten Pfade);
2. erstellt die venv `~/.config/opencode/silero-tts/venv` mit `torch` (CPU),
   `numpy`, `scipy`, `silero`;
3. installiert die `piper-tts`-CLI nach `~/.local/bin/piper` über `uv`, `pipx`
   oder `pip --user`;
4. installiert und startet die systemd-User-Unit `voice-hub.service`;
5. kopiert das GUI-Plugin nach `~/.config/opencode/voice-local-plugin`.

Danach das Plugin registrieren und OpenCode neu starten — siehe unten.

### Plugin registrieren

In `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "plugins": [
    "opencode-plugin-voice",
    "/home/<user>/.config/opencode/voice-local-plugin"
  ]
}
```

`opencode-plugin-voice` (Nakamura) liefert den eigentlichen Sprechmechanismus;
unser Plugin ergänzt die Einstellungsseite und das Styling des Players. Bei einem
anderen TTS-Plugin genügt es, dessen `apiUrl` auf voice-hub zu richten.

### TTS-Engine konfigurieren

Die Engine muss den lokalen Server ansprechen:

```jsonc
// Einstellungen des TTS-Plugins (Nakamura: engine "openai")
{
  "engine": "openai",
  "apiUrl": "http://127.0.0.1:8095",
  "apiModel": "voice-hub",
  "apiVoice": "eugene",   // wird ignoriert: der Server nutzt die Standardstimme
  "autoSpeak": true
}
```

Der Server ignoriert `voice` aus der Anfrage bewusst: einzige Quelle der Wahrheit
ist die auf der Einstellungsseite gewählte Stimme (gespeichert in
`~/.config/opencode/piper-tts/config.json`).

## Verwendung

1. **Einstellungen → Голоса (локальный TTS)** — die Stimmenliste.
2. **Auswählen** macht eine Stimme zur Standardstimme.
3. **Anhören** spielt ein kurzes Beispiel ab (beim ersten Mal ~10 s: torch-Import).
4. **Herunterladen** / **Löschen** verwalten Piper-Stimmen.
5. Sprachausgabe einer Antwort starten — ein kompakter Player erscheint
   (Pause/Fortsetzen, ✕ zum Abbrechen). An einer freien Stelle ziehen; beim Loslassen
   rastet er an der nächsten Ecke ein.

## HTTP-API

Der Server lauscht auf `127.0.0.1:8095` (Port über die Konstante `PORT` in
`server/server.py` änderbar).

| Methode | Pfad | Body / Parameter | Antwort |
| --- | --- | --- | --- |
| GET | `/health` | — | `{"health":"ok","default_voice":"...","silero_ready":true}` |
| GET | `/v1/models` | — | Modellliste im OpenAI-Stil |
| GET | `/voices` | — | `{"voices":[...],"default_voice":"..."}` |
| POST | `/voices/select` | `{"voice":"eugene"}` | `{"ok":true,"default_voice":"eugene"}` |
| POST | `/voices/download` | `{"voice":"ru_RU-irina-medium"}` | `{"ok":true}` |
| POST | `/voices/delete` | `{"voice":"ru_RU-irina-medium"}` | `{"ok":true}` |
| GET | `/voices/preview?voice=eugene` | — | `audio/wav` |
| POST | `/v1/audio/speech` | `{"input":"text","speed":1.0}` | `audio/wav` |

Beispiel:

```bash
curl -s -X POST http://127.0.0.1:8095/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"input":"Привет! Это локальная озвучка."}' \
  -o speech.wav
```

Silero liefert 48 kHz, Piper 22,05 kHz; beide als mono 16-Bit-PCM.

## Aufbau

```
opencode-voice-local/
├── server/
│   ├── server.py        # voice-hub: HTTP-Server, Stimmenkatalog, Konfiguration
│   └── synth.py         # Silero-Helfer (stdin → WAV, --speaker/--speed/--out)
├── systemd/
│   └── voice-hub.service
├── plugin/
│   ├── package.json     # exportiert "./gui-experimental" → gui.cjs
│   └── gui.cjs          # Einstellungsseite + Player-Anpassungen
├── install.sh
├── publish.sh           # einmaliger GitHub-Veröffentlicher
├── LICENSE
└── README.md
```

## Fehlersuche

| Symptom | Prüfen |
| --- | --- |
| „Сервер голосов недоступен“ auf der Seite | `systemctl --user status voice-hub`, `curl 127.0.0.1:8095/health` |
| Erstes Anhören ist langsam (~10 s) | normal: torch-Import und Laden des Modells |
| `voice model missing on disk` | Stimme über „Herunterladen“ holen oder Silero-Stimme wählen |
| Port belegt | `PORT` in `server/server.py` und `apiUrl` in den Engine-Einstellungen ändern |
| Einstellungsseite fehlt | `~/.config/ai.opencode.desktop/logs/*/renderer.log`, Zeilen mit `[plugin]` |

Server-Logs: `journalctl --user -u voice-hub -f`.

## Lizenz

MIT — siehe [LICENSE](LICENSE).
