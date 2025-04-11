"""Test the configreader module."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import voluptuous as vol
import yaml

from src.pvcast.config.configreader import ConfigReader
from tests.const import CONFIG_DICT  # TEST_CONF_ERR,; TEST_CONF_MISSING,
from tests.const import TEST_CONF_MICRO_PATH, TEST_CONF_STRING_PATH


class TestConfigReader:
    """Test the configreader module."""

    @pytest.fixture
    def config(self, request) -> ConfigReader:
        """Parametrized fixture with different test configurations."""
        return ConfigReader(request.param)

    @pytest.fixture
    def config_dict(self) -> dict:
        """Fixture for the config dictionary."""
        return CONFIG_DICT.copy()

    def test_configreader_no_config_file(self) -> None:
        """Test the configreader without a config file."""
        with pytest.raises(TypeError):
            ConfigReader()

    def test_configreader_wrong_config_file(self) -> None:
        """Test the configreader with a wrong config file."""
        with pytest.raises(FileNotFoundError):
            ConfigReader(Path("wrongfile.yaml"))

    @pytest.mark.parametrize(
        "config", [TEST_CONF_MICRO_PATH, TEST_CONF_STRING_PATH], indirect=True
    )
    def test_configreader_init(self, config: ConfigReader) -> None:
        """Test the configreader with a microinverter."""
        assert isinstance(config, ConfigReader)
        conf = config.config
        assert isinstance(conf, dict)
        conf_validated = config._config_schema(conf)
        assert isinstance(conf_validated, dict)
        print(conf_validated)

    def test_invalid_timezone(self, config_dict) -> None:
        """Test the configreader with an invalid timezone."""
        config_dict["general"]["location"]["timezone"] = "invalid_timezone"
        with pytest.raises(
            vol.MultipleInvalid, match="invalid_timezone for dictionary value"
        ):
            _ = ConfigReader(config_dict)

    def test_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Test that malformed YAML raises an error."""
        malformed_yaml = tmp_path / "bad.yaml"
        malformed_yaml.write_text(
            "general:\n  location: [unclosed", encoding="utf-8"
        )

        with pytest.raises(yaml.YAMLError):
            ConfigReader(malformed_yaml)

    def test_missing_required_fields(self, config_dict: dict) -> None:
        """Test missing required fields raise a schema validation error."""
        config_dict.pop("general")

        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape("required key not provided @ data['general']"),
        ):
            ConfigReader(config_dict)

    @pytest.mark.parametrize("config", [TEST_CONF_STRING_PATH], indirect=True)
    def test_correct_coercion_of_types(self, config: ConfigReader) -> None:
        """Test that coercion of float/bool types works as expected."""
        plant = config.config["plant"][0]
        assert isinstance(plant["microinverter"], bool)
        assert isinstance(plant["arrays"][0]["tilt"], float)

    def test_weather_sources_missing(self, config_dict: dict) -> None:
        """Test missing weather sources raise a schema validation error."""
        config_dict["general"]["weather"].pop("sources")
        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape(
                "required key not provided @ data['general']['weather']"
            ),
        ):
            ConfigReader(config_dict)
