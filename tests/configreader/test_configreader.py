"""Test the configreader module."""

from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest
import voluptuous as vol
import yaml
from src.pvcast.config.configreader import ConfigReader

from tests.const import (
    CONFIG_MICRO_DICT,
    CONFIG_SIMPLE_MICRO_DICT,
    CONFIG_STRING_DICT,
    TEST_CONF_MICRO_PATH,
    TEST_CONF_SIMPLE_PATH,
    TEST_CONF_STRING_PATH,
)


class TestConfigReader:
    """Test the configreader module."""

    @pytest.fixture
    def config(self, request: pytest.FixtureRequest) -> ConfigReader:
        """Parametrized fixture with different test configurations."""
        return ConfigReader(request.param)

    @pytest.fixture
    def config_dict_string(self) -> dict:
        """Fixture for the string inverter config dictionary."""
        return copy.deepcopy(CONFIG_STRING_DICT)

    @pytest.fixture
    def config_dict_micro(self) -> dict:
        """Fixture for the microinverter config dictionary."""
        return copy.deepcopy(CONFIG_MICRO_DICT)

    @pytest.fixture
    def config_dict_simple(self) -> dict:
        """Fixture for the simple config dictionary."""
        return copy.deepcopy(CONFIG_SIMPLE_MICRO_DICT)

    def test_configreader_no_config_file(self) -> None:
        """Test the configreader without a config file."""
        with pytest.raises(TypeError):
            ConfigReader()  # type: ignore[arg-type]

    def test_configreader_wrong_config_file(self) -> None:
        """Test the configreader with a wrong config file."""
        with pytest.raises(FileNotFoundError):
            ConfigReader(Path("wrongfile.yaml"))

    @pytest.mark.parametrize(
        "config",
        [TEST_CONF_MICRO_PATH, TEST_CONF_STRING_PATH, TEST_CONF_SIMPLE_PATH],
        indirect=True,
    )
    def test_configreader_init(self, config: ConfigReader) -> None:
        """Test the configreader with a microinverter."""
        assert isinstance(config, ConfigReader)
        conf = config.config
        assert isinstance(conf, dict)
        conf_validated = config._config_schema(conf)
        assert isinstance(conf_validated, dict)

    def test_invalid_timezone(self, config_dict_string: dict) -> None:
        """Test the configreader with an invalid timezone."""
        config_dict_string["general"]["location"]["timezone"] = "invalid_timezone"
        with pytest.raises(
            vol.MultipleInvalid, match="invalid_timezone for dictionary value"
        ):
            _ = ConfigReader(config_dict_string)

    def test_missing_module(self, config_dict_string: dict) -> None:
        """Test that missing module raises a schema validation error."""
        config_dict_string["plant"][0]["arrays"][0].pop("module")
        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape("config contains potential error"),
        ):
            ConfigReader(config_dict_string)

    def test_missing_inverter(self, config_dict_string: dict) -> None:
        """Test that missing inverter raises a schema validation error."""
        config_dict_string["plant"][0].pop("inverter")
        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape("config contains potential error"),
        ):
            ConfigReader(config_dict_string)

    def test_missing_array(self, config_dict_string: dict) -> None:
        """Test that plant with no arrays triggers length validation error."""
        config_dict_string["plant"][0]["arrays"] = []
        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape(
                "length of value must be at least 1 for dictionary value @ data['arrays']"
            ),
        ):
            ConfigReader(config_dict_string)

    def test_invalid_array_tilt(self, config_dict_string: dict) -> None:
        """Test that invalid array tilt raises a schema validation error."""
        config_dict_string["plant"][0]["arrays"][0]["tilt"] = -10.0
        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape("tilt must be between 0 ° and 90 ° (0 ° = horizontal)"),
        ):
            ConfigReader(config_dict_string)

    def test_invalid_array_azimuth(self, config_dict_string: dict) -> None:
        """Test that invalid array azimuth raises a schema validation error."""
        config_dict_string["plant"][0]["arrays"][0]["azimuth"] = -10.0
        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape("azimuth must be between 0 ° and 360 ° (0 ° = North)"),
        ):
            ConfigReader(config_dict_string)

    def test_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Test that malformed YAML raises an error."""
        malformed_yaml = tmp_path / "bad.yaml"
        malformed_yaml.write_text("general:\n  location: [unclosed", encoding="utf-8")

        with pytest.raises(yaml.YAMLError):
            ConfigReader(malformed_yaml)

    def test_missing_required_fields(self, config_dict_string: dict) -> None:
        """Test missing required fields raise a schema validation error."""
        config_dict_string.pop("general")

        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape("required key not provided @ data['general']"),
        ):
            ConfigReader(config_dict_string)

    def test_invalid_config_type(self) -> None:
        """Test that passing an invalid type raises a TypeError."""
        with pytest.raises(
            TypeError,
            match="Configuration file 12345 is not a valid path or dictionary.",
        ):
            ConfigReader(12345)  # type: ignore[arg-type]

    def test_exclusive_ac_power_inverter_keys(self, config_dict_string: dict) -> None:
        """Test that presence of both inverter and ac_power raises an error."""
        config_dict_string["plant"][0]["ac_power"] = 5000
        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape("extra keys not allowed @ data['ac_power']"),
        ):
            ConfigReader(config_dict_string)

    def test_duplicate_ac_power(self, config_dict_simple: dict) -> None:
        """We can't have both ac_power keys at the inverter and the array level."""
        config_dict_simple["plant"][0]["ac_power"] = 5000
        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape("extra keys not allowed @ data['ac_power']"),
        ):
            ConfigReader(config_dict_simple)

    def test_simple_full_mixed_config(self, config_dict_string: dict) -> None:
        """Test that a mixed config with both simple and complex keys throws an error."""
        config_dict_string["plant"][0]["ac_power"] = 5000
        config_dict_string["plant"][0].pop("inverter", None)
        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape("extra keys not allowed @ data['ac_power']"),
        ):
            ConfigReader(config_dict_string)

    @pytest.mark.parametrize("config", [TEST_CONF_STRING_PATH], indirect=True)
    def test_correct_coercion_of_types(self, config: ConfigReader) -> None:
        """Test that coercion of float/bool types works as expected."""
        conf: dict = dict(config.config)
        plant = conf["plant"][0]
        assert isinstance(plant["arrays"][0]["tilt"], float)

    def test_weather_sources_missing(self, config_dict_string: dict) -> None:
        """Test missing weather sources raise a schema validation error."""
        config_dict_string["general"]["weather"].pop("sources")
        with pytest.raises(
            vol.MultipleInvalid,
            match=re.escape("required key not provided @ data['general']['weather']"),
        ):
            ConfigReader(config_dict_string)
