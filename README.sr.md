# OpenCode Voice Local

**Jezici:** [English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Қазақша](README.kk.md) · Srpski

Potpuno oflajn (bez interneta) sinteza govora za **OpenCode Desktop**: devet ruskih
glasova, stranica sa podešavanjima za njihovo upravljanje i kompaktan lebdeći plejer.

Projekat se sastoji iz dva dela:

- **voice-hub** — lokalni HTTP server sa OpenAI-kompatibilnim `POST /v1/audio/speech`,
  koji obavija dva motora sinteze: **Silero v5_ru** (torch) i **Piper** (onnx);
- **GUI dodatak (plugin)** — stranica sa podešavanjima u OpenCode-u za biranje,
  slušanje, preuzimanje i brisanje glasova, uz prepisivanje stila lebdećeg plejera
  (kompaktan izgled, prevlačenje, prijanjanje uz ivicu).

Ništa ne napušta vaš računar: i tekst i zvuk ostaju lokalno.

```
OpenCode Desktop
 ├─ TTS motor (engine=openai) ──POST /v1/audio/speech──┐
 └─ opencode-voice-local-plugin ──/voices/*────────────┤
                                                       ▼
                                            voice-hub 127.0.0.1:8095
                                             ├─ Silero v5_ru (torch)
                                             └─ Piper (onnx, ru_RU)
```

## Mogućnosti

- **Devet ruskih glasova**: 5 ugrađenih Silero + 4 Piper koja se preuzimaju.
- **Stranica sa podešavanjima** „Голоса (локальный TTS)“ u dizajnu same aplikacije
  (dizajn-tokeni `--v2-*`, svetla i tamna tema).
- **Slušanje** glasa direktno sa stranice (kratak WAV uzorak).
- **Preuzimanje / brisanje** Piper glasova jednim dugmetom, bez ručnih komandi.
- **Podrazumevani glas** bira se na stranici i uvek se koristi pri sintezi.
- **Kompaktan plejer**: bez osciloskopa i tajmera, prevlači se mišem, prijanja uz
  najbliži ugao i pamti svoju poziciju.
- **OpenAI-kompatibilan API**: radi sa svakim klijentom koji poznaje `/v1/audio/speech`.

## Glasovi

| id | Motor | Opis |
| --- | --- | --- |
| `eugene` | Silero | muški, dubok (podrazumevani) |
| `aidar` | Silero | muški, neutralan |
| `baya` | Silero | muški, mekan |
| `kseniya` | Silero | ženski, poslovan |
| `xenia` | Silero | ženski, prijateljski |
| `ru_RU-denis-medium` | Piper | muški; ~63 MB, preuzima se |
| `ru_RU-dmitri-medium` | Piper | muški; ~63 MB, preuzima se |
| `ru_RU-irina-medium` | Piper | ženski; ~63 MB, preuzima se |
| `ru_RU-ruslan-medium` | Piper | muški; ~63 MB, preuzima se |

Silero glasovi su deo modela i ne zahtevaju preuzimanje. Piper glasovi se preuzimaju
sa HuggingFace (`rhasspy/piper-voices`) i čuvaju u `~/.local/share/piper-voices/`.

## Zahtevi

- Linux (testirano na Ubuntu 26.04, Wayland, KDE).
- OpenCode Desktop 2.2.x.
- Python 3.10+.
- ~1,5 GB na disku (CPU torch + Silero model + opcionalni Piper glasovi).
- Internet **samo** pri instalaciji i pri prvoj Silero sintezi
  (torch.hub preuzima model `snakers4/silero-models`).

## Instalacija

```bash
git clone https://github.com/Delobot/OpenCode-Voice-Local.git
cd OpenCode-Voice-Local
./install.sh
```

Skripta:

1. kopira server u `~/.config/opencode/piper-tts/server.py` i
   `~/.config/opencode/silero-tts/synth.py` (putanje koje server očekuje);
2. pravi venv `~/.config/opencode/silero-tts/venv` sa `torch` (CPU), `numpy`,
   `scipy`, `silero`;
3. instalira `piper-tts` CLI u `~/.local/bin/piper` preko `uv`, `pipx` ili `pip --user`;
4. instalira i pokreće systemd korisničku jedinicu `voice-hub.service`;
5. kopira GUI dodatak u `~/.config/opencode/voice-local-plugin`.

Zatim registrujte dodatak i restartujte OpenCode — vidi dole.

### Registracija dodatka

U `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "plugins": [
    "opencode-plugin-voice",
    "/home/<user>/.config/opencode/voice-local-plugin"
  ]
}
```

`opencode-plugin-voice` (Nakamura) daje sam mehanizam govora; naš dodatak dodaje
stranicu sa podešavanjima i stilizovanje plejera. Ako koristite drugi TTS dodatak,
dovoljno je da njegov `apiUrl` usmerite na voice-hub.

### Podešavanje TTS motora

Motor mora da komunicira sa lokalnim serverom:

```jsonc
// podešavanja TTS dodatka (Nakamura: engine "openai")
{
  "engine": "openai",
  "apiUrl": "http://127.0.0.1:8095",
  "apiModel": "voice-hub",
  "apiVoice": "eugene",   // ignoriše se: server koristi podrazumevani glas
  "autoSpeak": true
}
```

Server namerno ignoriše `voice` iz zahteva: jedini izvor istine je glas izabran na
stranici sa podešavanjima (čuva se u `~/.config/opencode/piper-tts/config.json`).

## Korišćenje

1. **Podešavanja → Голоса (локальный TTS)** — lista glasova.
2. **Izaberi** čini glas podrazumevanim.
3. **Poslušaj** pušta kratak uzorak (prvi put ~10 s: uvoz torch-a).
4. **Preuzmi** / **Obriši** upravljaju Piper glasovima.
5. Pokrenite govor za odgovor — pojavljuje se kompaktan plejer (pauza/nastavi, ✕ —
   otkaži). Prevlači se za prazno mesto; pri otpuštanju prijanja uz najbliži ugao.

## HTTP API

Server sluša na `127.0.0.1:8095` (port se menja konstantom `PORT` u `server/server.py`).

| Metod | Putanja | Telo / parametri | Odgovor |
| --- | --- | --- | --- |
| GET | `/health` | — | `{"health":"ok","default_voice":"...","silero_ready":true}` |
| GET | `/v1/models` | — | lista modela u OpenAI stilu |
| GET | `/voices` | — | `{"voices":[...],"default_voice":"..."}` |
| POST | `/voices/select` | `{"voice":"eugene"}` | `{"ok":true,"default_voice":"eugene"}` |
| POST | `/voices/download` | `{"voice":"ru_RU-irina-medium"}` | `{"ok":true}` |
| POST | `/voices/delete` | `{"voice":"ru_RU-irina-medium"}` | `{"ok":true}` |
| GET | `/voices/preview?voice=eugene` | — | `audio/wav` |
| POST | `/v1/audio/speech` | `{"input":"tekst","speed":1.0}` | `audio/wav` |

Primer:

```bash
curl -s -X POST http://127.0.0.1:8095/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"input":"Привет! Это локальная озвучка."}' \
  -o speech.wav
```

Silero daje 48 kHz, Piper 22,05 kHz; oba su mono PCM 16 bita.

## Struktura

```
opencode-voice-local/
├── server/
│   ├── server.py        # voice-hub: HTTP server, katalog glasova, konfiguracija
│   └── synth.py         # Silero pomoćnik (stdin → WAV, --speaker/--speed/--out)
├── systemd/
│   └── voice-hub.service
├── plugin/
│   ├── package.json     # izvoz "./gui-experimental" → gui.cjs
│   └── gui.cjs          # stranica sa podešavanjima + izmene plejera
├── install.sh
├── publish.sh           # objavljivanje na GitHub jednom komandom
├── LICENSE
└── README.md
```

## Rešavanje problema

| Simptom | Šta proveriti |
| --- | --- |
| „Сервер голосов недоступен“ na stranici | `systemctl --user status voice-hub`, `curl 127.0.0.1:8095/health` |
| Prvo slušanje je sporo (~10 s) | normalno: uvoz torch-a i učitavanje modela |
| `voice model missing on disk` | preuzmite glas dugmetom „Preuzmi“ ili izaberite Silero glas |
| Port je zauzet | izmenite `PORT` u `server/server.py` i `apiUrl` u podešavanjima motora |
| Stranica sa podešavanjima se ne pojavljuje | `~/.config/ai.opencode.desktop/logs/*/renderer.log`, linije sa `[plugin]` |

Logovi servera: `journalctl --user -u voice-hub -f`.

## Licenca

MIT — vidi [LICENSE](LICENSE).
