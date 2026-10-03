import { test, assert } from './harness.js';
import { SSEParser, parseEvent, streamEvents } from '../js/sse.js';
import { encodeInput, encodeResize, decodeFrame, terminalUrl } from '../js/terminal.js';
import { renderMarkdown, escapeHtml } from '../js/markdown.js';
import { parseHash } from '../js/router.js';
import { SessionStore } from '../js/session.js';

test('SSE parser handles split chunks, CRLF, comments and multi-line data', () => {
  const p = new SSEParser();
  let out = p.feed(': keepalive\n\nevent: log\ndata: {"line":"a');
  assert.deepStrictEqual(out, []);
  out = out.concat(p.feed('"}\n\nevent: state\r\ndata: {"x":\r\ndata: 1}\r\n\r\n'));
  assert.deepStrictEqual(out.map((e) => e.event), ['log', 'state']);
  assert.deepStrictEqual(parseEvent(out[0]).data, { line: 'a' });
  assert.strictEqual(out[1].data, '{"x":\n1}');
  assert.strictEqual(parseEvent({ event: 'x', data: 'not json' }).data, null);
});

test('streamEvents reads a streamed body and reports events', async () => {
  const enc = (s) => new TextEncoder().encode(s);
  const chunks = [enc('event: log\ndata: {"line":"hi"}\n'), enc('\nevent: state\ndata: {"state":"ACTIVE"}\n\n')];
  const fetchImpl = async () => ({ ok: true, status: 200, body: { getReader: () => ({ read: async () => (chunks.length ? { done: false, value: chunks.shift() } : { done: true }) }) } });
  const got = [];
  await streamEvents('/x', { fetchImpl, onEvent: (e) => got.push(e) });
  assert.deepStrictEqual(got.map((e) => e.event + ':' + JSON.stringify(e.data)), ['log:{"line":"hi"}', 'state:{"state":"ACTIVE"}']);
  await assert.rejects(() => streamEvents('/x', { fetchImpl: async () => ({ ok: false, status: 401 }), onEvent() {} }));
});

test('terminal frames match the contract', () => {
  assert.deepStrictEqual(JSON.parse(encodeInput('ls\r')), { t: 'i', d: 'ls\r' });
  assert.deepStrictEqual(JSON.parse(encodeResize(120, 32)), { t: 'r', c: 120, r: 32 });
  assert.deepStrictEqual(decodeFrame('{"t":"o","d":"hello"}'), { type: 'output', data: 'hello' });
  assert.deepStrictEqual(decodeFrame('{"t":"x","code":0}'), { type: 'exit', code: 0 });
  assert.strictEqual(decodeFrame('nope'), null);
  assert.strictEqual(decodeFrame('{"t":"zzz"}'), null);
  assert.strictEqual(terminalUrl('s_1', 'cp-1', 2, { protocol: 'https:', host: 'kops.example' }), 'wss://kops.example/api/sessions/s_1/terminal?target=cp-1&tab=2');
  assert.strictEqual(terminalUrl('s_1', 'base', 1, { protocol: 'http:', host: 'localhost:8099' }).slice(0, 5), 'ws://');
});

test('markdown escapes HTML and renders structure', () => {
  const html = renderMarkdown('# Title\n\nHello <script>alert(1)</script> `a<b` **bold**\n\n- one\n- two\n\n1. x\n2. y\n\n```sh\nkubectl get <pods>\n```\n[ok](https://k8s.io) [bad](javascript:alert(1))');
  assert.ok(!html.includes('<script>'));
  assert.ok(html.includes('&lt;script&gt;'));
  assert.ok(html.includes('<h2>Title</h2>'));
  assert.ok(html.includes('<code>a&lt;b</code>'));
  assert.ok(html.includes('<strong>bold</strong>'));
  assert.ok(html.includes('<ul><li>one</li><li>two</li></ul>'));
  assert.ok(html.includes('<ol><li>x</li><li>y</li></ol>'));
  assert.ok(html.includes('<pre><code>kubectl get &lt;pods&gt;</code></pre>'));
  assert.ok(html.includes('<a href="https://k8s.io" target="_blank" rel="noopener noreferrer">ok</a>'));
  assert.ok(!html.includes('href="javascript'));
  assert.strictEqual(escapeHtml('<"&\'>'), '&lt;&quot;&amp;&#39;&gt;');
  assert.strictEqual(renderMarkdown(null), '');
});

test('router parses hashes with fallback', () => {
  const r = ['practice', 'playground', 'progress'];
  assert.strictEqual(parseHash('#/progress', r, 'practice'), 'progress');
  assert.strictEqual(parseHash('#/admin', r, 'practice'), 'practice');
  assert.strictEqual(parseHash('', r, 'practice'), 'practice');
  assert.strictEqual(parseHash('#/practice?x=1', r, 'practice'), 'practice');
});

test('SessionStore falls back to polling when the stream drops, then stops at a final state', async () => {
  const states = [{ id: 's1', state: 'PROVISIONING' }, { id: 's1', state: 'ACTIVE' }, { id: 's1', state: 'INVALID', message: 'boom' }];
  let polls = 0;
  const api = { getSession: async () => states[Math.min(1 + polls++, 2)], listSessions: async () => [{ id: 's1', state: 'PROVISIONING' }] };
  let streams = 0;
  const stream = async (url, { onEvent }) => { streams++; onEvent({ event: 'log', data: { ts: 't', line: 'hello' } }); onEvent({ event: 'state', data: states[0] }); throw new Error('dropped'); };
  const store = new SessionStore(api, { stream, sleep: async () => {}, pollMs: 1, pollsBeforeRetry: 5 });
  const seenModes = [];
  store.subscribe((k) => { if (k === 'mode') seenModes.push(store.mode); });
  const s = await store.resume();
  assert.strictEqual(s.id, 's1');
  await new Promise((r) => setTimeout(r, 30));
  assert.strictEqual(streams, 1);
  assert.ok(seenModes.includes('poll'));
  assert.strictEqual(store.session.state, 'INVALID');
  assert.strictEqual(store.logs.length, 1);
  assert.strictEqual(store.mode, 'idle');
});

test('SessionStore.resume ignores ended sessions', async () => {
  const api = { listSessions: async () => [{ id: 'a', state: 'ENDED' }, { id: 'b', state: 'DESTROYED' }] };
  const store = new SessionStore(api, { stream: async () => {}, sleep: async () => {} });
  assert.strictEqual(await store.resume(), null);
  assert.strictEqual(store.session, null);
});
