# OpenCode Voice Local

**Languages:** English · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Қазақша](README.kk.md)

Fully offline text-to-speech for **OpenCode Desktop**: nine Russian voices, a settings
page for managing them, and a compact floating player.

The project has two parts:

- **voice-hub** — a local HTTP server exposing an OpenAI-compatible
  `POST /v1/audio/speech`, wrapping two synthesis engines: **Silero v5_ru** (torch)
  and **Piper** (onnx);
- **GUI plugin** — a settings page inside OpenCode to select, preview, download and
  delete voices, plus overrides for the floating player (compact look, drag,
  snap-to-corner).

Nothing ever leaves your machine: both the text and the audio stay local.

```
OpenCode Desktop
 ├─ TTS engine (engine=openai) ──POST /v1/audio/speech──┐
 └─ opencode-voice-local-plugin ──/voices/*─────────────┤
                                                        ▼
                                             voice-hub 127.0.0.1:8095
                                              ├─ Silero v5_ru (torch)
                                              └─ Piper (onnx, ru_RU)
```

## Features

- **Nine Russian voices**: 5 built-in Silero + 4 downloadable Piper.
- **Settings page** — "Голоса (локальный TTS)" — matching the app's own design
  language (design tokens `--v2-*`, light and dark themes).
- **Preview** a voice straight from the page (a short WAV sample).
- **Download / delete** Piper voices with one button, no manual commands.
- **Default voice** is chosen on the page and is always used for synthesis.
- **Compact player**: no oscilloscope or timer, drag it anywhere, it snaps to the
  nearest corner and remembers its position.
- **OpenAI-compatible API**: any client that speaks `/v1/audio/speech` works.

## Voices

| id | Engine | Description |
| --- | --- | --- |
| `eugene` | Silero | male, deep (default) |
| `aidar` | Silero | male, neutral |
| `baya` | Silero | male, soft |
| `kseniya` | Silero | female, businesslike |
| `xenia` | Silero | female, friendly |
| `ru_RU-denis-medium` | Piper | male; ~63 MB, downloadable |
| `ru_RU-dmitri-medium` | Piper | male; ~63 MB, downloadable |
| `ru_RU-irina-medium` | Piper | female; ~63 MB, downloadable |
| `ru_RU-ruslan-medium` | Piper | male; ~63 MB, downloadable |

Silero voices ship with the model and need no download. Piper voices are fetched
from HuggingFace (`rhasspy/piper-voices`) and stored in `~/.local/share/piper-voices/`.

## Requirements

- Linux (tested on Ubuntu 26.04, Wayland, KDE).
- OpenCode Desktop 2.2.x.
- Python 3.10+.
- ~1.5 GB on disk (CPU torch + Silero model + optional Piper voices).
- Internet **only** during installation and on the first Silero synthesis
  (torch.hub downloads the `snakers4/silero-models` model).

## Installation

```bash
git clone https://github.com/Delobot/OpenCode-Voice-Local.git
cd OpenCode-Voice-Local
./install.sh
```

The script:

1. copies the server to `~/.config/opencode/piper-tts/server.py` and
   `~/.config/opencode/silero-tts/synth.py` (the paths the server expects);
2. creates the venv `~/.config/opencode/silero-tts/venv` with `torch` (CPU),
   `numpy`, `scipy`, `silero`;
3. installs the `piper-tts` CLI into `~/.local/bin/piper` via `uv`, `pipx` or
   `pip --user`;
4. installs and starts the systemd user unit `voice-hub.service`;
5. copies the GUI plugin to `~/.config/opencode/voice-local-plugin`.

Then register the plugin and restart OpenCode — see below.

### Registering the plugin

In `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "plugins": [
    "opencode-plugin-voice",
    "/home/<user>/.config/opencode/voice-local-plugin"
  ]
}
```

`opencode-plugin-voice` (Nakamura) provides the speech mechanism itself; our plugin
adds the settings page and the player styling. If you use a different TTS plugin,
it is enough to point its `apiUrl` at voice-hub.

### Configuring the TTS engine

The engine must talk to the local server:

```jsonc
// TTS plugin settings (Nakamura: engine "openai")
{
  "engine": "openai",
  "apiUrl": "http://127.0.0.1:8095",
  "apiModel": "voice-hub",
  "apiVoice": "eugene",   // ignored: the server uses the default voice
  "autoSpeak": true
}
```

The server deliberately ignores `voice` from the request: the single source of
truth is the voice selected on the settings page (stored in
`~/.config/opencode/piper-tts/config.json`).

## Usage

1. **Settings → Голоса (локальный TTS)** — the voice list.
2. **Select** makes a voice the default one.
3. **Preview** plays a short sample (the first run takes ~10 s: torch import).
4. **Download** / **Delete** manage Piper voices.
5. Trigger speech for an answer — a compact player appears (pause/resume, ✕ to
   cancel). Drag it by any empty spot; on release it snaps to the nearest corner.

## HTTP API

The server listens on `127.0.0.1:8095` (change the `PORT` constant in
`server/server.py` to move it).

| Method | Path | Body / query | Response |
| --- | --- | --- | --- |
| GET | `/health` | — | `{"health":"ok","default_voice":"...","silero_ready":true}` |
| GET | `/v1/models` | — | OpenAI-style model list |
| GET | `/voices` | — | `{"voices":[...],"default_voice":"..."}` |
| POST | `/voices/select` | `{"voice":"eugene"}` | `{"ok":true,"default_voice":"eugene"}` |
| POST | `/voices/download` | `{"voice":"ru_RU-irina-medium"}` | `{"ok":true}` |
| POST | `/voices/delete` | `{"voice":"ru_RU-irina-medium"}` | `{"ok":true}` |
| GET | `/voices/preview?voice=eugene` | — | `audio/wav` |
| POST | `/v1/audio/speech` | `{"input":"text","speed":1.0}` | `audio/wav` |

Example:

```bash
curl -s -X POST http://127.0.0.1:8095/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"input":"Привет! Это локальная озвучка."}' \
  -o speech.wav
```

Silero outputs 48 kHz, Piper 22.05 kHz; both are mono 16-bit PCM.

## Layout

```
opencode-voice-local/
├── server/
│   ├── server.py        # voice-hub: HTTP server, voice catalog, config
│   └── synth.py         # Silero helper (stdin → WAV, --speaker/--speed/--out)
├── systemd/
│   └── voice-hub.service
├── plugin/
│   ├── package.json     # exports "./gui-experimental" → gui.cjs
│   └── gui.cjs          # settings page + player tweaks
├── install.sh
├── publish.sh           # one-shot GitHub publisher
├── LICENSE
├── TODO.md
└── README.md
```

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| "Сервер голосов недоступен" on the page | `systemctl --user status voice-hub`, `curl 127.0.0.1:8095/health` |
| First preview is slow (~10 s) | expected: torch import and model load |
| `voice model missing on disk` | download the voice with the Download button, or pick a Silero voice |
| Port already in use | change `PORT` in `server/server.py` and `apiUrl` in the engine settings |
| Settings page missing | `~/.config/ai.opencode.desktop/logs/*/renderer.log`, lines with `[plugin]` |

Server logs: `journalctl --user -u voice-hub -f`.

## License

MIT — see [LICENSE](LICENSE).
