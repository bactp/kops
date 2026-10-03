// KOPS dashboard entry point.
import { createApi } from './js/api.js';
import { SessionStore } from './js/session.js';
import { createRouter } from './js/router.js';
import { TerminalPane } from './js/terminal.js';
import { h, clear, icon, btn, toast } from './js/dom.js';
import { formatCountdown, stateLabel, isGone, friendlyError, canAct } from './js/state.js';
import { badge, errorBox } from './js/views/components.js';
import { createPracticeView } from './js/views/practice.js';
import { createPlaygroundView } from './js/views/playground.js';
import { createProgressView } from './js/views/progress.js';
import { createAdminView } from './js/views/admin.js';

const app = document.getElementById('app');
const api = createApi({ onUnauthenticated: () => { location.href = '/auth/login'; } });

async function boot() {
  let me, config;
  try { [me, config] = await Promise.all([api.me(), api.config()]); }
  catch (e) {
    if (e.status === 401) return;
    clear(app).append(h('main', { class: 'page' }, errorBox(e, boot), h('p', { class: 'muted' }, 'KOPS could not start.')));
    return;
  }
  config.features = config.features || {};
  const store = new SessionStore(api);
  const pane = new TerminalPane();
  const ctx = { api, me, config, store, pane };

  const routes = ['practice', 'playground', 'progress'];
  const views = { practice: createPracticeView(ctx), progress: createProgressView(ctx) };
  if (config.features.playground) views.playground = createPlaygroundView(ctx); else routes.splice(1, 1);
  if (me.is_admin) { views.admin = createAdminView(ctx); routes.push('admin'); }
  const labels = { practice: 'Practice', playground: 'Playground', progress: 'Progress', admin: 'Admin' };

  // ---- shell ----
  const nav = h('nav', { class: 'nav', 'aria-label': 'Main' });
  const sessionBar = h('div', { class: 'sessionbar', 'aria-live': 'polite' });
  const connEl = h('span', { class: 'muted small-text', role: 'status' });
  const view = h('main', { id: 'view', tabindex: '-1' });
  const header = h('header', { class: 'topbar' }, h('a', { class: 'brand', href: '#/practice' }, icon('terminal'), 'KOPS'), nav, h('div', { class: 'spacer' }), sessionBar, connEl,
    h('span', { class: 'user' }, me.username, me.is_admin ? badge('admin', 'tag') : null), h('a', { class: 'btn small', href: '/auth/logout' }, icon('logout'), 'Logout'));
  clear(app).append(h('a', { class: 'skip', href: '#view' }, 'Skip to content'), header, view);

  let current = null;
  const router = createRouter({ routes, fallback: 'practice', onRoute(name) {
    if (current && views[current] && views[current].unmount) views[current].unmount();
    current = name;
    clear(view);
    view.append(views[name].el);
    views[name].mount();
    renderNav(); document.title = `${labels[name]} - KOPS`;
  } });

  function renderNav() {
    clear(nav);
    for (const r of routes) nav.append(h('a', { href: `#/${r}`, 'aria-current': current === r ? 'page' : null }, labels[r]));
  }

  async function extend() {
    try { store.setSession(await api.extend(store.session.id)); toast('Session extended.'); } catch (e) { toast(friendlyError(e), 'error'); }
  }
  function renderSessionBar() {
    const s = store.session;
    clear(sessionBar);
    if (!s || isGone(s.state)) return;
    const title = s.type === 'practice' && s.task ? s.task.title : 'Playground';
    sessionBar.append(h('span', { class: 'crumb' }, s.type === 'practice' ? 'Practice' : 'Playground', s.task ? ` ▸ ${s.task.domain} ▸ ${title}` : ''),
      badge(stateLabel(s.state), `state-${s.state}`),
      s.state === 'INVALID' ? null : h('span', { class: 'timer', title: 'Time left' }, icon('clock'), h('span', { dataset: { countdown: s.expires_at } }, formatCountdown(s.expires_at))),
      s.state === 'INVALID' ? btn('Dismiss', { cls: 'small', onclick: () => store.dismiss() }) : btn('Extend', { cls: 'small', onclick: extend }));
  }
  setInterval(() => {
    for (const el of document.querySelectorAll('[data-countdown]')) el.textContent = formatCountdown(el.dataset.countdown);
  }, 1000);

  store.subscribe((kind) => {
    if (kind === 'session') { pane.bind(store.session && !isGone(store.session.state) ? store.session : null); renderSessionBar(); }
    if (kind === 'mode') connEl.textContent = store.mode === 'poll' ? (store.error ? 'offline, retrying…' : 'polling') : '';
    if (current && views[current]) views[current].onStore(kind);
  });

  router.start();
  try { await store.resume(); }
  catch (e) { if (e.status !== 401) { toast(friendlyError(e), 'error'); } }
  // refresh scenario statuses after a session ends
  let wasLive = false;
  store.subscribe((kind) => {
    if (kind !== 'session') return;
    const live = !!store.session && !isGone(store.session.state);
    if (wasLive && !live && views.practice.refreshScenarios) views.practice.refreshScenarios();
    wasLive = live;
  });
}

boot();
