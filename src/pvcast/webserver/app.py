"""Main module for the webserver."""

from fastapi import FastAPI

from .const import API_VERSION
from .routers.live import router as live_router

app = FastAPI(
    title="pvcast",
    description="A webserver for the pvcast project.",
    version=API_VERSION,
    docs_url=None,
    redoc_url=None,
)


app.include_router(live_router, prefix="/live", tags=["live"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the pvcast webserver!"}
