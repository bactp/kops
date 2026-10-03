"""Database models (SQLAlchemy 2). SQLite by default; nothing here is SQLite specific."""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import (Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


def utcnow() -> datetime:
    """Naive UTC: every timestamp in the database is UTC without tzinfo."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt: datetime | None) -> str | None:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None


def new_id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    subject: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str] = mapped_column(String(320), default="")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SessionRow(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(16))
    state: Mapped[str] = mapped_column(String(16), index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    rev: Mapped[int] = mapped_column(Integer, default=0)           # bumped on every change (SSE)
    scenario_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    params_json: Mapped[str] = mapped_column(Text, default="{}")
    reset_mode: Mapped[str | None] = mapped_column(String(8), nullable=True)
    workers: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    extensions: Mapped[int] = mapped_column(Integer, default=0)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    attempt_mark: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hints_read_json: Mapped[str] = mapped_column(Text, default="[]")
    solution_viewed: Mapped[bool] = mapped_column(Boolean, default=False)
    last_check_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sandbox_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    baselines_json: Mapped[str] = mapped_column(Text, default="{}")    # verifier guard digests
    pristine_json: Mapped[str | None] = mapped_column(Text, nullable=True)   # api-reset baseline


class SessionEvent(Base):
    __tablename__ = "session_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    line: Mapped[str] = mapped_column(Text)


class CheckRow(Base):
    __tablename__ = "checks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    scenario_id: Mapped[str] = mapped_column(String(200))
    attempt: Mapped[int] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(8))
    criteria_json: Mapped[str] = mapped_column(Text)
    required_passed: Mapped[int] = mapped_column(Integer)
    required_total: Mapped[int] = mapped_column(Integer)
    seconds: Mapped[float] = mapped_column(Float)
    solution_viewed: Mapped[bool] = mapped_column(Boolean, default=False)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ProgressRow(Base):
    __tablename__ = "progress"
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    checks: Mapped[int] = mapped_column(Integer, default=0)
    solved_clean: Mapped[bool] = mapped_column(Boolean, default=False)
    solved_assisted: Mapped[bool] = mapped_column(Boolean, default=False)
    best_outcome: Mapped[str | None] = mapped_column(String(8), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    seconds_spent: Mapped[int] = mapped_column(Integer, default=0)


class Database:
    def __init__(self, url: str):
        kw: dict = {"future": True, "pool_pre_ping": True}
        if url.startswith("sqlite"):
            kw["connect_args"] = {"check_same_thread": False, "timeout": 30}
            if ":memory:" in url or url in ("sqlite://", "sqlite:///"):
                kw["poolclass"] = StaticPool
        self.engine = create_engine(url, **kw)
        self._factory = sessionmaker(self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self):
        s = self._factory()
        try:
            yield s
        finally:
            s.close()
