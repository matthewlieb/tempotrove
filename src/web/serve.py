"""Production HTTP server: bind using PORT from the environment (no shell expansion).

Railway and some Docker runners invoke the start command without a shell, so
``uvicorn ... --port $PORT`` receives the literal string ``$PORT`` and exits.
This module reads ``os.environ`` instead.
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8013"))
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
