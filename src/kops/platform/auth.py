"""Authentication: OIDC authorization code + PKCE (authlib), signed cookie session, dev header."""
from __future__ import annotations

import base64
import json
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from starlette.requests import HTTPConnection

from .db import Database, User, utcnow
from .errors import ApiError
from .settings import Settings

log = logging.getLogger("kops.auth")


def role_claims(userinfo: dict, access_token: str | None) -> set[str]:
    """Role names from the id token claims and (unverified, just received) access token."""
    claims = [userinfo]
    if access_token and access_token.count(".") == 2:
        try:
            body = access_token.split(".")[1]
            claims.append(json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))))
        except Exception:
            pass
    roles: set[str] = set()
    for c in claims:
        roles |= set(c.get("roles") or []) | set(c.get("groups") or [])
        roles |= set((c.get("realm_access") or {}).get("roles") or [])
    return roles


def upsert_user(db: Database, cfg: Settings, username: str, email: str = "", subject: str | None = None,
                roles: set[str] | None = None, force_admin: bool = False) -> User:
    admin = force_admin or username in cfg.admin_users or bool(
        cfg.oidc_admin_role and cfg.oidc_admin_role in (roles or set()))
    with db.session() as s:
        u = s.scalar(select(User).where(User.username == username))
        if u is None:
            u = User(username=username, email=email, subject=subject, is_admin=admin)
            s.add(u)
        else:
            u.last_seen_at = utcnow()
            u.is_admin = admin
            if email:
                u.email = email
        s.commit()
        return u


def current_user(conn: HTTPConnection) -> User:
    """FastAPI dependency (HTTP and WebSocket): the authenticated user or 401."""
    cfg: Settings = conn.app.state.settings
    db: Database = conn.app.state.db
    if cfg.auth_mode == "dev-header":
        name = conn.headers.get("x-dev-user")
        if name:
            return upsert_user(db, cfg, name, f"{name}@dev.local",
                               force_admin=conn.headers.get("x-dev-admin") == "1")
    uid = conn.session.get("uid") if "session" in conn.scope else None
    if uid:
        with db.session() as s:
            u = s.get(User, uid)
            if u:
                u.last_seen_at = utcnow()
                u.is_admin = u.is_admin or u.username in cfg.admin_users
                s.commit()
                return u
    raise ApiError("unauthenticated", "login required")


def require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise ApiError("forbidden", "admin only")
    return user


def build_oauth(cfg: Settings):
    from authlib.integrations.starlette_client import OAuth
    oauth = OAuth()
    kw = {"scope": "openid profile email", "code_challenge_method": "S256"}
    if not cfg.oidc_client_secret:
        kw["token_endpoint_auth_method"] = "none"
    oauth.register("oidc", client_id=cfg.oidc_client_id, client_secret=cfg.oidc_client_secret or None,
                   server_metadata_url=cfg.oidc_issuer.rstrip("/") + "/.well-known/openid-configuration",
                   client_kwargs=kw)
    return oauth


def router() -> APIRouter:
    r = APIRouter(prefix="/auth")

    def _oauth(request: Request):
        cfg: Settings = request.app.state.settings
        if not (cfg.oidc_issuer and cfg.oidc_client_id):
            raise ApiError("provider_error", "OIDC is not configured")
        if getattr(request.app.state, "oauth", None) is None:
            request.app.state.oauth = build_oauth(cfg)
        return request.app.state.oauth.oidc

    @r.get("/login")
    async def login(request: Request):
        cfg: Settings = request.app.state.settings
        client = _oauth(request)
        return await client.authorize_redirect(request, cfg.oidc_redirect_uri or str(request.url_for("callback")))

    @r.get("/callback", name="callback")
    async def callback(request: Request):
        cfg: Settings = request.app.state.settings
        client = _oauth(request)
        try:
            token = await client.authorize_access_token(request)
        except Exception as e:
            log.warning("OIDC callback failed: %s", type(e).__name__)
            raise ApiError("unauthenticated", "login failed")
        info = dict(token.get("userinfo") or {})
        username = info.get("preferred_username") or info.get("email") or info.get("sub")
        if not username:
            raise ApiError("unauthenticated", "the identity provider returned no username")
        u = upsert_user(request.app.state.db, cfg, username, info.get("email", ""), info.get("sub"),
                        role_claims(info, token.get("access_token")))
        request.session.clear()
        request.session["uid"] = u.id
        return RedirectResponse("/", status_code=302)

    @r.get("/logout")
    async def logout(request: Request):
        """End the platform session AND the identity provider's SSO session. Clearing only our cookie left the
        Keycloak session alive, so the next visit logged the same user straight back in and a different account
        could not even be registered ("already_logged_in")."""
        from urllib.parse import urlencode
        cfg: Settings = request.app.state.settings
        request.session.clear()
        if cfg.oidc_issuer and cfg.oidc_client_id:
            home = (cfg.oidc_redirect_uri.rsplit("/auth/callback", 1)[0] if cfg.oidc_redirect_uri
                    else str(request.base_url).rstrip("/")) + "/"
            query = urlencode({"client_id": cfg.oidc_client_id, "post_logout_redirect_uri": home})
            return RedirectResponse(f"{cfg.oidc_issuer.rstrip('/')}/protocol/openid-connect/logout?{query}",
                                    status_code=302)
        return RedirectResponse("/", status_code=302)

    return r
