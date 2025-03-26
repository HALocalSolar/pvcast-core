"""Weather API class that scrapes the data from Clear Outside."""

from __future__ import annotations

import datetime as dt
import logging
from urllib.parse import urljoin

import pandas as pd
import pint_pandas  # TODO: ignore unused import
import requests
from bs4 import BeautifulSoup
from pvlib.location import Location

from src.pvcast.weather.api import WeatherAPI

_LOGGER = logging.getLogger(__name__)


class ClearOutside(WeatherAPI):
    """Weather API class that scrapes the data from Clear Outside."""

    _url_base: str = "https://clearoutside.com/forecast/"

    def __init__(
        self,
        location: Location,
        timeout: dt.timedelta = dt.timedelta(seconds=10),
    ):
        """Class constructor"""
        super().__init__(timeout)
        self.location = location
        lat = str(round(self.location.latitude, 2))
        lon = str(round(self.location.longitude, 2))
        self.url = urljoin(self._url_base, f"{lat}/{lon}")

    def retrieve_new_data(self) -> pd.DataFrame:
        """Retrieve weather data."""
        _LOGGER.debug("Retrieving new weather data from %s", self.url)
        response = requests.get(
            self.url, timeout=int(self.timeout.total_seconds())
        )
        _LOGGER.debug("Response status code: %s", response.status_code)

        weather_data_list = []
        soup = BeautifulSoup(response.content, "lxml")

        # loop over all forecast days in the HTML
        for day_div in soup.find_all("div", class_="fc_day"):
            daily_df = self._find_elements(day_div)

            if daily_df.empty:
                continue

            weather_data_list.append(daily_df)

        if not weather_data_list:
            return pd.DataFrame()

        df = pd.concat(weather_data_list, ignore_index=True)

        # interpolate and drop any remaining NaNs
        df = df.interpolate().dropna()

        # convert to pint datatype
        schema = self.input_schema
        df = df.astype(schema)
        return df

    @property
    def input_schema(self) -> dict[str, str]:
        return {
            "cloud_cover": "pint[dimensionless]",
            "temperature": "pint[celsius]",
            "humidity": "pint[dimensionless]",
            "wind_speed": "pint[mph]",
        }

    def _find_elements(self, table: BeautifulSoup) -> pd.DataFrame:
        """Find weather data elements in the table for one day (24 hours)."""

        def extract_hourly_values(detail_rows, label_text):
            for row in detail_rows:
                label = row.find("span", class_="fc_detail_label").get_text(
                    strip=True
                )
                if label == label_text:
                    return [
                        li.get_text(strip=True) for li in row.find_all("li")
                    ]
            return []

        detail_rows = table.select("div.fc_detail_row")

        total_clouds = extract_hourly_values(
            detail_rows, "Total Clouds (% Sky Obscured)"
        )
        temp = extract_hourly_values(detail_rows, "Temperature (°C)")
        rh = extract_hourly_values(detail_rows, "Relative Humidity (%)")

        wind_speeds = []
        wind_dirs = []
        for row in detail_rows:
            label = row.find("span", class_="fc_detail_label").get_text(
                strip=True
            )
            if label == "Wind Speed/Direction (mph)":
                for li in row.find_all("li"):
                    wind_speeds.append(li.get_text(strip=True))
                    title = li.get("title", "")
                    direction = (
                        title.split("from the ")[-1].split(" (")[0]
                        if "from the" in title
                        else ""
                    )
                    wind_dirs.append(direction)
                break

        if not total_clouds or not temp or not rh or not wind_speeds:
            return pd.DataFrame()  # Return empty if any key data is missing

        raw_data = pd.DataFrame(
            {
                "cloud_cover": pd.to_numeric(total_clouds, errors="coerce"),
                "temperature": pd.to_numeric(temp, errors="coerce"),
                "humidity": pd.to_numeric(rh, errors="coerce"),
                "wind_speed": pd.to_numeric(wind_speeds, errors="coerce"),
            }
        )

        return raw_data
