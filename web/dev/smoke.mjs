// Smoke test of the JS client modules against a running mock (or real) server. Works on Node >= 12.
// Usage: node web/dev/smoke.mjs http://localhost:8099
import http from 'http';
import { createApi } from '../js/api.js';
import { streamEvents } from '../js/sse.js';
import { SessionStore } from '../js/session.js';

const B = process.argv[2] || 'http://localhost:8099';
if (!globalThis.AbortController) { globalThis.AbortController = class { constructor() { const l = []; this.signal = { aborted: false, addEventListener: (_, f) => l.push(f) }; this.abort = () => { this.signal.aborted = true; l.forEach((f) => f()); }; } }; }

// minimal fetch over http (text() and streaming body reader)
function nodeFetch(url, init = {}) {
  return new Promise((resolve, reject) => {
    const req = http.request(url, { method: init.method || 'GET', headers: init.headers }, (res) => {
      const base = { status: res.statusCode, ok: res.statusCode < 400, statusText: res.statusMessage };
      resolve(Object.assign(base, {
        text: () => new Promise((r) => { let b = ''; res.on('data', (c) => (b += c)); res.on('end', () => r(b)); }),
        body: { getReader: () => { const q = []; let done = false, wake = null; res.on('data', (c) => { q.push(c); if (wake) wake(); }); res.on('end', () => { done = true; if (wake) wake(); }); res.on('error', () => { done = true; if (wake) wake(); });
          return { read: () => new Promise((r) => { const go = () => { if (q.length) r({ done: false, value: q.shift() }); else if (done) r({ done: true }); else wake = go; }; go(); }) }; } },
      }));
    });
    req.on('error', reject);
    if (init.signal) init.signal.addEventListener('abort', () => req.abort());
    if (init.body) req.write(init.body);
    req.end();
  });
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const api = createApi({ base: B, fetchImpl: nodeFetch });

async function main() {
  console.log('me', await api.me());
  console.log('scenarios', (await api.scenarios()).length);
  let s = await api.createSession({ type: 'practice', scenario_id: 'kops-net-service-endpoint-repair-001' });
  console.log('created', s.state);
  try { await api.createSession({ type: 'playground' }); } catch (e) { console.log('second create ->', e.code, e.status); }
  const seen = [];
  const ac = new AbortController();
  await streamEvents(`${B}/api/sessions/${s.id}/events`, { fetchImpl: (u, i) => nodeFetch(u, Object.assign({}, i, { signal: ac.signal })), signal: ac.signal,
    onEvent: (e) => { seen.push(e.event + ':' + (e.data.state || e.data.line)); if (e.data.state === 'ACTIVE') ac.abort(); } }).catch((e) => console.log('stream ended:', e.message));
  console.log('events', seen.join(' | '));
  let c = await api.check(s.id, true); console.log('check1', c.outcome, c.required_passed + '/' + c.required_total);
  c = await api.check(s.id, true); console.log('check2', c.outcome);
  console.log('hint', (await api.hint(s.id, 1)).text_md, '| hint4 ->', await api.hint(s.id, 4).catch((e) => e.status));
  console.log('solution chars', (await api.solution(s.id)).explanation_md.length, 'hints_used', (await api.getSession(s.id)).hints_used);
  console.log('progress', JSON.stringify((await api.progress()).summary));
  console.log('capacity', JSON.stringify(await api.adminCapacity()));
  await api.remove(s.id);
  await sleep(1200);
  console.log('after delete', (await api.getSession(s.id)).state);
  const st = new SessionStore(api, { stream: (u, o) => streamEvents(B + u, Object.assign({ fetchImpl: nodeFetch }, o)) });
  console.log('resume ->', await st.resume());
  const pg = await api.createSession({ type: 'playground' });
  console.log('playground', pg.type, pg.state);
  st.adopt(pg);
  for (let i = 0; i < 8; i++) { await sleep(700); console.log(i, st.session.state, st.logs.length, st.mode); }
  console.log('store state', st.session.state, 'logs', st.logs.length, 'mode', st.mode);
  st.stop();
  await api.remove(pg.id);
}
main().then(() => process.exit(0), (e) => { console.error('FAIL', e); process.exit(1); });
