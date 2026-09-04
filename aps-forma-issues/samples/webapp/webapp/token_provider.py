"""Adapts the Flask session's stored 3-legged token to `aps_forma_issues.TokenProvider`."""

from __future__ import annotations

from flask import session


class SessionTokenProvider:
    """Satisfies `aps_forma_issues.TokenProvider` from the current
    request's session-stored access token.

    Refreshing on expiry is out of scope for this sample — a 3-legged
    token lasts 60 minutes, long enough for one dashboard session; sign
    in again if it expires.
    """

    def get_token(self) -> str:
        """Returns the signed-in user's access token.

        Returns:
            str: The bearer access token.

        Raises:
            RuntimeError: If no user is signed in.
        """
        token = session.get("access_token")
        if not token:
            raise RuntimeError("No access token in session — user is not signed in.")
        return token
