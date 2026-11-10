# OpenCode Voice Local

**Языки:** [English](README.md) · Русский · [Deutsch](README.de.md) · [Қазақша](README.kk.md) · [Srpski](README.sr.md)

Локальная (полностью офлайн) озвучка ответов для **OpenCode Desktop** с русскими
голосами, страницей настроек и компактным плеером.

Проект состоит из двух частей:

- **voice-hub** — локальный HTTP-сервер с OpenAI-совместимым `POST /v1/audio/speech`,
  оборачивающий два движка синтеза: **Silero v5_ru** (torch) и **Piper** (onnx);
- **GUI-плагин** — страница настроек в OpenCode, где голоса можно выбирать, слушать,
  скачивать и удалять, плюс переопределения для плавающего плеера (компактный вид,
  перетаскивание, прилипание к углам).

Ничего не уходит в интернет: текст и аудио остаются на этой машине.

```
OpenCode Desktop
 ├─ TTS-движок (engine=openai) ──POST /v1/audio/speech──┐
 └─ opencode-voice-local-plugin ──/voices/*─────────────┤
                                                        ▼
                                             voice-hub 127.0.0.1:8095
                                              ├─ Silero v5_ru (torch)
                                              └─ Piper (onnx, ru_RU)
```

## Возможности

- **9 русских голосов**: 5 встроенных Silero + 4 скачиваемых Piper.
- **Страница настроек** «Голоса (локальный TTS)» в общем дизайне приложения
  (дизайн-токены `--v2-*`, светлая/тёмная тема).
- **Прослушивание** голоса прямо со страницы (короткий WAV-образец).
- **Скачивание/удаление** Piper-голосов по кнопке, без ручных команд.
- **Голос по умолчанию** задаётся на странице и всегда применяется при синтезе.
- **Компактный плеер**: без осциллограммы и таймера, перетаскивается мышью,
  прилипает к ближайшему углу, позиция запоминается.
- **OpenAI-совместимый API**: подходит любой клиент, умеющий `/v1/audio/speech`.

## Голоса

| id | Движок | Описание |
| --- | --- | --- |
| `eugene` | Silero | мужской, глубокий (по умолчанию) |
| `aidar` | Silero | мужской, нейтральный |
| `baya` | Silero | мужской, мягкий |
| `kseniya` | Silero | женский, деловой |
| `xenia` | Silero | женский, дружелюбный |
| `ru_RU-denis-medium` | Piper | мужской; ~63 МБ, скачивается |
| `ru_RU-dmitri-medium` | Piper | мужской; ~63 МБ, скачивается |
| `ru_RU-irina-medium` | Piper | женский; ~63 МБ, скачивается |
| `ru_RU-ruslan-medium` | Piper | мужской; ~63 МБ, скачивается |

Silero-голоса входят в модель и не требуют скачивания. Piper-голоса качаются с
HuggingFace (`rhasspy/piper-voices`) и лежат в `~/.local/share/piper-voices/`.

## Требования

- Linux (проверено на Ubuntu 26.04, Wayland, KDE).
- OpenCode Desktop 2.2.x.
- Python 3.10+.
- ~1.5 ГБ на диске (torch CPU + модель Silero + голоса Piper по желанию).
- Интернет — **только** при установке и при первом синтезе Silero
  (torch.hub скачивает модель `snakers4/silero-models`).

## Установка

```bash
git clone https://github.com/Delobot/OpenCode-Voice-Local.git
cd OpenCode-Voice-Local
./install.sh
```

Скрипт:

1. копирует сервер в `~/.config/opencode/piper-tts/server.py` и
   `~/.config/opencode/silero-tts/synth.py` (пути ожидаются сервером);
2. создаёт venv `~/.config/opencode/silero-tts/venv` с `torch` (CPU), `numpy`, `scipy`, `silero`;
3. ставит `piper-tts` в `~/.local/bin/piper` через `uv`, `pipx` или `pip --user`;
4. устанавливает и запускает systemd-юнит `voice-hub.service`;
5. копирует GUI-плагин в `~/.config/opencode/voice-local-plugin`.

Затем зарегистрируйте плагин и перезапустите OpenCode — см. ниже.

### Регистрация плагина

В `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "plugins": [
    "opencode-plugin-voice",
    "/home/<user>/.config/opencode/voice-local-plugin"
  ]
}
```

`opencode-plugin-voice` (Nakamura) даёт сам механизм озвучки; наш плагин добавляет
страницу настроек и оформление плеера. Если вы используете другой TTS-плагин,
достаточно указать ему `apiUrl` на voice-hub.

### Настройка TTS-движка

Движок должен ходить на локальный сервер:

```jsonc
// настройки плагина озвучки (Nakamura: engine "openai")
{
  "engine": "openai",
  "apiUrl": "http://127.0.0.1:8095",
  "apiModel": "voice-hub",
  "apiVoice": "eugene",   // игнорируется: сервер использует голос по умолчанию
  "autoSpeak": true
}
```

Сервер намеренно игнорирует `voice` из запроса: единственный источник истины —
голос, выбранный на странице настроек (сохраняется в
`~/.config/opencode/piper-tts/config.json`).

## Использование

1. **Настройки → Голоса (локальный TTS)** — список голосов.
2. «Выбрать» — сделать голос голосом по умолчанию.
3. «Прослушать» — короткий образец (первый запуск ~10 с: импорт torch).
4. «Скачать» / «Удалить» — управление Piper-голосами.
5. Запустите озвучку ответа — появится компактный плеер (пауза/продолжить, ✕ — отмена).
   Его можно перетащить за пустое место; при отпускании он прилипает к ближайшему углу.

## HTTP API

Сервер слушает `127.0.0.1:8095` (порт меняется константой `PORT` в `server/server.py`).

| Метод | Путь | Тело / параметры | Ответ |
| --- | --- | --- | --- |
| GET | `/health` | — | `{"health":"ok","default_voice":"...","silero_ready":true}` |
| GET | `/v1/models` | — | список моделей в стиле OpenAI |
| GET | `/voices` | — | `{"voices":[...],"default_voice":"..."}` |
| POST | `/voices/select` | `{"voice":"eugene"}` | `{"ok":true,"default_voice":"eugene"}` |
| POST | `/voices/download` | `{"voice":"ru_RU-irina-medium"}` | `{"ok":true}` |
| POST | `/voices/delete` | `{"voice":"ru_RU-irina-medium"}` | `{"ok":true}` |
| GET | `/voices/preview?voice=eugene` | — | `audio/wav` |
| POST | `/v1/audio/speech` | `{"input":"текст","speed":1.0}` | `audio/wav` |

Пример:

```bash
curl -s -X POST http://127.0.0.1:8095/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"input":"Привет! Это локальная озвучка."}' \
  -o speech.wav
```

Silero отдаёт 48 кГц, Piper — 22.05 кГц; оба — mono PCM 16 бит.

## Структура

```
opencode-voice-local/
├── server/
│   ├── server.py        # voice-hub: HTTP-сервер, каталог голосов, конфиг
│   └── synth.py         # хелпер Silero (stdin → WAV, --speaker/--speed/--out)
├── systemd/
│   └── voice-hub.service
├── plugin/
│   ├── package.json     # экспорт "./gui-experimental" → gui.cjs
│   └── gui.cjs          # страница настроек + правки плеера
├── install.sh
├── publish.sh           # публикация на GitHub одной командой
├── LICENSE
├── TODO.md
└── README.md
```

## Диагностика

| Симптом | Что проверить |
| --- | --- |
| `Сервер голосов недоступен` на странице | `systemctl --user status voice-hub`, `curl 127.0.0.1:8095/health` |
| Первое прослушивание долгое (~10 с) | нормально: импорт torch и загрузка модели в память |
| `voice model missing on disk` | скачайте голос кнопкой «Скачать» или выберите Silero-голос |
| Порт занят | измените `PORT` в `server/server.py` и `apiUrl` в настройках движка |
| Страница настроек не появилась | `~/.config/ai.opencode.desktop/logs/*/renderer.log`, строки `[plugin]` |

Логи сервера: `journalctl --user -u voice-hub -f`.

## Лицензия

MIT — см. [LICENSE](LICENSE).
