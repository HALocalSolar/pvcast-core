"""Test all configured weather platforms that inherit from WeatherAPI class."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import pytest
import responses
from bs4 import BeautifulSoup
from pvlib.location import Location
from src.pvcast.weather.api import API_FACTORY, WeatherAPI
from src.pvcast.weather.clearoutside import ClearOutside

from .test_weather import WeatherProviderTests

if TYPE_CHECKING:
    from collections.abc import Generator


class TestClearOutsideWeather(WeatherProviderTests):
    """Clearoutside specific weather API setup and tests."""

    @pytest.fixture(scope="session")
    def clearoutside_html_page(self) -> str:
        """Load the clearoutside html page."""
        with Path.open(
            Path("tests/data/clearoutside.html"), encoding="utf-8"
        ) as html_file:
            return html_file.read()

    @pytest.fixture
    def clearoutside_api(
        self, location: Location, clearoutside_html_page: str
    ) -> Generator[WeatherAPI]:
        """Set up the Clear Outside API."""
        lat = str(round(location.latitude, 2))
        lon = str(round(location.longitude, 2))

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                urljoin("https://clearoutside.com/forecast/", f"{lat}/{lon}"),
                body=clearoutside_html_page,
                status=200,
            )
            api = API_FACTORY.get_weather_api("clearoutside", location=location)
            assert isinstance(api, ClearOutside)
            yield api

    @pytest.fixture
    def weather_api(self, clearoutside_api: WeatherAPI) -> WeatherAPI:
        """Return the weather api."""
        return clearoutside_api

    def test_extract_hourly_values_missing_label(self, location: Location) -> None:
        """Test _extract_hourly_values with missing label."""
        api = ClearOutside(location)

        # create mock detail rows without the requested label
        mock_html = """
        <div class="fc_detail_row">
            <span class="fc_detail_label">Different Label</span>
            <ul><li>value1</li><li>value2</li></ul>
        </div>
        """
        soup = BeautifulSoup(mock_html, "lxml")
        detail_rows = soup.select("div.fc_detail_row")

        with pytest.raises(
            ValueError, match="Could not find label 'Missing Label' in detail rows."
        ):
            api._extract_hourly_values(detail_rows, "Missing Label")

    def test_find_elements_missing_wind_data(self, location: Location) -> None:
        """Test _find_elements when wind speed data is missing."""
        api = ClearOutside(location)

        # create mock HTML with weather data but missing wind speed section
        # the existing code will fail with mismatched array lengths
        # when wind data is missing
        # this test verifies the current behavior - it should raise ValueError
        mock_html = """
        <div class="fc_day">
            <div class="fc_detail_row">
                <span class="fc_detail_label">Total Clouds (% Sky Obscured)</span>
                <ul><li>10</li><li>20</li></ul>
            </div>
            <div class="fc_detail_row">
                <span class="fc_detail_label">Temperature (°C)</span>
                <ul><li>15</li><li>18</li></ul>
            </div>
            <div class="fc_detail_row">
                <span class="fc_detail_label">Relative Humidity (%)</span>
                <ul><li>60</li><li>65</li></ul>
            </div>
            <!-- Missing Wind Speed/Direction section -->
        </div>
        """
        soup = BeautifulSoup(mock_html, "lxml")
        table_element = soup.find("div", class_="fc_day")
        assert table_element is not None

        # this should raise ValueError due to mismatched array lengths
        # when wind data is empty but other columns have data
        with pytest.raises(ValueError, match="All arrays must be of the same length"):
            api._find_elements(table_element)  # type: ignore[arg-type]

    def test_get_start_time_missing_fc_hours(self, location: Location) -> None:
        """Test _get_start_time when fc_hours div is missing."""
        api = ClearOutside(location)

        # create mock HTML without fc_hours div
        mock_html = """
        <html>
            <h2>Generated: 23/03/25 13:29:25. Forecast: 23/03/25 to 29/03/25.
            Timezone: UTC+1.00</h2>
            <!-- Missing fc_hours div -->
        </html>
        """
        soup = BeautifulSoup(mock_html, "lxml")

        with pytest.raises(
            ValueError, match="Could not find 'fc_hours' div in the HTML."
        ):
            api._get_start_time(soup)

    def test_get_start_time_invalid_hour_format(self, location: Location) -> None:
        """Test _get_start_time when hour format cannot be parsed."""
        api = ClearOutside(location)

        # create mock HTML with invalid hour format
        mock_html = """
        <html>
            <h2>Generated: 23/03/25 13:29:25. Forecast: 23/03/25 to 29/03/25.
            Timezone: UTC+1.00</h2>
            <div class="fc_hours">
                <div class="fc_hours fc_hour_ratings">
                    <!-- Invalid hour format that won't match regex -->
                    <li><span>Invalid</span></li>
                </div>
            </div>
        </html>
        """
        soup = BeautifulSoup(mock_html, "lxml")

        with pytest.raises(ValueError, match="Could not parse forecast hour."):
            api._get_start_time(soup)

    def test_get_start_time_invalid_date_format(self, location: Location) -> None:
        """Test _get_start_time when date/timezone format cannot be parsed."""
        api = ClearOutside(location)

        # create mock HTML with valid hour but invalid date format
        mock_html = """
        <html>
            <h2>Generated: INVALID_DATE_FORMAT</h2>
            <div class="fc_hours">
                <div class="fc_hours fc_hour_ratings">
                    <li><span></span> 14 <span></span></li>
                </div>
            </div>
        </html>
        """
        soup = BeautifulSoup(mock_html, "lxml")

        with pytest.raises(
            ValueError, match="Could not parse forecast date or timezone."
        ):
            api._get_start_time(soup)

    def test_retrieve_new_data_with_malformed_html(self, location: Location) -> None:
        """Test retrieve_new_data with malformed HTML that triggers edge cases."""
        lat = str(round(location.latitude, 2))
        lon = str(round(location.longitude, 2))

        # create HTML that will trigger parsing errors
        malformed_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <h2>Generated: 23/03/25 13:29:25. Forecast: 23/03/25 to 29/03/25.
            Timezone: UTC+1.00</h2>
            <div class="fc_hours">
                <div class="fc_hours fc_hour_ratings">
                    <li><span></span> 14 <span></span></li>
                </div>
            </div>
            <div class="fc_day">
                <div class="fc_detail_row">
                    <span class="fc_detail_label">Total Clouds (% Sky Obscured)</span>
                    <ul><li>10</li><li>20</li></ul>
                </div>
                <div class="fc_detail_row">
                    <span class="fc_detail_label">Temperature (°C)</span>
                    <ul><li>15</li><li>18</li></ul>
                </div>
                <div class="fc_detail_row">
                    <span class="fc_detail_label">Relative Humidity (%)</span>
                    <ul><li>60</li><li>65</li></ul>
                </div>
                <!-- Missing Wind Speed/Direction data will cause DataFrame error -->
            </div>
        </body>
        </html>
        """

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                urljoin("https://clearoutside.com/forecast/", f"{lat}/{lon}"),
                body=malformed_html,
                status=200,
            )

            # this should raise ValueError due to header parsing failure
            api = ClearOutside(location)
            with pytest.raises(
                ValueError, match="Could not parse forecast date or timezone."
            ):
                api.retrieve_new_data()
