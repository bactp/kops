// Shared view components.
import { h, clear, btn, icon, setTrustedHtml } from '../dom.js';
import { timeline, stateLabel, isBusy, friendlyError, isRetryable, difficultyDots, statusLabel } from '../state.js';
import { renderMarkdown } from '../markdown.js';

export function badge(text, cls = '') { return h('span', { class: `badge ${cls}` }, text); }
export const statusBadge = (s) => badge(statusLabel(s), `st-${s || 'none'}`);
export const difficulty = (n) => h('span', { class: 'dots', title: `Difficulty ${n} of 3`, 'aria-label': `Difficulty ${n} of 3` }, difficultyDots(n));

export function markdownBlock(md, cls = 'md') {
  const el = h('div', { class: cls });
  setTrustedHtml(el, renderMarkdown(md)); // renderMarkdown escapes all input
  return el;
}

export function errorBox(err, retry) {
  return h('div', { class: 'alert error', role: 'alert' }, icon('warn'), h('span', {}, friendlyError(err)),
    retry && isRetryable(err) ? btn('Retry', { onclick: retry, cls: 'small' }) : null);
}

export function emptyState(title, text, ...actions) {
  return h('div', { class: 'empty' }, h('h3', {}, title), text ? h('p', { class: 'muted' }, text) : null, ...actions);
}

// Session state, provisioning timeline and live log lines. Call update(store) on store events.
export class StateBlock {
  constructor() {
    this.stateEl = h('div', { class: 'state-line', 'aria-live': 'polite' });
    this.steps = h('ol', { class: 'timeline', 'aria-label': 'Provisioning progress' });
    this.logEl = h('pre', { class: 'log', tabindex: '0', 'aria-label': 'Provisioning log' });
    this.msgEl = h('div', { class: 'alert error', role: 'alert', hidden: true });
    this.el = h('div', { class: 'state-block' }, this.stateEl, this.steps, this.msgEl, this.logEl);
    this.rendered = 0; this.lastKey = '';
  }
  update(store) {
    const s = store.session;
    if (!s) return;
    const key = `${s.id}|${s.state}`;
    if (key !== this.lastKey) {
      this.lastKey = key;
      clear(this.stateEl).append(badge(stateLabel(s.state), `state-${s.state}`), isBusy(s.state) ? h('span', { class: 'spinner', 'aria-hidden': 'true' }) : null);
      clear(this.steps);
      for (const st of timeline(s.state)) this.steps.append(h('li', { class: st.status, 'aria-current': st.status === 'current' ? 'step' : null }, st.label));
      const showTl = ['REQUESTED', 'PROVISIONING', 'SETUP', 'CONFIRMING', 'INVALID'].includes(s.state);
      this.steps.hidden = !showTl;
    }
    this.msgEl.hidden = !(s.state === 'INVALID');
    this.msgEl.textContent = s.state === 'INVALID' ? (s.message || 'The session could not be prepared.') : '';
    if (store.logs.length < this.rendered) { this.logEl.textContent = ''; this.rendered = 0; }
    for (; this.rendered < store.logs.length; this.rendered++) {
      const l = store.logs[this.rendered];
      this.logEl.append(document.createTextNode(`${(l.ts || '').slice(11, 19)} ${l.line}\n`));
    }
    this.logEl.hidden = store.logs.length === 0;
    if (!this.logEl.hidden) this.logEl.scrollTop = this.logEl.scrollHeight;
  }
}
