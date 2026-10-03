"""Application factory."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import auth, errors, routes
from .catalog import Catalog
from .db import Database
from .service import SessionService
from .settings import VERSION, Settings

log = logging.getLogger("kops.app")
_DEFAULT_CATALOG = Path(__file__).resolve().parents[3] / "catalog" / "available.txt"


def make_catalog(settings: Settings, provider_name: str) -> Catalog:
    """available.txt applies to real providers; kind/fake run everything unless a file is set."""
    if settings.catalog_file:
        avail = Path(settings.catalog_file)
    elif provider_name in ("kind", "fake"):
        avail = None
    else:
        avail = _DEFAULT_CATALOG
    return Catalog(settings.scenarios_dir, avail).load()


def create_app(settings: Settings, provider, verifier_factory=None) -> FastAPI:
    if settings.auth_mode == "dev-header" and not settings.allow_dev_auth:
        raise RuntimeError("KOPS_AUTH_MODE=dev-header requires KOPS_ALLOW_DEV_AUTH=1")
    db = Database(settings.db_url)
    catalog = make_catalog(settings, provider.name)
    kw = {"verifier_factory": verifier_factory} if verifier_factory else {}
    service = SessionService(settings, db, provider, catalog, **kw)

    async def sweeper():
        while True:
            await asyncio.sleep(settings.sweep_interval_seconds)
            try:
                await asyncio.to_thread(service.sweep)
            except Exception:
                log.exception("sweeper pass failed")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await asyncio.to_thread(service.recover)
        task = asyncio.create_task(sweeper()) if settings.sweep_interval_seconds > 0 else None
        yield
        if task:
            task.cancel()
        service.shutdown()

    app = FastAPI(title="KOPS platform", version=VERSION, lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings, app.state.db, app.state.provider = settings, db, provider
    app.state.catalog, app.state.service, app.state.oauth = catalog, service, None
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, same_site="lax",
                       https_only=settings.oidc_redirect_uri.startswith("https://"),
                       max_age=14 * 24 * 3600, session_cookie="kops_session")
    errors.install(app)
    app.include_router(routes.router())
    app.include_router(routes.health_router())
    app.include_router(auth.router())
    if settings.web_dir.is_dir():     # mounted last so it never shadows the API
        app.mount("/", StaticFiles(directory=settings.web_dir, html=True), name="web")
    return app
