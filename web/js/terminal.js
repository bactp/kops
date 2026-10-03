// Terminal frames (pure) and the xterm.js binding (browser only).
import { h, clear } from './dom.js';
import { canUseTerminal } from './state.js';

export const encodeInput = (d) => JSON.stringify({ t: 'i', d });
export const encodeResize = (c, r) => JSON.stringify({ t: 'r', c: Math.max(1, c | 0), r: Math.max(1, r | 0) });

// -> {type:'output',data} | {type:'exit',code} | null
export function decodeFrame(text) {
  let f;
  try { f = JSON.parse(text); } catch { return null; }
  if (!f || typeof f !== 'object') return null;
  if (f.t === 'o' && typeof f.d === 'string') return { type: 'output', data: f.d };
  if (f.t === 'x') return { type: 'exit', code: typeof f.code === 'number' ? f.code : null };
  return null;
}

export function terminalUrl(sessionId, target, tab, loc = globalThis.location) {
  const proto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${loc.host}/api/sessions/${encodeURIComponent(sessionId)}/terminal?target=${encodeURIComponent(target)}&tab=${encodeURIComponent(tab)}`;
}

const THEMES = {
  dark: { background: '#0d1117', foreground: '#d5dbe3', cursor: '#79c0ff' },
  light: { background: '#ffffff', foreground: '#1f2328', cursor: '#0969da', selectionBackground: '#b6d4fe' },
};
const prefersDark = () => !!(globalThis.matchMedia && globalThis.matchMedia('(prefers-color-scheme: dark)').matches);

// One xterm instance bound to one WebSocket.
export class TerminalTab {
  constructor({ sessionId, target, tab, onStatus }) {
    this.sessionId = sessionId; this.target = target; this.tab = tab; this.onStatus = onStatus || (() => {});
    this.status = 'idle'; // idle | connecting | open | closed | exited
    this.el = h('div', { class: 'term-host' });
    this.term = null; this.fit = null; this.ws = null;
    const X = globalThis.Terminal;
    if (X) {
      this.term = new X({ cursorBlink: true, fontSize: 14, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace', theme: prefersDark() ? THEMES.dark : THEMES.light, convertEol: false });
      const F = globalThis.FitAddon && globalThis.FitAddon.FitAddon;
      if (F) { this.fit = new F(); this.term.loadAddon(this.fit); }
      this.term.onData((d) => this._send(encodeInput(d)));
      this.term.onResize(({ cols, rows }) => this._send(encodeResize(cols, rows)));
    } else {
      this.el.append(h('p', { class: 'muted pad' }, 'xterm.js failed to load (CDN unreachable). Reload the page when online.'));
    }
    this.opened = false;
  }
  _setStatus(s) { this.status = s; this.onStatus(s); }
  _send(text) { if (this.ws && this.ws.readyState === 1) this.ws.send(text); }
  attachVisible() {
    if (this.term && !this.opened) { this.term.open(this.el); this.opened = true; }
    this.doFit();
  }
  doFit() {
    if (!this.term || !this.opened || !this.el.offsetParent) return;
    try { this.fit && this.fit.fit(); } catch { /* not laid out yet */ }
    const dims = `${this.term.cols}x${this.term.rows}`;
    if (this.status === 'open' && dims !== this.lastDims) { this.lastDims = dims; this._send(encodeResize(this.term.cols, this.term.rows)); }
  }
  connect() {
    this.disconnect();
    this._setStatus('connecting');
    let ws;
    try { ws = new WebSocket(terminalUrl(this.sessionId, this.target, this.tab)); } catch { this._setStatus('closed'); return; }
    this.ws = ws;
    ws.onopen = () => { this._setStatus('open'); this.lastDims = null; this.doFit(); if (this.term) { this.lastDims = `${this.term.cols}x${this.term.rows}`; this._send(encodeResize(this.term.cols, this.term.rows)); } };
    ws.onmessage = (ev) => {
      const f = decodeFrame(typeof ev.data === 'string' ? ev.data : '');
      if (!f || !this.term) return;
      if (f.type === 'output') this.term.write(f.data);
      else { this.term.write(`\r\n\x1b[2m[shell exited${f.code === null ? '' : ` with code ${f.code}`}]\x1b[0m\r\n`); this._setStatus('exited'); }
    };
    ws.onclose = () => { if (this.ws === ws) { if (this.status !== 'exited') { if (this.term && this.status === 'open') this.term.write('\r\n\x1b[2m[connection closed]\x1b[0m\r\n'); this._setStatus('closed'); } } };
    ws.onerror = () => { /* onclose follows */ };
  }
  disconnect() { const w = this.ws; this.ws = null; if (w) { w.onclose = null; try { w.close(); } catch { /* ignore */ } } }
  focus() { if (this.term) this.term.focus(); }
  dispose() { this.disconnect(); if (this.term) this.term.dispose(); }
}

// Right pane: tabs, target selector, reconnect, state overlay. Persistent per session id.
export class TerminalPane {
  constructor() {
    this.sessionId = null; this.session = null; this.tabs = []; this.active = null; this.counter = 0; this.lastState = null;
    this.tabBar = h('div', { class: 'tabs', role: 'tablist', 'aria-label': 'Terminals' });
    this.targetSel = h('select', { class: 'target-sel', 'aria-label': 'Terminal target host', title: 'Host for new terminals' });
    this.reconnectBtn = h('button', { class: 'btn small', type: 'button', onclick: () => this.reconnect() }, 'Reconnect');
    this.statusEl = h('span', { class: 'muted small-text', role: 'status' });
    this.body = h('div', { class: 'term-body' });
    this.overlay = h('div', { class: 'term-overlay', role: 'status' });
    this.el = h('section', { class: 'pane right-pane', 'aria-label': 'Terminal' },
      h('div', { class: 'pane-head' }, this.tabBar, h('div', { class: 'spacer' }), this.targetSel, this.reconnectBtn),
      h('div', { class: 'term-wrap' }, this.body, this.overlay),
      h('div', { class: 'pane-foot' }, this.statusEl));
    this.ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => this.fitActive()) : null;
    if (this.ro) this.ro.observe(this.body);
    this.extraTabs = [];
    this.render();
  }
  setExtraTabs(names) { this.extraTabs = names; this.render(); }
  bind(session) {
    if (!session || session.id !== this.sessionId) { this.disposeAll(); this.sessionId = session ? session.id : null; this.counter = 0; }
    const prev = this.lastState;
    this.session = session;
    this.lastState = session ? session.state : null;
    if (session) {
      const names = (session.targets || []).map((t) => t.name);
      if (names.join() !== [...this.targetSel.options].map((o) => o.value).join()) {
        clear(this.targetSel);
        for (const t of session.targets || []) this.targetSel.append(h('option', { value: t.name }, `${t.name} (${t.role})`));
      }
      if (canUseTerminal(session.state)) {
        if (!this.tabs.length) this.addTab();
        else if (prev && !canUseTerminal(prev)) for (const t of this.tabs) if (t.status !== 'open' && t.status !== 'connecting') t.connect();
      }
    }
    this.render();
  }
  addTab() {
    if (!this.sessionId) return;
    const target = this.targetSel.value || ((this.session.targets || [])[0] || { name: 'base' }).name;
    const t = new TerminalTab({ sessionId: this.sessionId, target, tab: ++this.counter, onStatus: () => this.render() });
    t.label = `Terminal ${this.counter}`;
    this.tabs.push(t); this.active = t;
    this.body.append(t.el);
    this.render();
    t.attachVisible();
    if (this.session && canUseTerminal(this.session.state)) t.connect();
    t.focus();
  }
  closeTab(t) {
    t.dispose(); t.el.remove();
    this.tabs = this.tabs.filter((x) => x !== t);
    if (this.active === t) this.active = this.tabs[this.tabs.length - 1] || null;
    this.render();
    this.fitActive();
  }
  select(t) { this.active = t; this.render(); t.attachVisible(); t.focus(); }
  reconnect() { if (this.active && this.session && canUseTerminal(this.session.state)) { this.active.connect(); this.active.focus(); } }
  fitActive() { if (this.active) this.active.attachVisible(); }
  disposeAll() { for (const t of this.tabs) { t.dispose(); t.el.remove(); } this.tabs = []; this.active = null; }
  // Call after the pane element was (re)inserted into the page.
  mounted() { requestAnimationFrame(() => this.fitActive()); }
  render() {
    clear(this.tabBar);
    this.tabs.forEach((t) => {
      const sel = t === this.active;
      this.tabBar.append(h('div', { class: `tab ${sel ? 'sel' : ''}` },
        h('button', { class: 'tab-btn', type: 'button', role: 'tab', 'aria-selected': String(sel), onclick: () => this.select(t) },
          h('span', { class: `dot ${t.status}` }), `${t.label}`, h('span', { class: 'muted small-text' }, ` ${t.target}`)),
        h('button', { class: 'tab-x', type: 'button', 'aria-label': `Close ${t.label}`, onclick: () => this.closeTab(t) }, '×')));
    });
    const usable = this.session && canUseTerminal(this.session.state);
    this.tabBar.append(h('button', { class: 'tab-add', type: 'button', 'aria-label': 'New terminal', title: 'New terminal', disabled: !usable, onclick: () => this.addTab() }, '+'));
    for (const n of this.extraTabs) this.tabBar.append(h('span', { class: 'tab placeholder', title: `${n} is not available in this build` }, n));
    this.tabs.forEach((t) => { t.el.hidden = t !== this.active; });
    let msg = '';
    if (!this.session) msg = 'No active session. Start a task or create a playground to get a terminal.';
    else if (!usable) msg = this.session.state === 'INVALID' ? `Session is invalid. ${this.session.message || ''}` : `Terminal unavailable while the session is ${this.session.state}.`;
    this.overlay.textContent = msg;
    this.overlay.hidden = !msg;
    this.reconnectBtn.disabled = !usable || !this.active;
    this.statusEl.textContent = this.active ? `${this.active.label} on ${this.active.target}: ${this.active.status}` : '';
    for (const t of this.tabs) if (t === this.active) t.doFit();
  }
}
