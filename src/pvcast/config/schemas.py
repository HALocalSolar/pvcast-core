"""PV-system validation schema (Voluptuous)."""

from __future__ import annotations

from typing import Final

from voluptuous import (
    All,
    Coerce,
    Invalid,
    Length,
    Range,
    Required,
    Schema,
)


def _positive_int(msg: str = "must be a positive integer") -> All:
    return All(Coerce(int), Range(min=1, msg=msg))


STR: Final = All(str, Length(min=1, msg="cannot be empty"))
TILT: Final = All(
    Coerce(float),
    Range(0.0, 90.0, msg="tilt must be between 0 ° and 90 ° (0 ° = horizontal)"),
)
AZIMUTH: Final = All(
    Coerce(float),
    Range(0.0, 360.0, msg="azimuth must be between 0 ° and 360 ° (0 ° = North)"),
)

ARRAY_SIMPLE_MICRO: Final = Schema(
    {
        Required("name"): STR,
        Required("tilt"): TILT,
        Required("azimuth"): AZIMUTH,
        Required("dc_power"): _positive_int(),
        Required("ac_power"): _positive_int(),
    },
    extra=False,
)

ARRAY_SIMPLE_STRING: Final = Schema(
    {
        Required("name"): STR,
        Required("tilt"): TILT,
        Required("azimuth"): AZIMUTH,
        Required("dc_power"): _positive_int(),
    },
    extra=False,
)

ARRAY_FULL_MICRO: Final = Schema(
    {
        Required("name"): STR,
        Required("tilt"): TILT,
        Required("azimuth"): AZIMUTH,
        Required("modules_per_string"): _positive_int(),
        Required("nr_inverters"): _positive_int(),
        Required("module"): STR,
        Required("inverter"): STR,
    },
    extra=False,
)

ARRAY_FULL_STRING: Final = Schema(
    {
        Required("name"): STR,
        Required("tilt"): TILT,
        Required("azimuth"): AZIMUTH,
        Required("modules_per_string"): _positive_int(),
        Required("strings"): _positive_int(),
        Required("module"): STR,
    },
    extra=False,
)

SYSTEM_SIMPLE_MICRO: Final = Schema(
    {
        Required("name"): STR,
        Required("arrays"): All([ARRAY_SIMPLE_MICRO], Length(min=1)),
    },
    extra=False,
)

SYSTEM_SIMPLE_STRING: Final = Schema(
    {
        Required("name"): STR,
        Required("ac_power"): _positive_int(),
        Required("arrays"): All([ARRAY_SIMPLE_STRING], Length(min=1)),
    },
    extra=False,
)

SYSTEM_FULL_MICRO: Final = Schema(
    {
        Required("name"): STR,
        Required("arrays"): All([ARRAY_FULL_MICRO], Length(min=1)),
    },
    extra=False,
)

SYSTEM_FULL_STRING: Final = Schema(
    {
        Required("name"): STR,
        Required("inverter"): STR,
        Required("arrays"): All([ARRAY_FULL_STRING], Length(min=1)),
    },
    extra=False,
)


def _dispatch(data: object) -> object:
    """Pick the first schema that validates *data* or raise a combined error."""
    excs: set[Invalid] = set()
    for variant in (
        SYSTEM_SIMPLE_MICRO,
        SYSTEM_SIMPLE_STRING,
        SYSTEM_FULL_MICRO,
        SYSTEM_FULL_STRING,
    ):
        try:
            return variant(data)  # type: ignore[arg-type]
        except Invalid as exc:
            excs.add(exc)
            continue
    msg = f"config contains potential errors: \n{'\n'.join(str(exc) for exc in excs)}"
    raise Invalid(msg)


PLANT_SCHEMA = Schema(_dispatch)

__all__: list[str] = [
    "PLANT_SCHEMA",
    "SYSTEM_FULL_MICRO",
    "SYSTEM_FULL_STRING",
    "SYSTEM_SIMPLE_MICRO",
    "SYSTEM_SIMPLE_STRING",
]
