// Uses node:test when available (node >= 18, `node --test web/tests`); otherwise a tiny fallback runner
// so the same test files also run on old Node (`for f in web/tests/*.test.js; do node $f; done`).
import { createRequire } from 'module';
import assert from 'assert';

const require = createRequire(import.meta.url);
let nodeTest = null;
try { nodeTest = require('node:test'); } catch (e) { nodeTest = null; }

const queue = [];
let scheduled = false;
async function runAll() {
  let failed = 0;
  for (const t of queue) {
    try { await t.fn(); console.log(`ok   ${t.name}`); } catch (e) { failed++; console.log(`FAIL ${t.name}\n     ${e && e.stack ? e.stack.split('\n').slice(0, 4).join('\n     ') : e}`); }
  }
  console.log(`${queue.length - failed}/${queue.length} passed`);
  if (failed) process.exitCode = 1;
}

export function test(name, fn) {
  if (nodeTest) return (nodeTest.test || nodeTest)(name, fn);
  queue.push({ name, fn });
  if (!scheduled) { scheduled = true; setTimeout(runAll, 0); }
}
export { assert };

// Polyfill for old Node used by session.js tests.
if (!globalThis.AbortController) {
  globalThis.AbortController = class {
    constructor() { const ls = []; this.signal = { aborted: false, addEventListener: (_, f) => ls.push(f) }; this.abort = () => { this.signal.aborted = true; ls.forEach((f) => f()); }; }
  };
}
