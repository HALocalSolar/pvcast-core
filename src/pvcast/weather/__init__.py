"""Weather API module."""

from __future__ import annotations

from .api import WeatherAPIFactory
from .clearoutside import ClearOutside

API_FACTORY = WeatherAPIFactory()
API_FACTORY.register("clearoutside", ClearOutside)
