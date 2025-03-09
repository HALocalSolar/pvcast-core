"""Entry point for the pvcast webserver."""

import uvicorn


def main() -> None:
    """Start the uvicorn server."""

    uvicorn.run("src.pvcast.webserver.app:app")


if __name__ == "__main__":
    main()
