"""This module contains utility functions for working with atmospheric quantities."""

import logging
from typing import Any

import numpy as np
import pandas as pd
from pvlib.irradiance import campbell_norman, disc, get_extra_radiation
from pvlib.location import Location

_LOGGER = logging.getLogger(__name__)


def cloud_cover_to_irradiance(
    cloud_cover: pd.DataFrame,
    location: Location,
    how: str = "clearsky_scaling",
    **kwargs: Any,
) -> pd.DataFrame:
    """Convert cloud cover to irradiance. A wrapper method.

    NB: Code copied from pvlib.forecast as the pvlib forecast module is deprecated as of pvlib 0.9.1!

    :param cloud_cover: Cloud cover as a pandas DataFrame with 'datetime' and 'cloud_cover' columns
    :param location: The pvlib Location object for solar position calculations
    :param how: Selects the method for conversion. Can be one of clearsky_scaling or campbell_norman.
    :param **kwargs: Passed to the selected method.
    :return: Irradiance, columns include ghi, dni, dhi.
    """
    # datetimes must be provided as a pd.DatetimeIndex otherwise pvlib fails
    if "timestamp" not in cloud_cover.columns:
        raise ValueError("cloud_cover DataFrame must contain a 'timestamp' column.")

    # infer frequency from the data
    datetime_series = pd.to_datetime(cloud_cover["timestamp"]).sort_values()
    freq = pd.infer_freq(datetime_series)

    # fallback to hourly if frequency can't be inferred
    if freq is None:
        freq = "h"

    times = pd.date_range(
        cloud_cover["timestamp"].min(),
        cloud_cover["timestamp"].max(),
        freq=freq,
    )

    # convert cloud cover to GHI/DNI/DHI
    how = how.lower()
    if how == "clearsky_scaling":
        irrads = _cloud_cover_to_irradiance_clearsky_scaling(
            cloud_cover, location, times, **kwargs
        )
    elif how == "campbell_norman":
        irrads = _cloud_cover_to_irradiance_campbell_norman(
            cloud_cover, location, times, **kwargs
        )
    else:
        msg = f"Invalid how argument: {how}"
        raise ValueError(msg)
    _LOGGER.debug(
        "Converted cloud cover to irradiance using %s. Result: \n%s", how, irrads
    )
    return irrads


def _cloud_cover_to_irradiance_clearsky_scaling(
    cloud_cover: pd.DataFrame,
    location: Location,
    times: pd.DatetimeIndex,
    **kwargs: Any,
) -> pd.DataFrame:
    """Convert cloud cover to irradiance using the clearsky scaling method.

    :param cloud_cover: Cloud cover as a pandas DataFrame with 'cloud_cover' column
    :param location: The pvlib Location object for solar position calculations
    :param times: DatetimeIndex for the time range
    :param **kwargs: Passed to the selected method.
    :return: Irradiance, columns include ghi, dni, dhi.
    """
    # get clear sky data for provided datetimes
    solpos = location.get_solarposition(times)
    clear_sky = location.get_clearsky(times, "ineichen", solpos)
    cover = np.asarray(cloud_cover["cloud_cover"].values, dtype=np.float64)

    # convert cloud cover to GHI/DNI/DHI
    ghi = _cloud_cover_to_ghi_linear(
        cover, np.asarray(clear_sky["ghi"].values, dtype=np.float64), **kwargs
    )

    dni = disc(ghi, solpos["zenith"], times)["dni"]
    dhi = ghi - np.asarray(dni * np.cos(np.radians(solpos["zenith"])), dtype=np.float64)

    # construct df with ghi, dni, dhi and fill NaNs with 0
    result = pd.DataFrame({"ghi": ghi, "dni": dni, "dhi": dhi})
    return result.fillna(0)


def _cloud_cover_to_irradiance_campbell_norman(
    cloud_cover: pd.DataFrame,
    location: Location,
    times: pd.DatetimeIndex,
    **kwargs: Any,
) -> pd.DataFrame:
    """Convert cloud cover to irradiance using the Campbell and Norman model.

    :param cloud_cover: Cloud cover in [%] as a pandas DataFrame with 'cloud_cover' column.
    :param location: The pvlib Location object for solar position calculations
    :param times: DatetimeIndex for the time range
    :param **kwargs: Passed to the selected method.
    :return: Irradiance as a pandas DataFrame with columns ghi, dni, dhi.
    """
    # get clear sky data for provided datetimes
    zen = np.asarray(
        location.get_solarposition(times)["apparent_zenith"], dtype=np.float64
    )
    dni_extra = np.asarray(get_extra_radiation(times), dtype=np.float64)
    transmittance = _cloud_cover_to_transmittance_linear(
        np.asarray(cloud_cover["cloud_cover"].values, dtype=np.float64), **kwargs
    )

    # convert cloud cover to GHI/DNI/DHI
    irrads = campbell_norman(zen, transmittance, dni_extra=dni_extra)

    # construct df with ghi, dni, dhi and fill NaNs with 0
    result = pd.DataFrame(
        {"ghi": irrads["ghi"], "dni": irrads["dni"], "dhi": irrads["dhi"]}
    )
    return result.fillna(0)


def _cloud_cover_to_transmittance_linear(
    cloud_cover: np.ndarray, offset: float = 0.75
) -> np.ndarray:
    """Convert cloud cover (percentage) to atmospheric transmittance using a linear model.

    :param cloud_cover: Cloud cover in [%] as a numpy array.
    :param offset: Determines the maximum transmittance for the linear model.
    :return: Atmospheric transmittance as a numpy array.
    """
    return ((100.0 - cloud_cover) / 100.0) * offset


def _cloud_cover_to_ghi_linear(
    cloud_cover: np.ndarray,
    ghi_clear: np.ndarray,
    offset: float = 35.0,
) -> np.ndarray:
    """Convert cloud cover to GHI using a linear relationship.

    :param cloud_cover: Cloud cover in [%] as a numpy array.
    :param ghi_clear: Clear sky GHI as a numpy array.
    :param offset: Determines the maximum GHI for the linear model.
    :return: GHI as a numpy array.
    """
    offset = offset / 100.0
    cloud_cover = cloud_cover / 100.0
    ghi = (offset + (1 - offset) * (1 - cloud_cover)) * ghi_clear
    return np.array(ghi, dtype=np.float64)
