"""Weather API class that scrapes the data from Clear Outside."""

from __future__ import annotations

import datetime as dt
import logging
import re
from urllib.parse import urljoin

import pandas as pd
import pint_pandas
import requests
import voluptuous as vol
from bs4 import BeautifulSoup
from pvlib.location import Location

from src.pvcast.weather.api import API_FACTORY, WeatherAPI

_LOGGER = logging.getLogger(__name__)
SCHEMA = vol.Schema({vol.Required("type"): "clearoutside", vol.Required("name"): str})


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
        response = requests.get(self.url, timeout=int(self.timeout.total_seconds()))
        _LOGGER.debug("Response status code: %s", response.status_code)

        weather_data_list = []
        soup = BeautifulSoup(response.content, "lxml")

        # get timezone and base date
        start = self._get_start_time(soup)
        _LOGGER.debug("Forecast start time: %s", start)

        # loop over all forecast days in the HTML
        for day_div in soup.find_all("div", class_="fc_day"):
            weather_data_list.append(self._find_elements(day_div))

        df = pd.concat(weather_data_list, ignore_index=True)

        # convert to pint datatype
        df = df.astype(self.input_schema)

        # add timestamp column
        df["datetime"] = pd.date_range(
            start=start,
            periods=len(df),
            freq="h",  # Use lowercase 'h' for hourly frequency
        )

        return df

    @property
    def input_schema(self) -> dict[str, str]:
        return {
            "cloud_cover": "pint[dimensionless]",
            "temperature": "pint[celsius]",
            "humidity": "pint[dimensionless]",
            "wind_speed": "pint[mph]",
        }

    def _extract_hourly_values(self, detail_rows, label_text):
        for row in detail_rows:
            label = row.find("span", class_="fc_detail_label").get_text(strip=True)
            if label == label_text:
                return [li.get_text(strip=True) for li in row.find_all("li")]
        raise ValueError(f"Could not find label '{label_text}' in detail rows.")

    def _find_elements(self, table: BeautifulSoup) -> pd.DataFrame:
        """Find weather data elements in the table for one day (24 hours)."""
        detail_rows = table.select("div.fc_detail_row")

        total_clouds = self._extract_hourly_values(
            detail_rows, "Total Clouds (% Sky Obscured)"
        )
        temp = self._extract_hourly_values(detail_rows, "Temperature (°C)")
        rh = self._extract_hourly_values(detail_rows, "Relative Humidity (%)")

        wind_speeds = []
        wind_dirs = []
        for row in detail_rows:
            label = row.find("span", class_="fc_detail_label").get_text(strip=True)
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

        raw_data = pd.DataFrame(
            {
                "cloud_cover": pd.to_numeric(total_clouds, errors="coerce"),
                "temperature": pd.to_numeric(temp, errors="coerce"),
                "humidity": pd.to_numeric(rh, errors="coerce"),
                "wind_speed": pd.to_numeric(wind_speeds, errors="coerce"),
            }
        )

        return raw_data

    def _get_start_time(self, soup: BeautifulSoup) -> dt.datetime:
        """Get start time including timezone from the forecast header."""
        match = re.search(
            r'<div class="fc_hours fc_hour_ratings">.*?<li[^>]*?><span[^>]*?>.*?</span>\s*(\d{1,2})\s*<span>',
            soup.find("div", class_="fc_hours").decode(),
            re.DOTALL,
        )
        # get hour
        if match:
            hour = int(match.group(1))
            time = dt.time(hour=hour, minute=0, second=0)
        else:
            raise ValueError("Could not parse forecast hour.")

        # extract timezone and base date from forecast header
        header = soup.find("h2", string=re.compile("Generated:"))
        match = re.search(
            r"Generated:\s*(\d{2}/\d{2}/\d{2}) (\d{2}:\d{2}:\d{2})\. "
            r"Forecast:\s*(\d{2}/\d{2}/\d{2}) to \d{2}/\d{2}/\d{2}\. "
            r"Timezone: UTC([+-]\d+\.\d+)",
            header.text,
        )
        _LOGGER.debug("Forecast header: %s", header.text)

        if match:
            date = dt.datetime.strptime(match.group(1), "%d/%m/%y").date()
            tz = match.group(4)

            start = dt.datetime.combine(
                date, time, dt.timezone(dt.timedelta(hours=float(tz)))
            )
            start = start.replace(minute=0, second=0, microsecond=0)
            return start
        raise ValueError("Could not parse forecast date or timezone.")


# Register the API with the factory
API_FACTORY.register(
    "clearoutside",
    ClearOutside,
    SCHEMA,
)
