"""Module that contains the command line application."""

from __future__ import annotations

from typing import Any

import uvicorn

from src.pvcast.commandline.commandline import get_args


def main() -> None:
    """Entry point for the application script."""
    args: dict[str, Any] = get_args()
    # start uvicorn server
    uvicorn.run(
        "src.pvcast.webserver.app:app",
        host=args["host"],
        port=args["port"],
        reload=False,
        workers=args["workers"],
    )


if __name__ == "__main__":
    main()
