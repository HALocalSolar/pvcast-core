"""Webserver data models base module."""

from enum import Enum

from pydantic import BaseModel
from typing_extensions import Annotated

res_examp = [
    {
        "datetime": "2023-09-19T15:00:00+0000",
        "watt": 1428,
        "watt_cumsum": 1428,
    },
    {
        "datetime": "2023-09-19T15:30:00+0000",
        "watt": 1012,
        "watt_cumsum": 2440,
    },
    {
        "datetime": "2023-09-19T16:00:00+0000",
        "watt": 279,
        "watt_cumsum": 2719,
    },
    {
        "datetime": "2023-09-19T16:30:00+0000",
        "watt": 0,
        "watt_cumsum": 2719,
    },
]


data_example = {
    "clearskymodel": "Ineichen",
    "start": "2023-09-19T15:00:00+0000",
    "end": "2023-09-20T15:00:00+0000",
    "timezone": "UTC",
    "interval": "1h",
    "period": res_examp,
}


class Interval(str, Enum):
    """Power interval enum."""

    MIN1 = "1m"
    MIN5 = "5m"
    MIN15 = "15m"
    MIN30 = "30m"
    H1 = "1h"


class PowerData(BaseModel):
    """Power data model."""

    datetime: str
    watt: int
    watt_cumsum: int


class BaseDataModel(BaseModel):
    """Base data model."""

    start: Annotated[str | None, "Start time of the returned data."]
    end: Annotated[str | None, "End time of the returned data."]
    forecast_type: Annotated[
        str | None, "Forecast type used to generate the data."
    ]
    plant_name: Annotated[str | None, "Name of the PV system"]
    timezone: Annotated[str | None, "Timezone of the returned data"] = "UTC"
    interval: Annotated[Interval, "Interval of the returned data"]
    period: Annotated[list[PowerData], "PV power at the requested interval."]
