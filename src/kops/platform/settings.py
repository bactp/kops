"""Platform settings, read from the environment."""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from .. import config

VERSION = "0.1.0"


def _csv(v: str | None) -> list[str]:
    return [x.strip() for x in (v or "").split(",") if x.strip()]


def _flag(v: str | None) -> bool:
    return (v or "").strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    db_url: str = "sqlite:///./kops.db"
    provider: str = "kubevirt"
    session_secret: str = ""
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""            # empty: public client with PKCE
    oidc_redirect_uri: str = ""
    admin_users: list[str] = field(default_factory=list)
    oidc_admin_role: str = ""
    max_sessions: int = 0                   # 0: whatever the provider reports
    sessions_per_user: int = 1
    practice_ttl_minutes: int = 120
    playground_ttl_minutes: int = 120
    max_extensions: int = 2
    scenarios_dir: Path = config.SCENARIOS_DIR
    catalog_file: str | None = None         # None: catalog/available.txt, enforced for real providers only
    web_dir: Path = config.ROOT / "web"
    allow_dev_auth: bool = False
    auth_mode: str = "oidc"                 # oidc | dev-header
    sweep_interval_seconds: float = 30.0    # 0 disables the background sweeper
    sse_poll_seconds: float = 0.5
    reset_timeout_seconds: float = 120.0
    reset_poll_seconds: float = 2.0
    features: dict = field(default_factory=lambda: {"playground": True, "mock_exam": False,
                                                    "docs": False, "editor": False})

    def __post_init__(self):
        if not self.session_secret:   # sessions then do not survive a restart
            self.session_secret = secrets.token_urlsafe(32)

    @classmethod
    def from_env(cls, env: dict | None = None) -> "Settings":
        e = os.environ if env is None else env
        s = cls(
            db_url=e.get("KOPS_DB_URL", "sqlite:///./kops.db"),
            provider=e.get("KOPS_PROVIDER", "kubevirt"),
            session_secret=e.get("KOPS_SESSION_SECRET", ""),
            oidc_issuer=e.get("KOPS_OIDC_ISSUER", ""),
            oidc_client_id=e.get("KOPS_OIDC_CLIENT_ID", ""),
            oidc_client_secret=e.get("KOPS_OIDC_CLIENT_SECRET", ""),
            oidc_redirect_uri=e.get("KOPS_OIDC_REDIRECT_URI", ""),
            admin_users=_csv(e.get("KOPS_ADMIN_USERS")),
            oidc_admin_role=e.get("KOPS_OIDC_ADMIN_ROLE", ""),
            max_sessions=int(e.get("KOPS_MAX_SESSIONS", "0") or 0),
            sessions_per_user=int(e.get("KOPS_SESSIONS_PER_USER", "1")),
            practice_ttl_minutes=int(e.get("KOPS_PRACTICE_TTL_MINUTES", "120")),
            playground_ttl_minutes=int(e.get("KOPS_PLAYGROUND_TTL_MINUTES", "120")),
            max_extensions=int(e.get("KOPS_MAX_EXTENSIONS", "2")),
            scenarios_dir=Path(e.get("KOPS_SCENARIOS_DIR", str(config.SCENARIOS_DIR))),
            catalog_file=e.get("KOPS_CATALOG_FILE") or None,
            web_dir=Path(e.get("KOPS_WEB_DIR", str(config.ROOT / "web"))),
            allow_dev_auth=_flag(e.get("KOPS_ALLOW_DEV_AUTH")),
            auth_mode=e.get("KOPS_AUTH_MODE", "oidc"),
            sweep_interval_seconds=float(e.get("KOPS_SWEEP_INTERVAL_SECONDS", "30")),
        )
        return s
