"""Entry point for the pvcast webserver."""

import uvicorn


def main() -> None:
    """Start the uvicorn server."""
    uvicorn.run("src.pvcast.webserver.app:app", reload=True)


if __name__ == "__main__":
    main()
