"""Entry point for the Somba API."""

from __future__ import annotations

import os

import uvicorn

from somba.api.app import app


if __name__ == "__main__":
<<<<<<< HEAD
    import uvicorn
=======
>>>>>>> refs/remotes/origin/main
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
