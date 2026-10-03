import { h, clear, btn, icon, confirmDialog, toast } from '../dom.js';
import { filterScenarios, domainsOf, scenarioDomain, isBusy, canAct, HintState, friendlyError, formatCountdown, stateLabel } from '../state.js';
import { badge, statusBadge, difficulty, markdownBlock, errorBox, emptyState, StateBlock } from './components.js';

export function createPracticeView(ctx) {
  const { api, store, pane } = ctx;
  const ui = { tab: 'tasks', filters: { profile: '', domain: '', difficulty: '', q: '' }, selected: null, picking: false,
    scenarios: null, loadError: null, check: null, checking: false, busy: false, hints: null, hintKey: '', hintErr: null };

  const tabs = { tasks: h('div', { class: 'tabpanel' }), task: h('div', { class: 'tabpanel' }), hints: h('div', { class: 'tabpanel' }) };
  const tabBar = h('div', { class: 'tabs', role: 'tablist', 'aria-label': 'Task panels' });
  const left = h('section', { class: 'pane left-pane', 'aria-label': 'Task' }, h('div', { class: 'pane-head' }, tabBar), h('div', { class: 'pane-body' }, tabs.tasks, tabs.task, tabs.hints));
  const root = h('div', { class: 'two-pane' }, left);
  const stateBlock = new StateBlock();

  const session = () => store.session;
  const practice = () => (store.session && store.session.type === 'practice' && !['ENDED', 'DESTROYED'].includes(store.session.state) ? store.session : null);

  function setTab(t) { ui.tab = t; renderTabs(); if (t === 'hints') syncHints(); }
  function renderTabs() {
    clear(tabBar);
    for (const [id, label] of [['tasks', 'Tasks'], ['task', 'Task'], ['hints', 'Hints']]) {
      const sel = ui.tab === id;
      tabBar.append(h('button', { class: 'tab-btn', type: 'button', role: 'tab', 'aria-selected': String(sel), onclick: () => setTab(id), onkeydown: tabKeys }, label));
      tabs[id].hidden = !sel;
    }
  }
  function tabKeys(e) {
    const order = ['tasks', 'task', 'hints'];
    const i = order.indexOf(ui.tab);
    if (e.key === 'ArrowRight') { setTab(order[(i + 1) % 3]); tabBar.children[(i + 1) % 3].focus(); }
    if (e.key === 'ArrowLeft') { setTab(order[(i + 2) % 3]); tabBar.children[(i + 2) % 3].focus(); }
  }

  // ---- Tasks tab ----
  const listBox = h('div', { class: 'task-list', role: 'list' });
  const detailBox = h('div', { class: 'task-detail' });
  const filterBox = h('form', { class: 'filters', onsubmit: (e) => e.preventDefault() });
  const searchInput = h('input', { type: 'search', placeholder: 'Search tasks', 'aria-label': 'Search tasks', oninput: (e) => { ui.filters.q = e.target.value; renderList(); } });
  const profSel = h('select', { 'aria-label': 'Profile', onchange: (e) => { ui.filters.profile = e.target.value; ui.filters.domain = ''; renderFilters(); renderList(); } },
    h('option', { value: '' }, 'All profiles'), h('option', { value: 'cka' }, 'CKA'), h('option', { value: 'ckad' }, 'CKAD'));
  const domSel = h('select', { 'aria-label': 'Domain', onchange: (e) => { ui.filters.domain = e.target.value; renderList(); } });
  const diffSel = h('select', { 'aria-label': 'Difficulty', onchange: (e) => { ui.filters.difficulty = e.target.value; renderList(); } },
    h('option', { value: '' }, 'Any difficulty'), h('option', { value: '1' }, 'Easy (1)'), h('option', { value: '2' }, 'Medium (2)'), h('option', { value: '3' }, 'Hard (3)'));
  filterBox.append(searchInput, h('div', { class: 'row wrap' }, profSel, domSel, diffSel));
  tabs.tasks.append(h('div', { class: 'pickbanner', hidden: true, id: 'pickbanner' }), filterBox, listBox, detailBox);

  function renderFilters() {
    clear(domSel).append(h('option', { value: '' }, 'All domains'));
    for (const d of domainsOf(ui.scenarios || [], ui.filters.profile)) domSel.append(h('option', { value: d, selected: d === ui.filters.domain }, d));
  }
  async function loadScenarios() {
    ui.loadError = null;
    try { ui.scenarios = await api.scenarios(); renderFilters(); }
    catch (e) { ui.loadError = e; }
    renderList();
  }
  function renderList() {
    clear(listBox);
    tabs.tasks.querySelector('#pickbanner').hidden = !ui.picking;
    tabs.tasks.querySelector('#pickbanner').textContent = ui.picking ? 'Pick the next task, then press "Switch to this task".' : '';
    if (ui.loadError) { listBox.append(errorBox(ui.loadError, loadScenarios)); return renderDetail(); }
    if (!ui.scenarios) { listBox.append(h('p', { class: 'muted pad' }, 'Loading tasks…')); return renderDetail(); }
    const rows = filterScenarios(ui.scenarios, ui.filters);
    if (!rows.length) listBox.append(emptyState('No tasks match', 'Clear the filters or search text.'));
    for (const sc of rows) {
      const sel = ui.selected === sc.id;
      const dom = scenarioDomain(sc, ui.filters.profile);
      listBox.append(h('button', { class: `task-row ${sel ? 'sel' : ''} ${sc.available ? '' : 'unavailable'}`, type: 'button', role: 'listitem', 'aria-pressed': String(sel),
        'aria-disabled': sc.available ? null : 'true', title: sc.available ? sc.title : (sc.availability_note || 'Not available yet'),
        onclick: () => { ui.selected = sc.id; renderList(); } },
        h('span', { class: 'tr-main' }, h('span', { class: 'tr-title' }, sc.title), h('span', { class: 'muted small-text' }, dom)),
        h('span', { class: 'tr-side' }, difficulty(sc.difficulty), statusBadge(sc.status))));
    }
    renderDetail();
  }
  function renderDetail() {
    clear(detailBox);
    const sc = (ui.scenarios || []).find((x) => x.id === ui.selected);
    if (!sc) { detailBox.append(h('p', { class: 'muted pad' }, 'Select a task to see its summary.')); return; }
    const active = practice();
    const profs = Object.entries(sc.profiles || {}).map(([p, v]) => `${p.toUpperCase()} · ${v.domain} · ${v.competency}`);
    detailBox.append(h('h3', {}, sc.title),
      h('div', { class: 'row wrap' }, difficulty(sc.difficulty), statusBadge(sc.status), ...(sc.tags || []).map((t) => badge(t, 'tag'))),
      h('ul', { class: 'plain muted' }, profs.map((p) => h('li', {}, p))),
      !sc.available ? h('div', { class: 'alert warn' }, icon('warn'), sc.availability_note || 'Not available yet.') : null);
    if (active && canAct(active.state) && ui.picking && sc.id !== active.scenario_id) {
      detailBox.append(btn('Switch to this task', { iconName: 'skip', cls: 'primary', disabled: !sc.available || ui.busy, onclick: () => doNext(sc.id) }));
    } else if (active) {
      detailBox.append(h('p', { class: 'muted' }, 'You have an active session. Use "Next task" in the Task tab to switch.'));
    } else if (store.session && store.session.type === 'playground' && store.session.state !== 'INVALID') {
      detailBox.append(h('p', { class: 'muted' }, 'A playground session is active. End it before starting a task.'));
    } else {
      detailBox.append(btn('Start', { iconName: 'play', cls: 'primary', disabled: !sc.available || ui.busy, onclick: () => doStart(sc.id) }));
    }
  }

  async function guard(fn, okMsg) {
    ui.busy = true; renderAll();
    try { const r = await fn(); if (okMsg) toast(okMsg); return r; }
    catch (e) { toast(friendlyError(e), 'error'); }
    finally { ui.busy = false; renderAll(); }
  }
  async function doStart(id) {
    const s = await guard(() => api.createSession({ type: 'practice', scenario_id: id, seed: null }));
    if (s) { ui.check = null; ui.picking = false; store.adopt(s); setTab('task'); }
  }
  async function doNext(id) {
    const s = await guard(() => api.next(session().id, id));
    if (s) { ui.check = null; ui.picking = false; store.setSession(s); store.watch(s.id); setTab('task'); }
  }

  // ---- Task tab ----
  const taskHead = h('div', { class: 'task-head' });
  const taskText = h('div', { class: 'task-text' });
  const actions = h('div', { class: 'actions', role: 'group', 'aria-label': 'Task actions' });
  const resultBox = h('div', { class: 'check-result', 'aria-live': 'polite' });
  tabs.task.append(taskHead, stateBlock.el, taskText, actions, resultBox);
  let textKey = '';

  function renderTask() {
    const s = practice() || (store.session && store.session.state === 'INVALID' ? store.session : null);
    const none = !s;
    stateBlock.el.hidden = none; taskHead.hidden = none; actions.hidden = none; resultBox.hidden = none;
    if (none) {
      taskText.textContent = '';
      textKey = '';
      taskText.append(emptyState('No active task', 'Choose a task in the Tasks tab and press Start.', btn('Browse tasks', { onclick: () => setTab('tasks') })));
      return;
    }
    if (taskText.querySelector('.empty')) { clear(taskText); textKey = ''; }
    stateBlock.update(store);
    clear(taskHead);
    if (s.task) taskHead.append(h('h2', {}, s.task.title), h('div', { class: 'row wrap muted' }, difficulty(s.task.difficulty), badge(s.task.domain, 'tag'), h('span', {}, `Attempt ${s.attempt}`), h('span', {}, `Hints used ${s.hints_used}`), s.solution_viewed ? badge('solution viewed', 'st-solved_assisted') : null));
    const key = `${s.id}|${s.attempt}|${s.task ? s.task.text_md : ''}`;
    if (key !== textKey) { textKey = key; clear(taskText); if (s.task) taskText.append(markdownBlock(s.task.text_md)); }
    const act = canAct(s.state) && !ui.busy && !ui.checking;
    clear(actions).append(
      btn('CHECK', { iconName: 'check', cls: 'primary', disabled: !act, onclick: doCheck }),
      btn('Hint', { iconName: 'bulb', disabled: !act && s.state !== 'CHECKING' ? true : false, onclick: () => { setTab('hints'); } }),
      btn('Show solution', { iconName: 'book', disabled: s.state === 'INVALID', onclick: () => { setTab('hints'); askSolution(); } }),
      btn('Next task', { iconName: 'skip', disabled: !act, onclick: () => { ui.picking = true; setTab('tasks'); renderList(); } }),
      btn('Restart task', { iconName: 'undo', disabled: !act, onclick: doRestart }),
      btn('End session', { iconName: 'stop', cls: 'danger', disabled: ui.busy, onclick: doEnd }));
    renderResult(s);
  }
  async function doCheck() {
    const s = session();
    ui.checking = true; renderAll();
    try {
      ui.check = await api.check(s.id, true);
      toast(ui.check.outcome === 'PASS' ? 'All required criteria passed.' : `Check outcome: ${ui.check.outcome}`);
    } catch (e) { ui.check = { error: e }; }
    ui.checking = false;
    store.refresh().catch(() => {});
    renderAll();
  }
  async function doRestart() {
    if (!(await confirmDialog('Restart task?', 'The task is reset to its initial state. Your changes are lost.', 'Restart'))) return;
    const s = await guard(() => api.restart(session().id));
    if (s) { ui.check = null; store.setSession(s); store.watch(s.id); }
  }
  async function doEnd() {
    if (!(await confirmDialog('End session?', 'The sandbox is destroyed and any unsaved work is lost.', 'End session'))) return;
    await guard(() => api.remove(session().id), 'Session is being destroyed.');
    store.refresh().catch(() => {});
  }
  function renderResult(s) {
    clear(resultBox);
    if (ui.checking || s.state === 'CHECKING') { resultBox.append(h('p', { class: 'muted' }, h('span', { class: 'spinner' }), ' Running checks…')); return; }
    if (ui.check && ui.check.error) { resultBox.append(errorBox(ui.check.error, doCheck)); return; }
    const c = ui.check || s.last_check;
    if (!c) return;
    resultBox.append(h('div', { class: `outcome ${c.outcome}` }, h('strong', {}, c.outcome === 'PASS' ? 'PASS' : c.outcome === 'FAIL' ? 'FAIL' : 'INVALID'),
      h('span', {}, ` ${c.required_passed}/${c.required_total} required criteria passed`), c.seconds != null ? h('span', { class: 'muted' }, ` in ${c.seconds}s`) : null),
      h('ul', { class: 'criteria' }, (c.criteria || []).map((k) => h('li', { class: `crit ${k.status}` },
        h('span', { class: 'crit-icon', 'aria-label': k.status }, icon(k.status === 'pass' ? 'check' : k.status === 'fail' ? 'x' : 'warn')),
        h('div', {}, h('div', {}, h('code', {}, k.id), ' ', k.required ? badge('required', 'req') : badge('optional', 'tag'), ' ', h('span', { class: 'muted' }, k.status)),
          k.evidence ? h('div', { class: 'evidence muted' }, k.evidence) : null)))));
  }

  // ---- Hints tab ----
  const hintBox = h('div', { class: 'hints' });
  tabs.hints.append(hintBox);
  async function syncHints() {
    const s = practice();
    if (!s) { ui.hints = null; ui.hintKey = ''; return renderHints(); }
    const key = `${s.id}|${s.scenario_id}|${s.attempt}`;
    if (key === ui.hintKey && ui.hints) return renderHints();
    ui.hintKey = key;
    let count = 3;
    try { count = (await api.scenario(s.scenario_id)).hint_count || 3; } catch { /* keep default */ }
    const hs = new HintState(count);
    ui.hints = hs;
    for (let n = 1; n <= s.hints_used && n <= count; n++) { // re-read hints already revealed (idempotent)
      try { hs.addHint(n, (await api.hint(s.id, n)).text_md); } catch { break; }
    }
    renderHints();
  }
  async function revealHint() {
    const s = practice(), hs = ui.hints;
    const n = hs.nextHint;
    ui.hintErr = null; ui.busy = true; renderHints();
    try { hs.addHint(n, (await api.hint(s.id, n)).text_md); store.refresh().catch(() => {}); }
    catch (e) { if (e.status === 404) hs.hintsExhausted(); else ui.hintErr = e; }
    ui.busy = false; renderHints();
  }
  async function askSolution() {
    await syncHints();
    const hs = ui.hints, s = practice();
    if (!hs || !s || hs.solutionStatus !== 'hidden') return;
    hs.askSolution(); renderHints();
    if (!(await confirmDialog('Show the solution?', 'Viewing the solution marks this attempt as assisted.', 'Show solution'))) { hs.cancelSolution(); return renderHints(); }
    hs.confirmSolution(); renderHints();
    try { hs.solutionLoaded((await api.solution(s.id)).explanation_md); store.refresh().catch(() => {}); }
    catch (e) { hs.solutionFailed(); ui.hintErr = e; }
    renderHints();
  }
  function renderHints() {
    clear(hintBox);
    const s = practice(), hs = ui.hints;
    if (!s) { hintBox.append(emptyState('No active task', 'Hints are available while a task is running.')); return; }
    if (!hs) { hintBox.append(h('p', { class: 'muted pad' }, 'Loading…')); return; }
    if (ui.hintErr) hintBox.append(errorBox(ui.hintErr));
    hintBox.append(h('p', { class: 'muted' }, `${hs.revealed} of ${hs.hintCount} hints revealed. Hints are counted but do not change your status.`));
    hs.hints.forEach((t, i) => hintBox.append(h('details', { class: 'hint', open: true }, h('summary', {}, `Hint ${i + 1}`), markdownBlock(t))));
    hintBox.append(btn(hs.canReveal() ? `Reveal hint ${hs.nextHint}` : 'No more hints', { iconName: 'bulb', disabled: !hs.canReveal() || ui.busy || !canAct(s.state) && s.state !== 'CHECKING', onclick: revealHint }));
    hintBox.append(h('hr'));
    if (hs.solutionStatus === 'shown') hintBox.append(h('h3', {}, 'Solution'), h('p', { class: 'muted' }, 'This attempt is marked as assisted.'), markdownBlock(hs.solution));
    else hintBox.append(btn(hs.solutionStatus === 'loading' ? 'Loading solution…' : 'Show solution', { iconName: 'book', disabled: hs.solutionStatus !== 'hidden', onclick: askSolution }));
  }

  function renderAll() { renderTask(); renderDetail(); renderHints(); }
  function banner() {
    const s = store.session;
    if (s && s.type === 'playground' && !['ENDED', 'DESTROYED'].includes(s.state)) {
      root.prepend(h('div', { class: 'alert warn banner', id: 'pgbanner' }, 'A playground session is active. ', h('a', { href: '#/playground' }, 'Go to Playground')));
    } else { const old = root.querySelector('#pgbanner'); if (old) old.remove(); }
  }

  return {
    el: root,
    mount() {
      root.append(pane.el);
      if (ctx.config.features.editor) pane.setExtraTabs([...(ctx.config.features.editor ? ['Editor'] : []), ...(ctx.config.features.docs ? ['Docs'] : [])]);
      else pane.setExtraTabs(ctx.config.features.docs ? ['Docs'] : []);
      if (practice() && ui.tab === 'tasks' && !ui.selected) ui.tab = 'task';
      renderTabs(); renderAll(); banner();
      if (!ui.scenarios) loadScenarios(); else renderList();
      pane.mounted();
    },
    onStore(kind) {
      if (kind === 'log' || kind === 'session' || kind === 'mode') { banner(); renderTask(); if (kind === 'session') { renderDetail(); const s = practice(); if (s && ui.hints && ui.hintKey !== `${s.id}|${s.scenario_id}|${s.attempt}`) syncHints(); } }
    },
    refreshScenarios: () => api.scenarios().then((l) => { ui.scenarios = l; renderList(); }).catch(() => {}),
  };
}
