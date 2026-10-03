import { test, assert } from './harness.js';
import * as S from '../js/state.js';

const list = [
  { id: 'a', title: 'Service endpoints', difficulty: 2, tags: ['service'], status: 'solved', profiles: { cka: { domain: 'troubleshooting' }, ckad: { domain: 'services-networking' } } },
  { id: 'b', title: 'Projected volume', difficulty: 1, tags: ['volume'], status: 'none', profiles: { ckad: { domain: 'configuration' } } },
  { id: 'c', title: 'Cordon node', difficulty: 3, tags: [], status: 'none', profiles: { cka: { domain: 'troubleshooting' } } },
];

test('state formatting and predicates', () => {
  assert.strictEqual(S.stateLabel('SETUP'), 'Setting up task');
  assert.strictEqual(S.stateLabel('WEIRD'), 'WEIRD');
  assert.ok(S.isBusy('CHECKING') && S.isBusy('RESETTING') && !S.isBusy('ACTIVE'));
  assert.ok(S.canUseTerminal('ACTIVE') && S.canUseTerminal('CHECKING') && !S.canUseTerminal('SETUP'));
  assert.ok(S.canAct('ACTIVE') && !S.canAct('CHECKING'));
  assert.ok(S.isFinal('INVALID') && S.isFinal('DESTROYED') && !S.isFinal('ENDED'));
});

test('timeline marks done/current/todo and failed', () => {
  const t = S.timeline('SETUP').map((x) => x.status);
  assert.deepStrictEqual(t, ['done', 'done', 'current', 'todo', 'todo']);
  assert.ok(S.timeline('ACTIVE').every((x) => x.status === 'done'));
  assert.strictEqual(S.timeline('INVALID').pop().status, 'failed');
});

test('countdown formatting', () => {
  const now = Date.parse('2026-10-03T00:00:00Z');
  assert.strictEqual(S.formatCountdown('2026-10-03T00:12:05Z', now), '12:05');
  assert.strictEqual(S.formatCountdown('2026-10-03T01:02:03Z', now), '1:02:03');
  assert.strictEqual(S.formatCountdown('2026-10-02T23:59:00Z', now), 'expired');
  assert.strictEqual(S.formatCountdown('garbage', now), '--:--');
});

test('difficulty dots and durations', () => {
  assert.strictEqual(S.difficultyDots(2), '●●○');
  assert.strictEqual(S.difficultyDots(9), '●●●');
  assert.strictEqual(S.formatDuration(45), '45s');
  assert.strictEqual(S.formatDuration(812), '13m 32s');
  assert.strictEqual(S.formatDuration(3720), '1h 02m');
});

test('filters: profile, domain, difficulty, free text', () => {
  const ids = (f) => S.filterScenarios(list, f).map((x) => x.id);
  assert.deepStrictEqual(ids({}), ['a', 'b', 'c']);
  assert.deepStrictEqual(ids({ profile: 'cka' }), ['a', 'c']);
  assert.deepStrictEqual(ids({ profile: 'ckad' }), ['a', 'b']);
  assert.deepStrictEqual(ids({ profile: 'cka', domain: 'services-networking' }), []);
  assert.deepStrictEqual(ids({ domain: 'services-networking' }), ['a']);
  assert.deepStrictEqual(ids({ difficulty: '3' }), ['c']);
  assert.deepStrictEqual(ids({ q: 'VOLUME' }), ['b']);
  assert.deepStrictEqual(ids({ q: 'node cordon' }), ['c']);
  assert.deepStrictEqual(S.domainsOf(list, 'cka'), ['troubleshooting']);
  assert.deepStrictEqual(S.domainsOf(list), ['configuration', 'services-networking', 'troubleshooting']);
});

test('progress summary computes totals and percentages', () => {
  const p = { summary: { cka: { troubleshooting: { solved: 2, assisted: 1, attempted: 1, total: 10 } }, ckad: {} } };
  const r = S.summarizeProgress(p);
  assert.strictEqual(r.rows.length, 1);
  assert.deepStrictEqual([r.rows[0].solvedPct, r.rows[0].assistedPct, r.rows[0].attemptedPct], [20, 10, 10]);
  assert.deepStrictEqual(r.totals, { solved: 2, assisted: 1, attempted: 1, total: 10 });
  assert.deepStrictEqual(S.summarizeProgress(null).rows, []);
});

test('hint state machine reveals one at a time', () => {
  const h = new S.HintState(3);
  assert.strictEqual(h.nextHint, 1);
  assert.ok(!h.addHint(2, 'skip'));
  assert.ok(h.addHint(1, 'one'));
  assert.strictEqual(h.nextHint, 2);
  h.addHint(2, 'two'); h.addHint(3, 'three');
  assert.ok(!h.canReveal());
  assert.strictEqual(h.revealed, 3);
  const g = new S.HintState(3);
  g.addHint(1, 'x'); g.hintsExhausted();
  assert.ok(!g.canReveal());
});

test('solution requires confirmation', () => {
  const h = new S.HintState(3);
  assert.strictEqual(h.confirmSolution(), 'hidden'); // cannot skip the confirm step
  assert.strictEqual(h.askSolution(), 'confirming');
  assert.strictEqual(h.cancelSolution(), 'hidden');
  h.askSolution();
  assert.strictEqual(h.confirmSolution(), 'loading');
  h.solutionLoaded('## sol');
  assert.strictEqual(h.solutionStatus, 'shown');
  assert.strictEqual(h.solution, '## sol');
  const f = new S.HintState(3); f.askSolution(); f.confirmSolution(); f.solutionFailed();
  assert.strictEqual(f.solutionStatus, 'hidden');
});

test('friendly error messages', () => {
  assert.match(S.friendlyError({ code: 'quota_exceeded' }), /resume it or end it/i);
  assert.match(S.friendlyError({ code: 'capacity_exceeded' }), /lab is full/i);
  assert.match(S.friendlyError({ code: 'provider_error', detail: 'kubevirt down' }), /kubevirt down/);
  assert.match(S.friendlyError({ code: 'network', detail: 'ECONNREFUSED' }), /Cannot reach/);
  assert.ok(S.isRetryable({ code: 'network' }) && !S.isRetryable({ code: 'quota_exceeded', status: 409 }));
});

test('memory percent is clamped', () => {
  assert.strictEqual(S.memPct(9000, 15000), 60);
  assert.strictEqual(S.memPct(20000, 15000), 100);
  assert.strictEqual(S.memPct(1, 0), 0);
});
