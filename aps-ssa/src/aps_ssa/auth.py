"""APS Service Account Authentication (SSA).

Exchanges a JWT assertion (signed with the service account's private key)
for an APS OAuth2 access token, and caches it until shortly before expiry.

This uses the JWT *as the grant itself* (RFC 7523 §2.1 —
`grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer` with the JWT
under `assertion`), but — confirmed against Autodesk's actual tutorial
(https://aps.autodesk.com/en/docs/ssa/v1/tutorials/getting-started-with-ssa/task3-generate-3-legged-access-token/)
after two rounds of guessing wrong — Autodesk's implementation is a
non-standard hybrid: it still requires `client_id` **and**
`client_secret` in the body alongside the JWT assertion, rather than
relying on the JWT signature alone. Omitting them produces a generic
`AUTH-001` "client_id ... does not have access to the api product"
error that looks like an account/entitlement problem but isn't one.

Still not validated end-to-end against a live service account with a
successful (non-error) response — see aps-ssa-sample.
"""

from __future__ import annotations

import threading
import time
from typing import Optional, Tuple

import jwt
import requests

from .config import SsaConfig
from .exceptions import AuthError

TOKEN_PATH = "/authentication/v2/token"


class SsaAuth:
    def __init__(self, config: SsaConfig, session: Optional[requests.Session] = None):
        self._config = config
        self._session = session or requests.Session()
        self._lock = threading.Lock()
        self._cached_token: Optional[str] = None
        self._expires_at: float = 0

    def get_token(self) -> str:
        with self._lock:
            if self._cached_token and time.time() < self._expires_at - 30:
                return self._cached_token
            self._cached_token, ttl = self._fetch_token()
            self._expires_at = time.time() + ttl
            return self._cached_token

    def _token_url(self) -> str:
        return f"{self._config.base_url}{TOKEN_PATH}"

    def _build_assertion(self) -> str:
        now = int(time.time())
        claims = {
            "iss": self._config.client_id,
            "sub": self._config.service_account_id,
            "aud": self._token_url(),
            "exp": now + 300,
            "iat": now,
            "scope": self._config.scopes.split(),
        }
        with open(self._config.private_key_path, "rb") as f:
            private_key = f.read()
        headers = {"alg": "RS256", "kid": self._config.key_id}
        return jwt.encode(claims, private_key, algorithm="RS256", headers=headers)

    def _fetch_token(self) -> Tuple[str, int]:
        assertion = self._build_assertion()
        resp = self._session.post(
            self._token_url(),
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
                "scope": self._config.scopes,
            },
            timeout=self._config.request_timeout_seconds,
        )
        if resp.status_code != 200:
            raise AuthError(
                f"APS token exchange failed: {resp.status_code} {resp.text}"
            )
        body = resp.json()
        return body["access_token"], int(body.get("expires_in", 3600))
