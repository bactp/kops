// Minimal DOM helper. Text is always inserted as text nodes, never as HTML.

export function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else if (k === 'dataset') Object.assign(el.dataset, v);
    else if (v === true) el.setAttribute(k, '');
    else el.setAttribute(k, String(v));
  }
  append(el, kids);
  return el;
}

export function append(el, kids) {
  for (const k of kids.flat(Infinity)) {
    if (k === null || k === undefined || k === false) continue;
    el.append(k instanceof Node ? k : document.createTextNode(String(k)));
  }
}

export function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }

// Only used with output of renderMarkdown (which escapes all input) or static constants.
export function setTrustedHtml(el, html) { el.innerHTML = html; return el; }

const ICONS = {
  play: '<path d="M8 5v14l11-7z"/>', check: '<path d="M20 6 9 17l-5-5"/>', x: '<path d="M18 6 6 18M6 6l12 12"/>',
  bulb: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>',
  book: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2zM4 21V5"/>', skip: '<path d="M5 5v14l9-7zM18 5v14"/>',
  undo: '<path d="M3 7v6h6M3 13a9 9 0 1 0 3-7"/>', stop: '<rect x="6" y="6" width="12" height="12" rx="1"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', plus: '<path d="M12 5v14M5 12h14"/>',
  warn: '<path d="M12 3 2 20h20zM12 10v5M12 18v.5"/>', logout: '<path d="M9 21H5V3h4M16 17l5-5-5-5M21 12H9"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-3-6.7M21 4v5h-5"/>', terminal: '<path d="M4 5h16v14H4zM7 9l3 3-3 3M12 15h5"/>',
};
export function icon(name) {
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('class', 'icon'); s.setAttribute('aria-hidden', 'true');
  s.setAttribute('fill', 'none'); s.setAttribute('stroke', 'currentColor'); s.setAttribute('stroke-width', '2');
  s.setAttribute('stroke-linecap', 'round'); s.setAttribute('stroke-linejoin', 'round');
  s.innerHTML = ICONS[name] || '';
  return s;
}

export function btn(label, { iconName, onclick, cls = '', disabled = false, title, type = 'button' } = {}) {
  return h('button', { class: `btn ${cls}`.trim(), type, onclick, disabled, title }, iconName ? icon(iconName) : null, label);
}

export function confirmDialog(title, body, okLabel = 'Confirm') {
  return new Promise((resolve) => {
    const dlg = h('dialog', { class: 'dlg', 'aria-labelledby': 'dlg-title' },
      h('h3', { id: 'dlg-title' }, title), h('p', {}, body),
      h('div', { class: 'row end' },
        h('button', { class: 'btn', type: 'button', onclick: () => dlg.close('cancel') }, 'Cancel'),
        h('button', { class: 'btn danger', type: 'button', autofocus: true, onclick: () => dlg.close('ok') }, okLabel)));
    dlg.addEventListener('close', () => { const ok = dlg.returnValue === 'ok'; dlg.remove(); resolve(ok); });
    document.body.append(dlg);
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
  });
}

export function toast(msg, kind = 'info') {
  let box = document.getElementById('toasts');
  if (!box) { box = h('div', { id: 'toasts', 'aria-live': 'polite' }); document.body.append(box); }
  const t = h('div', { class: `toast ${kind}` }, msg);
  box.append(t);
  setTimeout(() => t.remove(), kind === 'error' ? 8000 : 4000);
}
