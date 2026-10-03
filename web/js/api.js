// API client. Pure: all I/O goes through an injected fetch so it can be unit-tested.

export class ApiError extends Error {
  constructor(status, code, detail) {
    super(detail || code || `HTTP ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.code = code || 'error';
    this.detail = detail || '';
  }
}

export function createApi({ fetchImpl, onUnauthenticated = () => {}, base = '' } = {}) {
  const doFetch = fetchImpl || ((...a) => globalThis.fetch(...a));

  async function request(method, path, body) {
    const init = { method, credentials: 'same-origin', headers: { Accept: 'application/json' } };
    if (body !== undefined) {
      init.headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(body);
    }
    let res;
    try {
      res = await doFetch(base + path, init);
    } catch (e) {
      throw new ApiError(0, 'network', e && e.message ? e.message : 'network error');
    }
    let text = '';
    try { text = await res.text(); } catch { /* ignore */ }
    let data = null;
    if (text) { try { data = JSON.parse(text); } catch { data = null; } }
    if (res.status === 401) {
      onUnauthenticated();
      throw new ApiError(401, 'unauthenticated', 'Please sign in');
    }
    if (!res.ok) {
      throw new ApiError(res.status, (data && data.error) || 'error', (data && data.detail) || res.statusText || `HTTP ${res.status}`);
    }
    return data;
  }

  const q = (params) => {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries(params || {})) if (v !== undefined && v !== null && v !== '') p.set(k, String(v));
    const s = p.toString();
    return s ? `?${s}` : '';
  };
  const sid = (id) => `/api/sessions/${encodeURIComponent(id)}`;

  return {
    request,
    me: () => request('GET', '/api/me'),
    config: () => request('GET', '/api/config'),
    scenarios: (params) => request('GET', `/api/scenarios${q(params)}`),
    scenario: (id) => request('GET', `/api/scenarios/${encodeURIComponent(id)}`),
    listSessions: () => request('GET', '/api/sessions'),
    getSession: (id) => request('GET', sid(id)),
    createSession: (body) => request('POST', '/api/sessions', body),
    check: (id, wait = false) => request('POST', `${sid(id)}/check`, { wait }),
    hint: (id, n) => request('GET', `${sid(id)}/hints/${n}`),
    solution: (id) => request('POST', `${sid(id)}/solution`),
    next: (id, scenarioId) => request('POST', `${sid(id)}/next`, { scenario_id: scenarioId }),
    restart: (id) => request('POST', `${sid(id)}/restart`),
    extend: (id) => request('POST', `${sid(id)}/extend`),
    remove: (id) => request('DELETE', sid(id)),
    progress: () => request('GET', '/api/progress'),
    adminSessions: () => request('GET', '/api/admin/sessions'),
    adminDeleteSession: (id) => request('DELETE', `/api/admin/sessions/${encodeURIComponent(id)}`),
    adminUsers: () => request('GET', '/api/admin/users'),
    adminCapacity: () => request('GET', '/api/admin/capacity'),
  };
}
