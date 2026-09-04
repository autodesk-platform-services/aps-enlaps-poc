"""The three-step APS sign-in flow's HTTP endpoints.

    /oauth/login    -> redirects to Autodesk's sign-in page (step 1)
    /oauth/callback -> Autodesk redirects back here with a code (steps 2-3)
    /oauth/logout   -> clears the session and its cookie
"""

from __future__ import annotations

import hmac
import secrets

from flask import (
    Blueprint,
    current_app,
    make_response,
    redirect,
    request,
    session,
    url_for,
)

from .auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

# How many in-flight login attempts (unconsumed CSRF state tokens) to
# remember at once — more than one tab/window mid-login shouldn't break
# either of them, but there's no reason to let this grow unbounded either.
_MAX_PENDING_OAUTH_STATES = 10


def _remember_oauth_state(state: str) -> None:
    pending = session.setdefault("oauth_states", [])
    pending.append(state)
    session["oauth_states"] = pending[-_MAX_PENDING_OAUTH_STATES:]
    # Flask's session only re-saves the cookie when it detects a change to
    # the session dict itself — mutating a list *inside* it (append, above)
    # doesn't trigger that detection on its own, so this flag must be set
    # by hand or the updated `oauth_states` list would silently not persist.
    session.modified = True


def _consume_oauth_state(state: str | None) -> bool:
    """True if `state` matches a token _remember_oauth_state stored
    earlier (and removes it, so it can't be replayed) — False otherwise.
    """
    if not state:
        return False

    pending = session.get("oauth_states", [])
    matched_index = None
    for index, candidate in enumerate(pending):
        # hmac.compare_digest instead of `==`: a plain string comparison
        # returns as soon as it finds the first mismatched character,
        # which leaks (via timing) how many leading characters a guess
        # got right — compare_digest always takes the same time.
        if hmac.compare_digest(state, candidate):
            matched_index = index
            break

    if matched_index is None:
        return False

    pending.pop(matched_index)
    session["oauth_states"] = pending
    session.modified = True
    return True


@auth_bp.route("/oauth/login")
def login():
    """Step 1: sends the user to Autodesk's sign-in/consent page."""
    state = secrets.token_urlsafe(16)
    _remember_oauth_state(state)
    return redirect(AuthService.build_authorize_url(state))


@auth_bp.route("/oauth/callback")
def callback():
    """Steps 2-3: Autodesk redirects back here with `?code=`/`?state=`
    (or `?error=` if the user declined) after they sign in.
    """
    if session.get("access_token"):
        # Already signed in — happens if this callback URL loads twice
        # (common with double page loads), harmless to just move on.
        return redirect(url_for("main.index"))

    error = request.args.get("error")
    if error:
        description = request.args.get("error_description", "")
        return f"Authorization failed: {error} - {description}", 400

    state = request.args.get("state")
    if not _consume_oauth_state(state):
        return "Invalid state parameter. Possible CSRF attempt.", 400

    code = request.args.get("code")
    if not code:
        return "No authorization code returned.", 400

    token = AuthService.exchange_code(code)
    session["access_token"] = token.get("access_token")
    session["refresh_token"] = token.get("refresh_token")

    # A failed profile lookup shouldn't block login — the user's name is
    # only cosmetic (shown in the navbar).
    profile = AuthService.get_user_profile(token.get("access_token"))
    if profile:
        session["user_name"] = profile.get("name") or profile.get("email")

    return redirect(url_for("main.index"))


@auth_bp.route("/oauth/logout")
def logout():
    """Clears the session (server-side) and its cookie (browser-side)."""
    session.clear()
    response = make_response(redirect(url_for("main.index")))
    response.delete_cookie(
        current_app.config.get("SESSION_COOKIE_NAME", "session"),
        path=current_app.config.get("SESSION_COOKIE_PATH") or "/",
        domain=current_app.config.get("SESSION_COOKIE_DOMAIN"),
    )
    return response
