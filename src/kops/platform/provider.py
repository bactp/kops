"""Provider selection from KOPS_PROVIDER."""
from __future__ import annotations

from .settings import Settings


def make_provider(settings: Settings):
    if settings.provider == "kind":
        from ..providers.kind import KindProvider
        return KindProvider(max_sessions=settings.max_sessions or 2)
    if settings.provider == "fake":
        from ..providers.fake import FakeProvider
        return FakeProvider(max_sessions=settings.max_sessions or 4)
    if settings.provider == "kubevirt":
        try:
            from ..providers.kubevirt import KubeVirtProvider
        except ImportError as e:
            raise SystemExit(f"KOPS_PROVIDER=kubevirt but the KubeVirt provider is not available: {e}")
        return KubeVirtProvider()
    raise SystemExit(f"unknown KOPS_PROVIDER {settings.provider!r} (kubevirt|kind|fake)")
