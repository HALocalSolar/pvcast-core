"""Main module for the webserver."""

from fastapi import FastAPI

from .const import API_VERSION
from .routers.live import router as live_router

app = FastAPI(
    title="pvcast",
    description="A webserver for the pvcast project.",
    version=API_VERSION,
)


app.include_router(live_router, prefix="/live", tags=["live"])
