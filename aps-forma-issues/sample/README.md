# aps-forma-issues sample

This sample illustrates use of 'aps-forma-issues' library to create 
"Safety" type issues, along with a real image, that will be stored 
and accessible in Docs and then linked, so it renders as an attachment 
on the related Issue.

This library has several API calls chained together, each of
which could independently fail — so the sample checks them one at a
time and stops at the first failure, printing which step it was. 

## Setup

```bash
uv sync --all-packages     # installs aps-ssa + aps-forma-issues + this sample's deps
cp .env.example .env       # then fill in real values
```

## Run

```bash
uv run python create_issue.py                       # uses a built-in placeholder image
uv run python create_issue.py path/to/situation.jpg  # or a real one — recommended, see below
```

Expected output on full success:

```
STEP 1/5: Authenticate (aps-ssa) ...
  OK

STEP 2/5: Create Issue ...
  OK — issue id: ... (#42), published: True

STEP 3/5: Upload 'situation.jpg' to project storage ...
  OK — storage urn: ...

STEP 4/5: Create a real Item in the configured folder ...
  OK — item lineage urn: ...

STEP 5/5: Link the item to issue ... via the Relationships API ...
  OK — relationship: [...]

All steps succeeded. Now go check this Issue in the Forma Build UI...
Direct link to the uploaded file: https://acc.autodesk.com/docs/files/...
```

The placeholder image (used when no path is given) is enough to prove
every API call succeeds, but it's not a real, decodable image — it will be store 
and every step above will report success, but the
attachment will show as a broken thumbnail in the UI. Pass a real image
path to have it properly rendered.

