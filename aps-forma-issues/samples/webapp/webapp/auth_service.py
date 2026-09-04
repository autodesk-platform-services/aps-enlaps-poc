"""Implements the APS 3-legged OAuth (Authorization Code) flow, in three
steps that map 1:1 onto the three methods below:

1. Send the user to Autodesk's sign-in/consent page (build_authorize_url).
2. Autodesk redirects back with a one-time `code` (auth_routes.py's
   /oauth/callback handles that redirect).
3. Exchange that `code` for a real access token (exchange_code), then
   optionally fetch the user's profile to show their name in the navbar
   (get_user_profile).

See https://aps.autodesk.com/en/docs/oauth/v2/tutorials/get-3-legged-token/
for the full walkthrough this mirrors.
"""

from __future__ import annotations

import base64
from urllib.parse import urlencode

import requests
from flask import current_app


class AuthService:
    """Implements the APS 3-legged OAuth (Authorization Code) flow."""

    @staticmethod
    def build_authorize_url(state: str) -> str:
        """Step 1: the URL to redirect the user's browser to.

        Args:
            state (str): Random CSRF token — auth_routes.py stores it in
                the session and checks it again on the callback.

        Returns:
            str: Full authorize URL, including query string.
        """
        params = {
            "response_type": "code",
            "client_id": current_app.config["APS_CLIENT_ID"],
            "redirect_uri": current_app.config["APS_REDIRECT_URI"],
            "scope": current_app.config["APS_SCOPE"],
            "state": state,
        }
        return f"{current_app.config['APS_AUTHORIZE_URL']}?{urlencode(params)}"

    @staticmethod
    def exchange_code(code: str) -> dict:
        """Step 3: trades the one-time authorization `code` for a real
        access token. Authenticated as the app itself (via HTTP Basic
        built from the client id/secret) — this is why APS_CLIENT_SECRET
        must stay server-side and never reach the browser.

        Args:
            code (str): Authorization code from the callback's `?code=`.

        Returns:
            dict: `{"access_token", "refresh_token", "expires_in", ...}`.
        """
        client_id = current_app.config["APS_CLIENT_ID"]
        client_secret = current_app.config["APS_CLIENT_SECRET"]
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": current_app.config["APS_REDIRECT_URI"],
        }
        resp = requests.post(
            current_app.config["APS_TOKEN_URL"], headers=headers, data=data, timeout=15
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_user_profile(access_token: str) -> dict | None:
        """Fetches the signed-in user's name/email, for display only.

        Args:
            access_token (str): A valid access token with `user-profile:read`.

        Returns:
            dict | None: Profile fields, or `None` if the lookup failed —
            a failure here isn't fatal to signing in.
        """
        resp = requests.get(
            current_app.config["APS_USERINFO_URL"],
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        return resp.json() if resp.status_code == 200 else None
