"""Test PV plant creation."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import voluptuous as vol
import yaml

from src.pvcast.model.plant import MicroPlant, StringPlant
from tests.const import CONFIG_STRING_DICT


class TestPlant:
    """Test PV plant creation."""

    @pytest.fixture
    def string_plant(self) -> StringPlant:
        """Fixture for the micro plant."""
        return StringPlant(CONFIG_STRING_DICT["plant"][0])

    def test_string_plant(self, string_plant: StringPlant) -> None:
        """Test the micro plant."""
        assert isinstance(string_plant, StringPlant)
        assert isinstance(string_plant._config, dict)
