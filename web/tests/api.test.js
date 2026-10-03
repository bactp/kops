import { test, assert } from './harness.js';
import { createApi, ApiError } from '../js/api.js';

const resp = (status, body) => ({ status, ok: status < 400, statusText: 'x', text: async () => (body === undefined ? '' : JSON.stringify(body)) });

test('GET parses JSON and sends credentials', async () => {
  const calls = [];
  const api = createApi({ fetchImpl: async (u, i) => { calls.push([u, i]); return resp(200, { username: 'alice' }); } });
  assert.deepStrictEqual(await api.me(), { username: 'alice' });
  assert.strictEqual(calls[0][0], '/api/me');
  assert.strictEqual(calls[0][1].credentials, 'same-origin');
});

test('POST sends JSON body', async () => {
  let seen;
  const api = createApi({ fetchImpl: async (u, i) => { seen = [u, i]; return resp(201, { id: 's_1' }); } });
  await api.createSession({ type: 'practice', scenario_id: 'x', seed: null });
  assert.strictEqual(seen[1].method, 'POST');
  assert.deepStrictEqual(JSON.parse(seen[1].body), { type: 'practice', scenario_id: 'x', seed: null });
  assert.strictEqual(seen[1].headers['Content-Type'], 'application/json');
});

test('401 calls onUnauthenticated and throws', async () => {
  let called = 0;
  const api = createApi({ fetchImpl: async () => resp(401, { error: 'unauthenticated' }), onUnauthenticated: () => called++ });
  await assert.rejects(() => api.me(), (e) => e instanceof ApiError && e.status === 401);
  assert.strictEqual(called, 1);
});

test('error body becomes ApiError code and detail', async () => {
  const api = createApi({ fetchImpl: async () => resp(409, { error: 'quota_exceeded', detail: 'one at a time' }) });
  await assert.rejects(() => api.createSession({ type: 'playground' }), (e) => e.code === 'quota_exceeded' && e.detail === 'one at a time' && e.status === 409);
});

test('network failure becomes code "network"', async () => {
  const api = createApi({ fetchImpl: async () => { throw new Error('boom'); } });
  await assert.rejects(() => api.config(), (e) => e.code === 'network' && e.status === 0);
});

test('202 with empty body returns null; query strings skip empty params', async () => {
  const urls = [];
  const api = createApi({ fetchImpl: async (u) => { urls.push(u); return resp(202); } });
  assert.strictEqual(await api.remove('s/1'), null);
  await api.scenarios({ profile: 'cka', q: '', difficulty: 2 });
  assert.strictEqual(urls[0], '/api/sessions/s%2F1');
  assert.strictEqual(urls[1], '/api/scenarios?profile=cka&difficulty=2');
});

test('check, hint, next, restart, extend hit contract paths', async () => {
  const seen = [];
  const api = createApi({ fetchImpl: async (u, i) => { seen.push(`${i.method} ${u} ${i.body || ''}`); return resp(200, {}); } });
  await api.check('s_1', true); await api.hint('s_1', 2); await api.next('s_1', 'sc'); await api.restart('s_1'); await api.extend('s_1'); await api.solution('s_1');
  assert.deepStrictEqual(seen, ['POST /api/sessions/s_1/check {"wait":true}', 'GET /api/sessions/s_1/hints/2 ', 'POST /api/sessions/s_1/next {"scenario_id":"sc"}',
    'POST /api/sessions/s_1/restart ', 'POST /api/sessions/s_1/extend ', 'POST /api/sessions/s_1/solution ']);
});
