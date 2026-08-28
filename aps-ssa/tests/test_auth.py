from urllib.parse import parse_qs

import responses

from aps_ssa.auth import SsaAuth
from aps_ssa.exceptions import AuthError


@responses.activate
def test_get_token_caches_until_near_expiry(config):
    responses.add(
        responses.POST,
        f"{config.base_url}/authentication/v2/token",
        json={"access_token": "token-1", "expires_in": 3600},
        status=200,
    )

    auth = SsaAuth(config)
    token1 = auth.get_token()
    token2 = auth.get_token()

    assert token1 == "token-1"
    assert token2 == "token-1"
    assert len(responses.calls) == 1  # second call served from cache

    sent = parse_qs(responses.calls[0].request.body)
    assert sent["grant_type"] == ["urn:ietf:params:oauth:grant-type:jwt-bearer"]
    assert "assertion" in sent
    assert sent["client_id"] == [config.client_id]
    assert sent["client_secret"] == [config.client_secret]
    assert "client_assertion" not in sent


@responses.activate
def test_get_token_raises_on_failure(config):
    responses.add(
        responses.POST,
        f"{config.base_url}/authentication/v2/token",
        json={"error": "invalid_client"},
        status=401,
    )

    auth = SsaAuth(config)
    try:
        auth.get_token()
        assert False, "expected AuthError"
    except AuthError:
        pass
