"""Test the configreader module."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from pytz import UnknownTimeZoneError
from voluptuous import MultipleInvalid

from src.pvcast.config.configreader import ConfigReader
from tests.const import (
    TEST_CONF_ERR,
    TEST_CONF_MICRO_PATH,
    TEST_CONF_MISSING,
    TEST_CONF_STRING_PATH,
)


class TestConfigReader:
    """Test the configreader module."""

    @pytest.fixture
    def config(self, request) -> ConfigReader:
        """Parametrized fixture with different test configurations."""
        return ConfigReader(request.param)

    def test_configreader_no_config_file(self) -> None:
        """Test the configreader without a config file."""
        with pytest.raises(TypeError):
            ConfigReader()  # type: ignore[call-arg]

    def test_configreader_wrong_config_file(self) -> None:
        """Test the configreader with a wrong config file."""
        with pytest.raises(FileNotFoundError):
            ConfigReader(Path("wrongfile.yaml"))

    @pytest.mark.parametrize("config", [TEST_CONF_MICRO_PATH], indirect=True)
    def test_configreader_micro(self, config: ConfigReader) -> None:
        """Test the configreader with a microinverter."""
        assert isinstance(config, ConfigReader)
        conf = config.config

    def test_invalid_timezone(self) -> None:
        """Test the configreader with an invalid timezone."""
        with pytest.raises(UnknownTimeZoneError):
            _ = ConfigReader(config_file_path=TEST_CONF_ERR)

    def test_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Test that malformed YAML raises an error."""
        malformed_yaml = tmp_path / "bad.yaml"
        malformed_yaml.write_text(
            "general:\n  location: [unclosed", encoding="utf-8"
        )

        with pytest.raises(yaml.YAMLError):
            ConfigReader(config_file_path=malformed_yaml)

    def test_missing_required_fields(self, tmp_path: Path) -> None:
        """Test missing required fields raise a schema validation error."""
        bad_schema = tmp_path / "missing.yaml"
        bad_schema.write_text("general: {}\nplant: []", encoding="utf-8")

        with pytest.raises(MultipleInvalid):
            ConfigReader(config_file_path=bad_schema)

    @pytest.mark.parametrize("config", [TEST_CONF_STRING_PATH], indirect=True)
    def test_correct_coercion_of_types(self, config: ConfigReader) -> None:
        """Test that coercion of float/bool types works as expected."""
        plant = config.config["plant"][0]
        assert isinstance(plant["microinverter"], bool)
        assert isinstance(plant["arrays"][0]["tilt"], float)

    def test_weather_sources_missing(self) -> None:
        """Test missing weather sources raise a schema validation error."""
        with pytest.raises(
            MultipleInvalid,
            match=re.escape(
                "expected a list for dictionary value @ data['general']['weather']['sources']"
            ),
        ):
            ConfigReader(config_file_path=TEST_CONF_MISSING)
