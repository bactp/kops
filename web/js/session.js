// Holds the user's current session. Watches it via SSE, falling back to polling every 3 s.
import { streamEvents } from './sse.js';
import { isFinal, isGone } from './state.js';

const sleepReal = (ms, signal) => new Promise((res) => {
  const t = setTimeout(res, ms);
  if (signal) signal.addEventListener('abort', () => { clearTimeout(t); res(); }, { once: true });
});

export class SessionStore {
  constructor(api, { stream = streamEvents, sleep = sleepReal, pollMs = 3000, pollsBeforeRetry = 5 } = {}) {
    this.api = api; this.stream = stream; this.sleep = sleep; this.pollMs = pollMs; this.pollsBeforeRetry = pollsBeforeRetry;
    this.session = null; this.logs = []; this.mode = 'idle'; // idle | sse | poll
    this.error = null; this.listeners = new Set(); this._ctl = null; this.dismissed = new Set();
    try { for (const id of JSON.parse(localStorage.getItem('kops.dismissed') || '[]')) this.dismissed.add(id); } catch { /* no storage */ }
  }
  subscribe(fn) { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  _emit(kind) { for (const fn of this.listeners) { try { fn(kind, this); } catch (e) { console.error(e); } } }

  setSession(s) {
    const changedId = !this.session || !s || this.session.id !== s.id;
    if (changedId) this.logs = [];
    this.session = s;
    this._emit('session');
  }
  addLog(entry) { this.logs.push(entry); if (this.logs.length > 500) this.logs.shift(); this._emit('log'); }

  // Newest session that is still relevant (not ended/destroyed, not dismissed).
  async resume() {
    const list = await this.api.listSessions();
    const s = (list || []).find((x) => !isGone(x.state) && !this.dismissed.has(x.id)) || null;
    this.setSession(s);
    if (s) this.watch(s.id); else this.stop();
    return s;
  }
  dismiss() {
    if (!this.session) return;
    this.dismissed.add(this.session.id);
    try { localStorage.setItem('kops.dismissed', JSON.stringify([...this.dismissed].slice(-50))); } catch { /* ignore */ }
    this.stop(); this.setSession(null);
  }
  adopt(session) { this.setSession(session); this.watch(session.id); }
  async refresh() {
    if (!this.session) return null;
    const s = await this.api.getSession(this.session.id);
    this.setSession(s);
    return s;
  }
  stop() { if (this._ctl) this._ctl.abort(); this._ctl = null; this.mode = 'idle'; }

  watch(id) {
    this.stop();
    const ctl = new AbortController();
    this._ctl = ctl;
    this._run(id, ctl).catch((e) => console.error(e));
  }

  async _run(id, ctl) {
    const alive = () => !ctl.signal.aborted;
    while (alive()) {
      this.mode = 'sse'; this._emit('mode');
      try {
        await this.stream(`/api/sessions/${encodeURIComponent(id)}/events`, {
          signal: ctl.signal,
          onEvent: ({ event, data }) => {
            if (!alive() || !data) return;
            if (event === 'state') this.setSession(data);
            else if (event === 'log') this.addLog(data);
          },
        });
      } catch { /* dropped: fall back to polling */ }
      if (!alive()) return;
      if (this.session && this.session.id === id && isFinal(this.session.state)) { this.stop(); this._emit('mode'); return; }
      this.mode = 'poll'; this._emit('mode');
      for (let i = 0; i < this.pollsBeforeRetry && alive(); i++) {
        await this.sleep(this.pollMs, ctl.signal);
        if (!alive()) return;
        try {
          const s = await this.api.getSession(id);
          this.error = null;
          if (alive()) this.setSession(s);
          if (isFinal(s.state)) { this.stop(); this._emit('mode'); return; }
        } catch (e) {
          if (e.status === 404) { this.stop(); this.setSession(null); return; }
          if (e.status === 401) { this.stop(); return; }
          this.error = e; this._emit('mode');
        }
      }
    }
  }
}
