"""Weather API class that scrapes the data from Clear Outside."""

from __future__ import annotations

import datetime as dt
import logging
from urllib.parse import urljoin

import pandas as pd
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

    def get_weather(self) -> pd.DataFrame:
        """Retrieve weather data."""
        response = requests.get(
            self.url, timeout=int(self.timeout.total_seconds())
        )

        weather_data_list = []
        n_days = 1  # Adjust as needed

        soup = BeautifulSoup(response.content, "lxml")

        for day_int in range(n_days):
            result = soup.select(f"#day_{day_int}")
            if len(result) != 1:
                _LOGGER.debug("No data for day %s, breaking loop.", day_int)
                break

            table = result[0]
            daily_df = self._find_elements(table)

            # Append daily data
            weather_data_list.append(daily_df)

        if not weather_data_list:
            return pd.DataFrame()

        weather_df = pd.concat(weather_data_list, ignore_index=True)

        # Interpolate missing values and drop remaining NaNs
        weather_df = weather_df.interpolate().dropna()

        return weather_df

    def _find_elements(self, table: BeautifulSoup) -> pd.DataFrame:
        """Find weather data elements in the table for one day (24 hours)."""

        # Helper function
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

        # Get detail rows
        detail_rows = table.select("div.fc_detail_row")
        print(detail_rows)

        # Extract relevant parameters
        total_clouds = extract_hourly_values(
            detail_rows, "Total Clouds (% Sky Obscured)"
        )
        temp = extract_hourly_values(detail_rows, "Temperature (°C)")
        rh = extract_hourly_values(detail_rows, "Relative Humidity (%)")
        fog = extract_hourly_values(detail_rows, "Fog (%)")
        precip_prob = extract_hourly_values(
            detail_rows, "Precipitation Probability (%)"
        )
        precip_amt = extract_hourly_values(
            detail_rows, "Precipitation Amount (mm)"
        )

        # Wind speed and direction
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

        # Build DataFrame
        raw_data = pd.DataFrame(
            {
                "cloud_cover": pd.to_numeric(total_clouds, errors="coerce"),
                "temperature": pd.to_numeric(temp, errors="coerce"),
                "humidity": pd.to_numeric(rh, errors="coerce"),
                "wind_speed": pd.to_numeric(wind_speeds, errors="coerce"),
            }
        )

        # Convert wind speed from mph to m/s
        raw_data["wind_speed"] *= 0.44704

        return raw_data
