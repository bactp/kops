"""Logging out must end the identity provider's SSO session too, not only the platform cookie."""
from urllib.parse import parse_qs, urlparse

from conftest import Env


def test_logout_with_oidc_goes_through_the_provider_end_session_endpoint(tmp_path, scenarios):
    e = Env(tmp_path, scenarios, oidc_issuer="http://kc.example:30880/realms/kops", oidc_client_id="kops-web",
            oidc_redirect_uri="http://kops.example:30800/auth/callback")
    r = e.client.get("/auth/logout", follow_redirects=False)
    assert r.status_code == 302
    u = urlparse(r.headers["location"])
    assert f"{u.scheme}://{u.netloc}{u.path}" == "http://kc.example:30880/realms/kops/protocol/openid-connect/logout"
    q = parse_qs(u.query)
    assert q["client_id"] == ["kops-web"]
    assert q["post_logout_redirect_uri"] == ["http://kops.example:30800/"]


def test_logout_without_oidc_just_returns_home(tmp_path, scenarios):
    e = Env(tmp_path, scenarios)
    r = e.client.get("/auth/logout", follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"] == "/"
