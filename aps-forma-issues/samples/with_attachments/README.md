# aps-forma-issues sample with attachments

This sample illustrates use of 'aps-forma-issues' library to create 
"Safety" type issues, along with a real image, that will be directly 
attached to an issue and will show the corresponding thumbnails in the reports.  

> **The main benefit:** attached pictures show in issue reports

> **The main drawback:** the images exist as a hidden items in an internal folder


This library has several API calls chained together, each of
which could independently fail — so the sample checks them one at a
time and stops at the first failure, printing which step it was.

## Setup

```bash
uv sync --all-packages                   # installs aps-ssa + aps-forma-issues + this sample's deps
cp .env.example .env                     # then fill in real values
```

## Run

```bash
uv run python create_issue_with_attach.py                                  # one built-in placeholder image
uv run python create_issue_with_attach.py photo1.jpg photo2.jpg photo3.jpg # multiple real images, one issue
```

Pass as many image paths as you like — this is the point of this
sample: confirming multiple images attach to a single issue via this
path (additive across calls, confirmed live).

Expected output on full success:

```
STEP 1/3: Authenticate (aps-ssa) ...
  OK

STEP 2/3: Create Issue ...
  OK — issue id: ... (#42), published: True

STEP 3/3: Attach 3 image(s) via the Issues-attachments endpoint ...
  [1/3] uploading + attaching 'photo1.jpg' ...
    OK — attachmentId: ...
  [2/3] uploading + attaching 'photo2.jpg' ...
    OK — attachmentId: ...
  [3/3] uploading + attaching 'photo3.jpg' ...
    OK — attachmentId: ...

attachmentCount on re-fetched issue: 3 (expected 3)

All steps succeeded. Now go check this Issue in the Forma Build UI...
```

The `attachmentCount` check at the end is deliberate: unlike the
default (items + Relationships API) path — where the issue's own
`attachmentCount`/`linkedDocuments` fields stay `0`/`[]` even though
the image renders fine — this endpoint-based path keeps
`attachmentCount` in sync. If it doesn't match the number of images you
passed, something's wrong.

The placeholder image (used when no path is given) is enough to prove
every API call succeeds, but it's not a real, decodable image — it will be store 
and every step above will report success, but the
attachment will show as a broken thumbnail in the UI. Pass a real image
path to have it properly rendered.
