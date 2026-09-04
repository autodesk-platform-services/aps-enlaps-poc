"""Entry point for local development.

Run (from this directory, after `uv sync --all-packages` at the
workspace root, i.e. ..):

    cp .env.example .env   # fill in real values
    uv run python run.py

Then open http://localhost:5000 and sign in with Autodesk.
"""

from dotenv import load_dotenv

# override=True: see ../aps-ssa-sample — a stale shell-exported var can
# otherwise silently shadow this script's own .env.
load_dotenv(override=True)

from webapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"], debug=app.config["DEBUG"])
