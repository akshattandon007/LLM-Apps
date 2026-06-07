"""``python -m flights_over_me`` launches the dev server."""

from __future__ import annotations

import uvicorn

from .config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "flights_over_me.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    main()
