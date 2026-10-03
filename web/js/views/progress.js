import { h, clear, btn } from '../dom.js';
import { summarizeProgress, formatDuration } from '../state.js';
import { statusBadge, errorBox, emptyState } from './components.js';

export function createProgressView(ctx) {
  const { api } = ctx;
  const root = h('div', { class: 'page' });
  let titles = {};

  async function load() {
    clear(root).append(h('p', { class: 'muted pad' }, 'Loading progress…'));
    try {
      const [p, sc] = await Promise.all([api.progress(), api.scenarios().catch(() => [])]);
      titles = Object.fromEntries(sc.map((s) => [s.id, s.title]));
      render(p);
    } catch (e) { clear(root).append(errorBox(e, load)); }
  }

  function bar(r) {
    return h('div', { class: 'bar', role: 'img', 'aria-label': `${r.solved} solved, ${r.assisted} assisted, ${r.attempted} attempted of ${r.total}` },
      h('span', { class: 'seg solved', style: `width:${r.solvedPct}%` }), h('span', { class: 'seg assisted', style: `width:${r.assistedPct}%` }), h('span', { class: 'seg attempted', style: `width:${r.attemptedPct}%` }));
  }

  function render(p) {
    clear(root);
    const { rows, totals } = summarizeProgress(p);
    root.append(h('h2', {}, 'Progress'));
    if (!rows.length && !(p.scenarios || []).length) { root.append(emptyState('Nothing yet', 'Complete a task and your progress appears here.', h('a', { class: 'btn primary', href: '#/practice' }, 'Start practising'))); return; }
    root.append(h('p', { class: 'muted' }, `${totals.solved} solved, ${totals.assisted} assisted, ${totals.attempted} attempted of ${totals.total} tasks.`),
      h('div', { class: 'legend' }, h('span', { class: 'seg solved' }), ' solved ', h('span', { class: 'seg assisted' }), ' assisted ', h('span', { class: 'seg attempted' }), ' attempted'),
      h('div', { class: 'summary' }, rows.map((r) => h('div', { class: 'sum-row' }, h('div', { class: 'sum-label' }, h('strong', {}, r.profile.toUpperCase()), ` ${r.domain}`), bar(r),
        h('div', { class: 'muted small-text' }, `${r.solved + r.assisted + 0}/${r.total}`)))));
    root.append(h('h3', {}, 'Tasks'));
    const tbl = h('table', {}, h('thead', {}, h('tr', {}, ['Task', 'Status', 'Attempts', 'Best', 'Last checked', 'Time spent'].map((c) => h('th', { scope: 'col' }, c)))),
      h('tbody', {}, (p.scenarios || []).map((s) => h('tr', {}, h('td', {}, titles[s.scenario_id] || s.scenario_id), h('td', {}, statusBadge(s.status)), h('td', {}, String(s.attempts)),
        h('td', {}, s.best_outcome || '-'), h('td', {}, s.last_checked_at ? new Date(s.last_checked_at).toLocaleString() : '-'), h('td', {}, formatDuration(s.seconds_spent))))));
    root.append(h('div', { class: 'table-wrap' }, tbl));
  }
  return { el: root, mount: load, onStore() {} };
}
