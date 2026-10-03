"""KOPS platform backend: FastAPI application, session service, terminal gateway."""
from .app import create_app
from .settings import Settings

__all__ = ["create_app", "Settings"]
