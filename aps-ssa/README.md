# aps-ssa

Client for Autodesk Platform Services **Service
Account Authentication (SSA)** — a machine identity for server-to-server calls.

## Two identities involved

- `client_id` (+ `client_secret`) identifies the *application* (the APS
  app registered in the developer portal) — `client_id` is also the
  `iss` claim in the JWT assertion.
- `service_account_id` identifies the *machine actor* calling on that
  app's behalf — a service account that nees to be provision separately, with its
  own auto-generated email/Oxygen ID.

For more details check https://aps.autodesk.com/en/docs/ssa/v1/developers_guide/jwt-assertions/


## Usage

```python
from aps_ssa import SsaAuth, SsaConfig

auth = SsaAuth(SsaConfig(
    client_id="...",
    client_secret="...",
    service_account_id="...",
    key_id="...",
    private_key_path="./secrets/ssa_private_key.pem",
))
# or: auth = SsaAuth(SsaConfig.from_env())

token = auth.get_token()  # cached; refreshed automatically near expiry
```

## Test

```bash
uv sync --all-packages
uv run pytest
```
## Sample
Check [aps-ssa sample](./sample/) for illustration on usage and integration. 