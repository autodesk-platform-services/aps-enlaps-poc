# aps-ssa sample

This sample illustrates how to use aps-ssa library to get an APS access token, using
Service Account Authentication credentials. 

## Setup

```bash
uv sync --all-packages    
cp .env.example .env      # then fill in real values
```

You'll need a provisioned SSA service account + RSA key pair first — by following this tutorial: https://aps.autodesk.com/en/docs/ssa/v1/tutorials/getting-started-with-ssa/task1-create-an-ssa/

## Run

```bash
uv run python get_token.py
```

Expected output on success:

```
Requesting a token for service account 'sa-...' via https://developer.api.autodesk.com ...
Success.
Access token: eyJhbGciOi...
```


### Possible errors

- `Config error` means an env var is missing; 
- `Token exchange failed` means the request reached Autodesk but was rejected — check the printed
status code/body for why (wrong key, service account not yet active etc.).
