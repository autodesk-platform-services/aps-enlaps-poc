"""Token provider interface.

Decouples this library from any specific authentication mechanism —
every request just needs a bearer token, not a particular auth flow.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TokenProvider(Protocol):
    """Anything that can provide a bearer access token.

    `aps_ssa.SsaAuth` satisfies this already. Any other object with a
    `get_token` method works too — for example, a thin wrapper around a
    three-legged OAuth token you already have:

        class SimpleTokenProvider:
            def __init__(self, access_token: str):
                self._access_token = access_token

            def get_token(self) -> str:
                return self._access_token

        client = FormaIssuesClient(config, SimpleTokenProvider(my_3legged_token))
    """

    def get_token(self) -> str:
        """Returns a bearer access token, refreshing or caching it however
        the implementation sees fit.
        """
        ...
