# """Test unit conversion utilities."""

# from __future__ import annotations

# import typing

# import pandas as pd
# import pytest

# from src.pvcast.util.units import convert_unit


# class TestUnitConversion:
#     """Test unit conversion utilities."""

#     # define valid test cases for speed conversion
#     # fmt: off
#     valid_speed_test_cases: typing.ClassVar[list[tuple[str, str, pd.Series]]] = [
#         ("m/s", "km/h", pd.Series([-36.0, 0.0, 90.0, 360.0, 133.2], dtype=float)),
#         ("km/h", "m/s", pd.Series([-2.78, 0.0, 6.94, 27.78, 10.28], dtype=float)),
#         ("mi/h", "m/s", pd.Series([-4.47, 0.0, 11.18, 44.70, 16.54], dtype=float)),
#     ]
#     # fmt: on

#     # define invalid test cases for speed conversion
#     invalid_speed_test_cases: typing.ClassVar[list[tuple[str, str]]] = [
#         ("m/s", "invalid_unit"),
#         ("invalid_unit", "km/h"),
#         ("invalid_unit", "invalid_unit"),
#         ("invalid_unit", "mi/h"),
#     ]

#     # Define test data
#     unit_conv_data = pd.Series(
#         "temperature",
#         [-10.0, 0.0, 25.0, 100.0, 37.0],
#         dtype=float,
#     )

#     # fahrenheit to celsius conversion
#     f_to_c_out = pd.Series(
#         "temperature",
#         [-23.3333, -17.7778, -3.8889, 37.7778, 2.7778],
#         dtype=float,
#     )

#     # define valid test cases for temperature conversion
#     # fmt: off
#     valid_temperature_test_cases: typing.ClassVar[list[tuple[str, str, pd.Series]]] = [
#         ("°F", "°C", f_to_c_out),
#         ("°F", "C", f_to_c_out),
#         ("F", "°C", f_to_c_out),
#         ("F", "C", f_to_c_out),
#         ("C", "C", unit_conv_data),
#     ]
#     # fmt: on

#     # define invalid test cases for temperature conversion
#     invalid_temperature_test_cases: typing.ClassVar[list[tuple[str, str]]] = [
#         ("C", "invalid_unit"),
#         ("invalid_unit", "C"),
#         ("invalid_unit", "invalid_unit"),
#         ("invalid_unit", "F"),
#     ]

#     @pytest.mark.parametrize(
#         ("from_unit", "to_unit", "expected"),
#         valid_temperature_test_cases + valid_speed_test_cases,
#     )
#     def test_valid_conversion(
#         self,
#         from_unit: str,
#         to_unit: str,
#         expected: pd.Series,
#     ) -> None:
#         """Test timedelta_to_pl_duration function."""
#         result = convert_unit(self.unit_conv_data, from_unit, to_unit)
#         assert isinstance(result, pd.Series)
#         # assert_series_equal(
#         #     result,
#         #     expected,
#         #     check_dtype=False,
#         #     atol=0.01,
#         #     check_exact=False,
#         #     check_names=False,
#         # )

#     @pytest.mark.parametrize(
#         ("from_unit", "to_unit"),
#         invalid_temperature_test_cases + invalid_speed_test_cases,
#     )
#     def test_invalid_conversion(self, from_unit: str, to_unit: str) -> None:
#         """Test invalid conversions."""
#         with pytest.raises(
#             ValueError,
#             match=rf"Conversion from \[{from_unit}\] to \[{to_unit}\] not supported.",
#         ):
#             convert_unit(self.unit_conv_data, from_unit, to_unit)

#     def test_invalid_data_type(self) -> None:
#         """Test invalid data type list instead of pd.Series."""
#         with pytest.raises(TypeError, match="Data must be a pd.Series."):
#             convert_unit([0, 25, 100, 37], "F", "C")  # type: ignore[arg-type]
