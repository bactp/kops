# KOPS Platform API (v0.1 contract)

This is the contract between the platform backend (`src/kops/platform/`) and the web dashboard (`web/`). Both are built against it in parallel. Change it only together with both sides.

- Base path `/api`, JSON in and out, UTF-8, timestamps ISO 8601 UTC (`2026-10-03T07:30:00Z`).
- **Auth.** Browser login uses OIDC (authorization code with PKCE) against the bundled Keycloak. The backend sets a signed, HTTP-only session cookie. An unauthenticated API call returns `401 {"error":"unauthenticated"}`; the browser UI then navigates to `/auth/login`. `/auth/login`, `/auth/callback`, `/auth/logout` are plain HTTP redirects, not JSON. For automated tests only, `KOPS_AUTH_MODE=dev-header` accepts `X-Dev-User: <name>` (and `X-Dev-Admin: 1`); it is refused unless `KOPS_ALLOW_DEV_AUTH=1`.
- Errors: `{"error": "<code>", "detail": "<human text>"}` with a suitable status. Codes used: `unauthenticated` 401, `forbidden` 403, `not_found` 404, `quota_exceeded` 409, `capacity_exceeded` 503, `bad_state` 409, `invalid_request` 422, `provider_error` 502.
- Every resource is owned. A non-admin user sees and acts only on their own sessions and progress.

## Identity and configuration

`GET /api/me` → `{"id":"<uuid>","username":"alice","email":"a@x","is_admin":false}`

`GET /api/config` →
```json
{"version":"0.1.0","provider":"kubevirt",
 "quotas":{"active_sessions_per_user":1,"practice_ttl_minutes":120,"playground_ttl_minutes":120,"max_extensions":2},
 "features":{"playground":true,"mock_exam":false,"docs":false,"editor":false}}
```
The dashboard hides features that are `false`.

## Scenarios (the catalogue)

`GET /api/scenarios?profile=cka|ckad&domain=<id>&difficulty=1|2|3&q=<text>` →
```json
[{"id":"kops-net-service-endpoint-repair-001","title":"Restore traffic to a web Service that has no endpoints",
  "difficulty":2,"tags":["service","endpoints"],
  "profiles":{"cka":{"domain":"troubleshooting","competency":"CKA-TRB-05"},"ckad":{"domain":"services-networking","competency":"CKAD-SNW-02"}},
  "available":true,"availability_note":null,"reset":"api",
  "status":"none"}]
```
`status` is the caller's progress: `none | attempted | solved | solved_assisted`. A scenario the provider cannot run yet has `available:false` and a note (for example "validated on kind only"); the dashboard shows it greyed out.

`GET /api/scenarios/{id}` → the same object plus `"hint_count":3`. The task text is **not** returned here (it contains seeded names); it is only returned inside a session.

## Sessions

Session object:
```json
{"id":"s_3f9a1c","type":"practice","state":"ACTIVE","owner":"alice",
 "created_at":"…","expires_at":"…","extensions":0,
 "scenario_id":"kops-net-service-endpoint-repair-001",
 "task":{"title":"…","text_md":"…","domain":"troubleshooting","difficulty":2},
 "targets":[{"name":"base","role":"base"},{"name":"cp-1","role":"node"}],
 "hints_used":0,"solution_viewed":false,"attempt":1,
 "last_check":null,"reset":"api","message":null}
```
- `type`: `practice | playground`. `task` is `null` for a playground.
- `state`: `REQUESTED, PROVISIONING, SETUP, CONFIRMING, ACTIVE, CHECKING, RESETTING, ENDED, DESTROYED, INVALID`. `message` carries a human reason for `INVALID`.
- `targets` lists the hosts a terminal can open. `base` is the entry host; the candidate reaches `cp-1` (and workers) with `ssh` from `base`.

Endpoints:

| Method and path | Body | Result |
|---|---|---|
| `POST /api/sessions` | `{"type":"practice","scenario_id":"…","seed":null}` or `{"type":"playground"}` | `201` session in `REQUESTED`/`PROVISIONING`. `409 quota_exceeded` when the user already has an active session; `503 capacity_exceeded` when the provider has no room. |
| `GET /api/sessions` | | the caller's sessions, newest first (active ones first) |
| `GET /api/sessions/{id}` | | session |
| `GET /api/sessions/{id}/events` | | Server-Sent Events: `event: state` (data = session JSON), `event: log` (data `{"ts":"…","line":"…"}` provisioning log lines). The stream ends when the session is `DESTROYED` or `INVALID`. |
| `POST /api/sessions/{id}/check` | `{"wait":false}` | practice, state `ACTIVE`: runs the verifier. `{"outcome":"PASS|FAIL|INVALID","criteria":[{"id":"endpoints_count","required":true,"status":"pass|fail|error","evidence":"…"}],"required_passed":3,"required_total":4,"checked_at":"…","seconds":3.8}`. `wait:true` lets criteria with `settle` poll (up to 60 s). |
| `GET /api/sessions/{id}/hints/{n}` | | `n` = 1..3. `{"n":1,"text_md":"…"}`; increments `hints_used` the first time each hint is read. `404` if the scenario has fewer hints. |
| `POST /api/sessions/{id}/solution` | | `{"explanation_md":"…"}`; sets `solution_viewed` and marks the attempt assisted. |
| `POST /api/sessions/{id}/next` | `{"scenario_id":"…"}` | switches the session to another scenario: `api` reset when both scenarios allow it, otherwise a `vm` reset. Returns the session in `RESETTING`/`SETUP`. |
| `POST /api/sessions/{id}/restart` | | resets the current task to its initial state. |
| `POST /api/sessions/{id}/extend` | | playground or practice: adds the configured TTL if `extensions < max_extensions`, else `409 quota_exceeded`. |
| `DELETE /api/sessions/{id}` | | `202`; destroys the sandbox. |
| `GET /api/sessions/{id}/terminal` (WebSocket) | query `target=base&tab=1` | interactive shell, see below. |

### Terminal WebSocket

Text frames, JSON. Client to server: `{"t":"i","d":"<keystrokes>"}` input, `{"t":"r","c":120,"r":32}` resize (columns, rows). Server to client: `{"t":"o","d":"<terminal output>"}`, `{"t":"x","code":0}` on exit (the socket then closes). Only the session owner (or an admin) may connect. A tab is one pty; several tabs may be open at once (the dashboard opens one WebSocket per tab).

## Progress

`GET /api/progress` →
```json
{"scenarios":[{"scenario_id":"…","status":"solved_assisted","attempts":3,"best_outcome":"PASS","last_checked_at":"…","seconds_spent":812}],
 "summary":{"cka":{"troubleshooting":{"solved":2,"assisted":1,"attempted":1,"total":10}},"ckad":{}}}
```
Status rules: `attempted` = at least one CHECK but never PASS; `solved` = a PASS and the solution was not viewed; `solved_assisted` = a PASS or a finished attempt after the solution was viewed. Hints are counted and shown but do not change the status.

## Admin (requires `is_admin`)

- `GET /api/admin/sessions` → all sessions (with owner).
- `DELETE /api/admin/sessions/{id}` → destroy any session.
- `GET /api/admin/users` → `[{"id","username","email","created_at","last_seen_at","active_session":"s_…"|null,"sessions_total":N}]`.
- `GET /api/admin/capacity` → `{"provider":"kubevirt","max_sessions":2,"active_sessions":1,"nodes":[{"name":"kops-worker-1","memory_allocatable_mib":15000,"memory_requested_mib":9000}],"orphans":0}`.

## Health

`GET /healthz` → `200 {"status":"ok"}` (process up). `GET /readyz` → `200` when the database is reachable and the provider answers, else `503`.

## Session lifecycle (backend behaviour the UI relies on)

1. `POST /api/sessions` creates the row (`REQUESTED`), checks the quota and capacity, and starts provisioning in the background (`PROVISIONING`, `log` events as it goes).
2. Practice: after provisioning, the scenario setup runs (`SETUP`), the negative control is confirmed (`CONFIRMING`), then `ACTIVE`. Failure at any step is `INVALID` with a `message`, resources are destroyed.
3. `ACTIVE` ⇄ `CHECKING` on every CHECK. `RESETTING` during `next`, `restart`.
4. `ENDED` on delete or expiry, then `DESTROYED` once the sandbox is gone. A sweeper destroys sandboxes that have no session row or whose session expired.
