// voice-hub plugin GUI: settings page for the local voice-hub TTS server.
//
// Resolved through package.json "./gui-experimental" export. The host shims
// `require` for gui bundles with: solid-js(+web/store), @opencode/plugin/gui
// (+/file /review /browser), @opencode/plugin/rpc, @opencode/client(+solid).
// @opencode/ui components are NOT exposed to plugins, so the page ships its
// own CSS (via the Style registry) built on the app's --v2-* design tokens,
// which follow the app's light/dark theme automatically.
"use strict"

const gui = require("@opencode/plugin/gui")
const { SettingsPage, Style } = gui

const SERVER = "http://127.0.0.1:8095"

const CSS = `
.vh-page{max-width:760px;color:var(--v2-text-text-base);font-size:14px}
.vh-title{font-size:20px;font-weight:700;line-height:1.3;margin:0}
.vh-sub{margin:4px 0 20px;color:var(--v2-text-text-muted);font-size:13px;line-height:1.5}
.vh-status{margin:0 0 12px;font-size:13px;color:var(--v2-text-text-muted)}
.vh-status--error{color:var(--v2-state-fg-danger)}
.vh-card{border:1px solid var(--v2-border-border-muted);border-radius:var(--radius-lg,10px);background:var(--v2-background-bg-layer-01);overflow:hidden}
.vh-row{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:12px 16px}
.vh-row + .vh-row{border-top:1px solid var(--v2-border-border-muted)}
.vh-id{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;min-width:0}
.vh-name{font-weight:600;font-size:14px}
.vh-default{color:var(--v2-state-fg-success);font-size:12px;font-weight:500}
.vh-meta{color:var(--v2-text-text-muted);font-size:12px;margin-top:2px}
.vh-actions{display:flex;gap:8px;flex-shrink:0;align-items:center}
.vh-btn{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:var(--radius-md,8px);border:1px solid var(--v2-border-border-base);background:var(--v2-background-bg-button-neutral);color:var(--v2-text-text-base);font-size:13px;font-weight:500;cursor:pointer;transition:background .12s ease,color .12s ease,opacity .12s ease}
.vh-btn:hover:not(:disabled){background:var(--v2-overlay-simple-overlay-hover)}
.vh-btn:focus-visible{outline:2px solid var(--v2-border-border-focus);outline-offset:1px}
.vh-btn:disabled{opacity:.55;cursor:default}
.vh-btn--accent{background:var(--v2-background-bg-accent);color:var(--v2-background-bg-contrast,#fff);border-color:transparent}
.vh-btn--accent:hover:not(:disabled){background:color-mix(in srgb,var(--v2-background-bg-accent) 85%,transparent)}
.vh-btn--danger{background:transparent;color:var(--v2-state-fg-danger)}
.vh-btn--danger:hover:not(:disabled){background:var(--v2-overlay-simple-overlay-hover)}
.vh-btn--ghost{background:transparent;border-color:transparent;color:var(--v2-text-text-muted);cursor:default}
.vh-empty{padding:16px;color:var(--v2-text-text-muted)}

/* Compact, draggable nakamura-voice-player: no waveform, no time, pill shape.
   The host stylesheet rules are !important because the player rewrites its
   own inline left/top/width every animation frame. */
.nakamura-voice-player{height:auto!important;padding:6px 8px!important;gap:6px!important;border-radius:9999px!important;width:auto!important;transform:none!important;left:auto!important;top:auto!important;right:16px!important;bottom:96px!important;box-shadow:0 6px 18px rgba(0,0,0,.35)!important;cursor:grab!important;touch-action:none!important;transition:left .18s ease-out,top .18s ease-out}
.nakamura-voice-player[data-vh-dragging]{transition:none!important}
.nakamura-voice-player[data-vh-dock]{left:var(--vh-px,16px)!important;top:var(--vh-py,96px)!important;right:auto!important;bottom:auto!important}
.nakamura-voice-player:active{cursor:grabbing!important}
.nakamura-voice-player button{cursor:pointer!important}
.nakamura-voice-player-wave{display:none!important}
.nakamura-voice-player-time{display:none!important}
.nakamura-voice-player-toggle{width:28px!important;height:28px!important}
.nakamura-voice-player-close{width:28px!important;height:28px!important}
`

function el(tag, cls, text) {
  const node = document.createElement(tag)
  if (cls) node.className = cls
  if (text != null) node.textContent = text
  return node
}

function btn(label, variant, onclick, disabled) {
  const node = el("button", "vh-btn" + (variant ? " vh-btn--" + variant : ""))
  node.type = "button"
  node.textContent = label
  if (disabled) node.disabled = true
  else if (onclick) node.addEventListener("click", onclick)
  return node
}

// Make the nakamura-voice-player bar draggable with edge docking.
// The player element already exists in the window (created by the
// nakamura-voice plugin); we only attach pointer handlers and a saved
// position. Its own loop keeps writing inline left/top, but our stylesheet
// uses !important + CSS vars, so the docked position always wins.
function installPlayerTweaks() {
  if (typeof document === "undefined" || typeof MutationObserver === "undefined") return
  const KEY = "voice-hub-player-pos"
  const MARGIN = 16
  const MAGNET = 64
  let bound = null

  function setPos(node, x, y) {
    node.style.setProperty("--vh-px", Math.round(x) + "px")
    node.style.setProperty("--vh-py", Math.round(y) + "px")
    node.setAttribute("data-vh-dock", "")
  }

  function clampPos(node, x, y) {
    const w = node.offsetWidth || 0
    const h = node.offsetHeight || 0
    const maxX = Math.max(0, window.innerWidth - w - 4)
    const maxY = Math.max(0, window.innerHeight - h - 4)
    return [Math.max(4, Math.min(maxX, x)), Math.max(4, Math.min(maxY, y))]
  }

  function bind(root) {
    if (bound === root) return
    bound = root
    try {
      const saved = JSON.parse(localStorage.getItem(KEY) || "null")
      if (saved && typeof saved.x === "number" && typeof saved.y === "number") {
        const [x, y] = clampPos(root, saved.x, saved.y)
        setPos(root, x, y)
      }
    } catch (e) { /* ignore corrupted storage */ }

    root.addEventListener("pointerdown", (e) => {
      if (e.target.closest("button")) return
      e.preventDefault()
      const rect = root.getBoundingClientRect()
      const offX = e.clientX - rect.left
      const offY = e.clientY - rect.top
      root.setAttribute("data-vh-dragging", "")

      const move = (ev) => {
        let x = ev.clientX - offX
        let y = ev.clientY - offY
        ;[x, y] = clampPos(root, x, y)
        // magnetic pull to the nearest edges while dragging
        if (x < MARGIN + MAGNET) x = MARGIN
        else if (x > window.innerWidth - root.offsetWidth - MARGIN - MAGNET) {
          x = window.innerWidth - root.offsetWidth - MARGIN
        }
        if (y < MARGIN + MAGNET) y = MARGIN
        else if (y > window.innerHeight - root.offsetHeight - MARGIN - MAGNET) {
          y = window.innerHeight - root.offsetHeight - MARGIN
        }
        setPos(root, x, y)
      }
      const up = () => {
        document.removeEventListener("pointermove", move)
        document.removeEventListener("pointerup", up)
        // re-enable the snap animation, then dock to the nearest corner
        root.removeAttribute("data-vh-dragging")
        const r = root.getBoundingClientRect()
        const x = (window.innerWidth - r.right < r.left)
          ? window.innerWidth - r.width - MARGIN
          : MARGIN
        const y = (window.innerHeight - r.bottom < r.top)
          ? window.innerHeight - r.height - MARGIN
          : MARGIN
        setPos(root, x, y)
        try { localStorage.setItem(KEY, JSON.stringify({ x, y })) } catch (e) { /* ignore */ }
      }
      document.addEventListener("pointermove", move)
      document.addEventListener("pointerup", up)
    })
  }

  const existing = document.querySelector(".nakamura-voice-player")
  if (existing) { bind(existing); return }
  const obs = new MutationObserver(() => {
    const node = document.querySelector(".nakamura-voice-player")
    if (node) { obs.disconnect(); bind(node) }
  })
  obs.observe(document.body, { childList: true })
}

function setup(ctx) {
  const state = { voices: [], defaultVoice: null, status: null, busy: null, loading: true }

  ctx.add(Style, CSS)
  installPlayerTweaks()

  async function api(path, init) {
    const res = await fetch(SERVER + path, init)
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error((data && data.error && data.error.message) || `HTTP ${res.status}`)
    return data
  }

  async function refresh() {
    try {
      const data = await api("/voices")
      state.voices = data.voices || []
      state.defaultVoice = data.default_voice || null
      if (state.status && state.status.error && state.status.sticky !== true) state.status = null
    } catch (e) {
      state.status = { text: "Сервер голосов недоступен: " + (e && e.message), error: true, sticky: true }
    } finally {
      state.loading = false
      render()
    }
  }

  async function action(path, body, id, successText) {
    state.busy = id
    state.status = null
    render()
    try {
      await api(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      if (successText) state.status = { text: successText, error: false }
    } catch (e) {
      state.status = { text: "Ошибка: " + (e && e.message), error: true }
    } finally {
      state.busy = null
      await refresh()
    }
  }

  function onPreview(v) {
    state.status = { text: "Синтезируем образец: " + v.label + "…", error: false }
    render()
    const a = new Audio(SERVER + "/voices/preview?voice=" + encodeURIComponent(v.id))
    a.onended = () => { state.status = null; render() }
    a.onerror = () => { state.status = { text: "Не удалось синтезировать образец", error: true }; render() }
    void a.play()
  }

  const engineLabel = (v) =>
    v.engine === "silero" ? "Silero · встроен" :
    v.installed ? "Piper · скачан" : "Piper · не скачан"

  function row(v) {
    const isDefault = v.id === state.defaultVoice
    const isBusy = state.busy === v.id

    const actions = el("div", "vh-actions")
    actions.appendChild(
      isDefault
        ? btn("Выбран ✓", "ghost", null, true)
        : btn("Выбрать", "", () => action("/voices/select", { voice: v.id }, v.id, "Голос по умолчанию: " + v.label), isBusy)
    )
    actions.appendChild(btn(isBusy ? "…" : "Прослушать", "", () => onPreview(v), isBusy))
    if (v.engine === "piper") {
      actions.appendChild(
        v.installed
          ? btn("Удалить", "danger", () => action("/voices/delete", { voice: v.id }, v.id, "Голос удалён: " + v.label), isBusy)
          : btn("Скачать", "accent", () => action("/voices/download", { voice: v.id }, v.id, "Голос скачан: " + v.label), isBusy)
      )
    }

    const id = el("div", "vh-id")
    id.appendChild(el("span", "vh-name", v.label))
    if (isDefault) id.appendChild(el("span", "vh-default", "по умолчанию"))

    const left = el("div")
    left.appendChild(id)
    left.appendChild(el("div", "vh-meta", engineLabel(v)))

    const row = el("div", "vh-row")
    row.appendChild(left)
    row.appendChild(actions)
    return row
  }

  let rootEl = null

  function render() {
    if (!rootEl) return
    rootEl.textContent = ""
    const page = el("div", "vh-page")
    page.appendChild(el("h2", "vh-title", "Голоса озвучки"))
    page.appendChild(el("div", "vh-sub",
      "Локальный синтез речи (Silero + Piper). Выбранный голос озвучивает ответы; всё работает офлайн."))
    if (state.status) {
      page.appendChild(el("div", "vh-status" + (state.status.error ? " vh-status--error" : ""), state.status.text))
    }
    const card = el("div", "vh-card")
    if (state.voices.length) {
      for (const v of state.voices) card.appendChild(row(v))
    } else {
      card.appendChild(el("div", "vh-empty", state.loading ? "Загрузка…" : "Голоса не найдены"))
    }
    page.appendChild(card)
    rootEl.appendChild(page)
  }

  ctx.add(SettingsPage, {
    id: "voice-hub",
    icon: "outline-wave-audio",
    get title() { return "Голоса (локальный TTS)" },
    render: () => {
      const mount = el("div")
      rootEl = mount
      render()
      void refresh()
      return mount
    },
  })
}

Object.defineProperty(module.exports, "__esModule", { value: true })
module.exports.default = { setup }
