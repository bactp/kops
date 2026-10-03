import { h, clear, btn, confirmDialog, toast } from '../dom.js';
import { friendlyError, canAct, formatCountdown } from '../state.js';
import { StateBlock, emptyState, badge } from './components.js';

export function createPlaygroundView(ctx) {
  const { api, store, pane } = ctx;
  const stateBlock = new StateBlock();
  const info = h('div', { class: 'pg-info' });
  const root = h('div', { class: 'two-pane' });
  const left = h('section', { class: 'pane left-pane', 'aria-label': 'Playground' }, h('div', { class: 'pane-head' }, h('h2', { class: 'pane-title' }, 'Playground')), h('div', { class: 'pane-body' }, info));
  root.append(left);
  let busy = false;

  const pg = () => (store.session && store.session.type === 'playground' && !['ENDED', 'DESTROYED'].includes(store.session.state) ? store.session : null);

  async function run(fn, ok) {
    busy = true; render();
    try { const r = await fn(); if (ok) toast(ok); return r; }
    catch (e) { toast(friendlyError(e), 'error'); }
    finally { busy = false; render(); }
  }
  const create = async () => { const s = await run(() => api.createSession({ type: 'playground' })); if (s) store.adopt(s); };
  const extend = async () => { const s = await run(() => api.extend(pg().id), 'Session extended.'); if (s) store.setSession(s); else store.refresh().catch(() => {}); };
  const reset = async () => {
    if (!(await confirmDialog('Reset playground?', 'The cluster is restored to its initial state.', 'Reset'))) return;
    const s = await run(() => api.restart(pg().id)); if (s) { store.setSession(s); store.watch(s.id); }
  };
  const del = async () => {
    if (!(await confirmDialog('Delete playground?', 'The sandbox is destroyed.', 'Delete'))) return;
    await run(() => api.remove(pg().id), 'Playground is being destroyed.'); store.refresh().catch(() => {});
  };

  function render() {
    clear(info);
    const other = store.session && store.session.type === 'practice' && !['ENDED', 'DESTROYED'].includes(store.session.state);
    const s = pg();
    if (!s) {
      info.append(emptyState('Free-form Kubernetes sandbox', 'A disposable cluster with no task and no grading. Use it to explore and test commands.',
        other ? h('p', { class: 'alert warn' }, 'A practice session is active. ', h('a', { href: '#/practice' }, 'Resume it'), ' or end it before creating a playground.')
          : btn('Create playground', { iconName: 'play', cls: 'primary', disabled: busy, onclick: create })));
      return;
    }
    const ok = canAct(s.state);
    info.append(h('div', { class: 'row wrap' }, h('strong', {}, 'Playground'), badge(`extensions ${s.extensions}`, 'tag')),
      stateBlock.el,
      h('p', {}, 'Expires in ', h('strong', { dataset: { countdown: s.expires_at } }, formatCountdown(s.expires_at))),
      h('div', { class: 'actions' },
        btn('Extend', { iconName: 'clock', disabled: busy, onclick: extend }),
        btn('Reset', { iconName: 'undo', disabled: busy || !ok, onclick: reset }),
        btn('Delete', { iconName: 'stop', cls: 'danger', disabled: busy, onclick: del })));
    stateBlock.update(store);
  }

  return {
    el: root,
    mount() { root.append(pane.el); pane.setExtraTabs([]); render(); pane.mounted(); },
    onStore() { render(); },
  };
}
