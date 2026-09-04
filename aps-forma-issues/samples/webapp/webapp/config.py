"""Flask configuration, read from environment variables (see .env.example)."""

from __future__ import annotations

import os


class Config:
    """Flask reads this via `app.config.from_object(Config)`."""

    # --- 3-legged OAuth (Authorization Code flow) ---
    # Required over a service account here: listing/reading Issues as a
    # real user is what lets assignedTo/ownerId resolve against that
    # user's own project membership, and matches how a human would browse
    # the dashboard in the first place.
    APS_CLIENT_ID = os.environ.get("APS_CLIENT_ID")
    APS_CLIENT_SECRET = os.environ.get("APS_CLIENT_SECRET")
    APS_REDIRECT_URI = os.environ.get(
        "APS_REDIRECT_URI", "http://localhost:5000/oauth/callback"
    )
    APS_SCOPE = os.environ.get(
        "APS_SCOPE", "user-profile:read data:read data:write account:read"
    )

    # Fixed APS Authentication v2 endpoints — see
    # https://aps.autodesk.com/en/docs/oauth/v2/tutorials/get-3-legged-token/
    APS_AUTHORIZE_URL = "https://developer.api.autodesk.com/authentication/v2/authorize"
    APS_TOKEN_URL = "https://developer.api.autodesk.com/authentication/v2/token"
    APS_USERINFO_URL = "https://api.userprofile.autodesk.com/userinfo"

    # --- aps-forma-issues ---
    ACC_PROJECT_ID = os.environ.get("ACC_PROJECT_ID")
    ACC_BASE_URL = os.environ.get("ACC_BASE_URL", "https://developer.api.autodesk.com")
    REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "15"))

    # Flask signs the session cookie with this — the OAuth state and access
    # token both live in that session, so always override this in a real
    # deployment via FLASK_SECRET_KEY; the default is only safe for local dev.
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-only-insecure-key")

    # APS redirects back to /oauth/callback as a cross-site top-level
    # navigation after login, so the session cookie must still be sent on
    # that request — "Strict" would silently drop it and break login.
    SESSION_COOKIE_SAMESITE = "Lax"

    PORT = int(os.environ.get("PORT", "5000"))
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
