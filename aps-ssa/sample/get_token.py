from __future__ import annotations

import sys

from dotenv import load_dotenv

load_dotenv(override=True)

from aps_ssa import AuthError, SsaAuth, SsaConfig


def main() -> int:
    try:
        config = SsaConfig.from_env()
    except RuntimeError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Requesting a token for service account {config.service_account_id!r} "
        f"via {config.base_url} ..."
    )

    auth = SsaAuth(config)
    try:
        token = auth.get_token()
    except AuthError as exc:
        print(f"Token exchange failed: {exc}", file=sys.stderr)
        return 1

    print("Success.")
    print(f"Access token: {token}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
