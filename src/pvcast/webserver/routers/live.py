"""Contains the FastAPI router for the /live endpoint."""

from __future__ import annotations

import datetime as dt  # noqa: TCH003

from fastapi import APIRouter, Query
from typing_extensions import Annotated

from src.pvcast.webserver.models.base import Interval
from src.pvcast.webserver.models.live import LiveModel

router = APIRouter()


@router.get("/{interval}")
async def get(
    start: Annotated[
        dt.datetime | None,
        Query(
            description="Start datetime in ISO format. Leave empty for no \
                filter. Must be UTC."
        ),
    ] = None,
    end: Annotated[
        dt.datetime | None,
        Query(
            description="End datetime in ISO format. Leave empty for no \
                filter. Must be UTC."
        ),
    ] = None,
    interval: Interval = Interval.H1,
) -> LiveModel:
    """Get the estimated PV output power in Watts.

    Forecast is provided at interval <interval> for the given PV system <name>.

    NB: Power data is defined to represent the state at the beginning of the \
    interval and what is going to happen in this interval.
    """
    print(f"Request for {start} to {end} for {interval} interval")
