// Hash router. Routes are "#/name"; unknown routes fall back to the default.

export function parseHash(hash, routes, fallback) {
  const name = String(hash || '').replace(/^#\/?/, '').split(/[/?]/)[0];
  return routes.includes(name) ? name : fallback;
}

export function createRouter({ routes, fallback, onRoute, win = globalThis }) {
  const current = () => parseHash(win.location.hash, routes, fallback);
  const handle = () => onRoute(current());
  win.addEventListener('hashchange', handle);
  return {
    start: handle,
    current,
    go(name) { if (current() === name && win.location.hash === `#/${name}`) handle(); else win.location.hash = `#/${name}`; },
  };
}
