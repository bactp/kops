// Pure helpers: state formatting, filters, progress summary, hint/solution state machine.

export const PROVISION_STEPS = ['REQUESTED', 'PROVISIONING', 'SETUP', 'CONFIRMING', 'ACTIVE'];
const BUSY = new Set(['REQUESTED', 'PROVISIONING', 'SETUP', 'CONFIRMING', 'CHECKING', 'RESETTING']);
const GONE = new Set(['ENDED', 'DESTROYED']);
const LABELS = {
  REQUESTED: 'Requested', PROVISIONING: 'Provisioning', SETUP: 'Setting up task', CONFIRMING: 'Verifying setup',
  ACTIVE: 'Active', CHECKING: 'Checking', RESETTING: 'Resetting', ENDED: 'Ended', DESTROYED: 'Destroyed', INVALID: 'Invalid',
};

export const stateLabel = (s) => LABELS[s] || s || 'Unknown';
export const isBusy = (s) => BUSY.has(s);
export const isGone = (s) => GONE.has(s);
export const isFinal = (s) => s === 'DESTROYED' || s === 'INVALID';
export const canUseTerminal = (s) => s === 'ACTIVE' || s === 'CHECKING';
export const canAct = (s) => s === 'ACTIVE';
export const isLive = (session) => !!session && !GONE.has(session.state);

// Timeline entries: [{state,label,status:'done'|'current'|'todo'|'failed'}]
export function timeline(state) {
  if (state === 'INVALID') return PROVISION_STEPS.slice(0, 4).map((s) => ({ state: s, label: stateLabel(s), status: 'todo' }))
    .concat([{ state: 'INVALID', label: 'Invalid', status: 'failed' }]);
  const idx = PROVISION_STEPS.indexOf(state);
  const cur = idx >= 0 ? idx : PROVISION_STEPS.length - 1;
  return PROVISION_STEPS.map((s, i) => ({ state: s, label: stateLabel(s), status: i < cur ? 'done' : i === cur ? (s === 'ACTIVE' ? 'done' : 'current') : 'todo' }));
}

export function formatCountdown(expiresAt, now = Date.now()) {
  const t = Date.parse(expiresAt);
  if (Number.isNaN(t)) return '--:--';
  const sec = Math.floor((t - now) / 1000);
  if (sec <= 0) return 'expired';
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
  const p = (n) => String(n).padStart(2, '0');
  return h > 0 ? `${h}:${p(m)}:${p(s)}` : `${p(m)}:${p(s)}`;
}

export const difficultyDots = (n, max = 3) => '●'.repeat(Math.max(0, Math.min(max, n | 0))) + '○'.repeat(Math.max(0, max - Math.max(0, Math.min(max, n | 0))));

const STATUS_LABELS = { none: 'Not tried', attempted: 'Attempted', solved: 'Solved', solved_assisted: 'Solved (assisted)' };
export const statusLabel = (s) => STATUS_LABELS[s] || s || 'Not tried';

export function formatDuration(seconds) {
  const s = Math.max(0, Math.round(seconds || 0));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ${String(s % 60).padStart(2, '0')}s`;
  return `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, '0')}m`;
}

// ---- scenario filters ------------------------------------------------------
export function scenarioDomain(sc, profile) {
  const p = sc.profiles || {};
  if (profile && p[profile]) return p[profile].domain;
  const first = Object.values(p)[0];
  return first ? first.domain : '';
}

export function domainsOf(list, profile) {
  const set = new Set();
  for (const sc of list) {
    for (const [name, v] of Object.entries(sc.profiles || {})) if (!profile || profile === name) set.add(v.domain);
  }
  return [...set].sort();
}

export function filterScenarios(list, f = {}) {
  const q = (f.q || '').trim().toLowerCase();
  return list.filter((sc) => {
    const profiles = sc.profiles || {};
    if (f.profile && !profiles[f.profile]) return false;
    if (f.domain) {
      const inDomain = f.profile ? (profiles[f.profile] || {}).domain === f.domain : Object.values(profiles).some((p) => p.domain === f.domain);
      if (!inDomain) return false;
    }
    if (f.difficulty && Number(sc.difficulty) !== Number(f.difficulty)) return false;
    if (f.status && sc.status !== f.status) return false;
    if (q) {
      const hay = [sc.title, sc.id, ...(sc.tags || []), ...Object.values(profiles).map((p) => p.domain)].join(' ').toLowerCase();
      if (!q.split(/\s+/).every((w) => hay.includes(w))) return false;
    }
    return true;
  });
}

// ---- progress --------------------------------------------------------------
export function summarizeProgress(progress) {
  const rows = [];
  const totals = { solved: 0, assisted: 0, attempted: 0, total: 0 };
  const summary = (progress && progress.summary) || {};
  for (const profile of Object.keys(summary).sort()) {
    for (const domain of Object.keys(summary[profile] || {}).sort()) {
      const c = summary[profile][domain];
      const total = c.total || 0;
      const pct = (n) => (total > 0 ? Math.round(((n || 0) / total) * 100) : 0);
      rows.push({ profile, domain, solved: c.solved || 0, assisted: c.assisted || 0, attempted: c.attempted || 0, total,
        solvedPct: pct(c.solved), assistedPct: pct(c.assisted), attemptedPct: pct(c.attempted) });
      totals.solved += c.solved || 0; totals.assisted += c.assisted || 0; totals.attempted += c.attempted || 0; totals.total += total;
    }
  }
  return { rows, totals };
}

// ---- hints and solution ----------------------------------------------------
export class HintState {
  constructor(hintCount = 3) {
    this.hintCount = hintCount;
    this.hints = [];            // revealed texts, index 0 = hint 1
    this.solution = null;       // markdown once shown
    this.solutionStatus = 'hidden'; // hidden | confirming | loading | shown
  }
  get revealed() { return this.hints.length; }
  get nextHint() { return this.hints.length < this.hintCount ? this.hints.length + 1 : null; }
  canReveal() { return this.nextHint !== null; }
  addHint(n, text) {
    if (n === this.hints.length + 1) { this.hints.push(text); return true; }
    if (n >= 1 && n <= this.hints.length) { this.hints[n - 1] = text; return true; }
    return false; // out of order
  }
  hintsExhausted() { this.hintCount = this.hints.length; }
  askSolution() { if (this.solutionStatus === 'hidden') this.solutionStatus = 'confirming'; return this.solutionStatus; }
  cancelSolution() { if (this.solutionStatus === 'confirming') this.solutionStatus = 'hidden'; return this.solutionStatus; }
  confirmSolution() { if (this.solutionStatus === 'confirming') this.solutionStatus = 'loading'; return this.solutionStatus; }
  solutionLoaded(md) { this.solution = md; this.solutionStatus = 'shown'; }
  solutionFailed() { if (this.solutionStatus === 'loading') this.solutionStatus = 'hidden'; }
}

// ---- errors ----------------------------------------------------------------
export function friendlyError(err) {
  const code = err && err.code;
  const detail = (err && (err.detail || err.message)) || '';
  switch (code) {
    case 'quota_exceeded': return 'You already have an active session (or hit a limit). Resume it or end it first.';
    case 'capacity_exceeded': return 'The lab is full. Try again in a few minutes.';
    case 'provider_error': return `The sandbox provider reported an error${detail ? `: ${detail}` : ''}.`;
    case 'network': return `Cannot reach the server${detail ? ` (${detail})` : ''}.`;
    case 'forbidden': return 'You are not allowed to do that.';
    case 'not_found': return 'Not found. It may have expired or been deleted.';
    case 'bad_state': return `The session is not in a state that allows this${detail ? `: ${detail}` : ''}.`;
    default: return detail || 'Something went wrong.';
  }
}

export const isRetryable = (err) => !!err && (err.code === 'network' || err.code === 'provider_error' || err.status >= 500);

export const memPct = (requested, allocatable) => (allocatable > 0 ? Math.min(100, Math.round((requested / allocatable) * 100)) : 0);
