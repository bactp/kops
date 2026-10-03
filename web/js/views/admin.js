import { h, clear, btn, confirmDialog, toast } from '../dom.js';
import { memPct, friendlyError } from '../state.js';
import { errorBox, badge } from './components.js';

export function createAdminView(ctx) {
  const { api } = ctx;
  const root = h('div', { class: 'page' });
  let timer = null;

  const table = (cols, rows) => h('div', { class: 'table-wrap' }, h('table', {}, h('thead', {}, h('tr', {}, cols.map((c) => h('th', { scope: 'col' }, c)))), h('tbody', {}, rows)));
  const when = (t) => (t ? new Date(t).toLocaleString() : '-');

  async function load() {
    try {
      const [sessions, users, cap] = await Promise.all([api.adminSessions(), api.adminUsers(), api.adminCapacity()]);
      render(sessions, users, cap);
    } catch (e) { clear(root).append(errorBox(e, load)); }
  }
  async function del(s) {
    if (!(await confirmDialog('Delete session?', `Destroy session ${s.id} of ${s.owner}.`, 'Delete'))) return;
    try { await api.adminDeleteSession(s.id); toast('Deletion requested.'); } catch (e) { toast(friendlyError(e), 'error'); }
    load();
  }
  function render(sessions, users, cap) {
    clear(root);
    root.append(h('div', { class: 'row' }, h('h2', {}, 'Admin'), h('div', { class: 'spacer' }), btn('Refresh', { iconName: 'refresh', onclick: load })));
    root.append(h('h3', {}, 'Capacity'), h('p', {}, `Provider ${cap.provider}. Active sessions ${cap.active_sessions} of ${cap.max_sessions}. Orphans: `, badge(String(cap.orphans), cap.orphans ? 'st-attempted' : 'tag')));
    root.append(h('div', { class: 'summary' }, (cap.nodes || []).map((n) => {
      const pct = memPct(n.memory_requested_mib, n.memory_allocatable_mib);
      return h('div', { class: 'sum-row' }, h('div', { class: 'sum-label' }, n.name),
        h('div', { class: 'bar', role: 'img', 'aria-label': `${n.name}: ${n.memory_requested_mib} of ${n.memory_allocatable_mib} MiB requested` }, h('span', { class: `seg ${pct > 85 ? 'attempted' : 'solved'}`, style: `width:${pct}%` })),
        h('div', { class: 'muted small-text' }, `${n.memory_requested_mib}/${n.memory_allocatable_mib} MiB (${pct}%)`));
    })));
    root.append(h('h3', {}, 'Sessions'), table(['ID', 'Owner', 'Type', 'State', 'Scenario', 'Created', 'Expires', ''],
      sessions.map((s) => h('tr', {}, h('td', {}, h('code', {}, s.id)), h('td', {}, s.owner), h('td', {}, s.type), h('td', {}, badge(s.state, `state-${s.state}`)), h('td', {}, s.scenario_id || '-'),
        h('td', {}, when(s.created_at)), h('td', {}, when(s.expires_at)), h('td', {}, btn('Delete', { cls: 'small danger', onclick: () => del(s) }))))));
    root.append(h('h3', {}, 'Users'), table(['User', 'Email', 'Created', 'Last seen', 'Active session', 'Sessions'],
      users.map((u) => h('tr', {}, h('td', {}, u.username), h('td', {}, u.email || '-'), h('td', {}, when(u.created_at)), h('td', {}, when(u.last_seen_at)), h('td', {}, u.active_session ? h('code', {}, u.active_session) : '-'), h('td', {}, String(u.sessions_total))))));
  }
  return { el: root, mount() { clear(root).append(h('p', { class: 'muted pad' }, 'Loading…')); load(); timer = setInterval(load, 15000); }, unmount() { clearInterval(timer); }, onStore() {} };
}
