# OpenCode Voice Local

**Тілдер:** [English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · Қазақша · [Srpski](README.sr.md)

**OpenCode Desktop** үшін толық офлайн (интернетсіз) дауыстау: тоғыз орыс дауысы,
оларды басқаруға арналған баптаулар беті және ықшам қалқымалы ойнатқыш.

Жоба екі бөліктен тұрады:

- **voice-hub** — OpenAI-үйлесімді `POST /v1/audio/speech` ұсынатын жергілікті HTTP
  сервері; ол екі синтез қозғалтқышын қапсырады: **Silero v5_ru** (torch) және
  **Piper** (onnx);
- **GUI-плагин** — OpenCode ішіндегі баптаулар беті: дауыстарды таңдау, тыңдау,
  жүктеп алу және жою, сонымен қатар қалқымалы ойнатқышты өзгерту (ықшам көрініс,
  сүйреу, бұрышқа жабысу).

Ешнәрсе интернетке кетпейді: мәтін де, аудио да осы компьютерде қалады.

```
OpenCode Desktop
 ├─ TTS қозғалтқышы (engine=openai) ──POST /v1/audio/speech──┐
 └─ opencode-voice-local-plugin ──────/voices/*──────────────┤
                                                             ▼
                                                  voice-hub 127.0.0.1:8095
                                                   ├─ Silero v5_ru (torch)
                                                   └─ Piper (onnx, ru_RU)
```

## Мүмкіндіктер

- **Тоғыз орыс дауысы**: 5 кіріктірілген Silero + 4 жүктелетін Piper.
- **Баптаулар беті** «Голоса (локальный TTS)» қолданбаның өз дизайнында
  (дизайн-токендер `--v2-*`, ашық және қараңғы тақырып).
- Дауысты **тыңдау** — тікелей беттен (қысқа WAV үлгісі).
- Piper дауыстарын **жүктеп алу / жою** — бір түймемен, қолмен командасыз.
- **Әдепкі дауыс** бетте таңдалады және синтезде әрқашан сол қолданылады.
- **Ықшам ойнатқыш**: осциллограммасыз және таймерсіз, тінтуірмен сүйреледі,
  жақын бұрышқа жабысады, орны есте сақталады.
- **OpenAI-үйлесімді API**: `/v1/audio/speech` түсінетін кез келген клиент жарайды.

## Дауыстар

| id | Қозғалтқыш | Сипаттама |
| --- | --- | --- |
| `eugene` | Silero | ер, терең (әдепкі) |
| `aidar` | Silero | ер, бейтарап |
| `baya` | Silero | ер, жұмсақ |
| `kseniya` | Silero | әйел, іскер |
| `xenia` | Silero | әйел, жайдарлы |
| `ru_RU-denis-medium` | Piper | ер; ~63 МБ, жүктеледі |
| `ru_RU-dmitri-medium` | Piper | ер; ~63 МБ, жүктеледі |
| `ru_RU-irina-medium` | Piper | әйел; ~63 МБ, жүктеледі |
| `ru_RU-ruslan-medium` | Piper | ер; ~63 МБ, жүктеледі |

Silero дауыстары модельге кіреді, жүктеуді қажет етпейді. Piper дауыстары
HuggingFace (`rhasspy/piper-voices`) сайтынан алынып, `~/.local/share/piper-voices/`
қалтасында сақталады.

## Талаптар

- Linux (Ubuntu 26.04, Wayland, KDE жүйесінде тексерілген).
- OpenCode Desktop 2.2.x.
- Python 3.10+.
- Дискіде ~1,5 ГБ (CPU torch + Silero моделі + қалауыңызша Piper дауыстары).
- Интернет — **тек** орнату кезінде және алғашқы Silero синтезінде
  (torch.hub `snakers4/silero-models` моделін жүктейді).

## Орнату

```bash
git clone https://github.com/Delobot/OpenCode-Voice-Local.git
cd OpenCode-Voice-Local
./install.sh
```

Скрипт:

1. серверді `~/.config/opencode/piper-tts/server.py` және
   `~/.config/opencode/silero-tts/synth.py` жолдарына көшіреді (сервер осы жолдарды күтеді);
2. `~/.config/opencode/silero-tts/venv` виртуалды ортасын `torch` (CPU), `numpy`,
   `scipy`, `silero` құрамдастарымен жасайды;
3. `piper-tts` CLI-ын `~/.local/bin/piper` жолына `uv`, `pipx` немесе `pip --user`
   арқылы орнатады;
4. `voice-hub.service` systemd пайдаланушы юнитін орнатып, іске қосады;
5. GUI-плагинді `~/.config/opencode/voice-local-plugin` қалтасына көшіреді.

Содан кейін плагинді тіркеп, OpenCode-ты қайта іске қосыңыз — төменде қараңыз.

### Плагинді тіркеу

`~/.config/opencode/opencode.jsonc` файлында:

```jsonc
{
  "plugins": [
    "opencode-plugin-voice",
    "/home/<user>/.config/opencode/voice-local-plugin"
  ]
}
```

`opencode-plugin-voice` (Nakamura) дауыстау тетігін береді; біздің плагин баптаулар
бетін және ойнатқыштың безендірілуін қосады. Басқа TTS-плагин қолдансаңыз, оның
`apiUrl` мәнін voice-hub-қа бағыттау жеткілікті.

### TTS қозғалтқышын баптау

Қозғалтқыш жергілікті серверге жүгінуі керек:

```jsonc
// дауыстау плагинінің баптаулары (Nakamura: engine "openai")
{
  "engine": "openai",
  "apiUrl": "http://127.0.0.1:8095",
  "apiModel": "voice-hub",
  "apiVoice": "eugene",   // еленбейді: сервер әдепкі дауысты пайдаланады
  "autoSpeak": true
}
```

Сервер сұранымдағы `voice` мәнін әдейі елемейді: жалғыз ақиқат көзі — баптаулар
бетінде таңдалған дауыс (`~/.config/opencode/piper-tts/config.json` ішінде сақталады).

## Қолдану

1. **Баптаулар → Голоса (локальный TTS)** — дауыстар тізімі.
2. **Таңдау** — дауысты әдепкі етеді.
3. **Тыңдау** — қысқа үлгіні ойнатады (алғашқы жолы ~10 с: torch импорты).
4. **Жүктеу** / **Жою** — Piper дауыстарын басқарады.
5. Жауапты дауыстауды іске қосыңыз — ықшам ойнатқыш шығады (кідірту/жалғастыру,
   ✕ — тоқтату). Оны бос жерден сүйреуге болады; жібергенде жақын бұрышқа жабысады.

## HTTP API

Сервер `127.0.0.1:8095` портында тыңдайды (портты `server/server.py` ішіндегі `PORT`
константасымен өзгертуге болады).

| Әдіс | Жол | Дене / параметр | Жауап |
| --- | --- | --- | --- |
| GET | `/health` | — | `{"health":"ok","default_voice":"...","silero_ready":true}` |
| GET | `/v1/models` | — | OpenAI стиліндегі модельдер тізімі |
| GET | `/voices` | — | `{"voices":[...],"default_voice":"..."}` |
| POST | `/voices/select` | `{"voice":"eugene"}` | `{"ok":true,"default_voice":"eugene"}` |
| POST | `/voices/download` | `{"voice":"ru_RU-irina-medium"}` | `{"ok":true}` |
| POST | `/voices/delete` | `{"voice":"ru_RU-irina-medium"}` | `{"ok":true}` |
| GET | `/voices/preview?voice=eugene` | — | `audio/wav` |
| POST | `/v1/audio/speech` | `{"input":"мәтін","speed":1.0}` | `audio/wav` |

Мысал:

```bash
curl -s -X POST http://127.0.0.1:8095/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"input":"Привет! Это локальная озвучка."}' \
  -o speech.wav
```

Silero 48 кГц, Piper 22,05 кГц береді; екеуі де — mono PCM 16 бит.

## Құрылым

```
opencode-voice-local/
├── server/
│   ├── server.py        # voice-hub: HTTP-сервер, дауыстар каталогы, конфиг
│   └── synth.py         # Silero көмекшісі (stdin → WAV, --speaker/--speed/--out)
├── systemd/
│   └── voice-hub.service
├── plugin/
│   ├── package.json     # "./gui-experimental" → gui.cjs экспорты
│   └── gui.cjs          # баптаулар беті + ойнатқыш түзетулері
├── install.sh
├── publish.sh           # GitHub-қа бір командамен жариялау
├── LICENSE
├── TODO.md
└── README.md
```

## Ақаулықтарды жою

| Белгі | Нені тексеру керек |
| --- | --- |
| Бетте «Сервер голосов недоступен» | `systemctl --user status voice-hub`, `curl 127.0.0.1:8095/health` |
| Алғашқы тыңдау ұзақ (~10 с) | қалыпты: torch импорты мен модельді жүктеу |
| `voice model missing on disk` | дауысты «Жүктеу» түймесімен алыңыз немесе Silero дауысын таңдаңыз |
| Порт бос емес | `server/server.py` ішіндегі `PORT` пен қозғалтқыш баптауындағы `apiUrl`-ды өзгертіңіз |
| Баптаулар беті шықпады | `~/.config/ai.opencode.desktop/logs/*/renderer.log`, `[plugin]` жолдары |

Сервер логтары: `journalctl --user -u voice-hub -f`.

## Лицензия

MIT — [LICENSE](LICENSE) қараңыз.
