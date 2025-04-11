"""Constants"""

from voluptuous import Coerce, Required, Schema

STRING_SYS = Schema(
    {
        Required("name"): str,
        Required("inverter"): str,
        Required("microinverter"): Coerce(bool),
        Required("arrays"): [
            {
                Required("name"): str,
                Required("tilt"): Coerce(float),
                Required("azimuth"): Coerce(float),
                Required("modules_per_string"): int,
                Required("strings"): int,
                Required("module"): str,
            }
        ],
    }
)


MICRO_SYS = Schema(
    {
        Required("name"): str,
        Required("arrays"): [
            {
                Required("name"): str,
                Required("tilt"): Coerce(float),
                Required("azimuth"): Coerce(float),
                Required("modules_per_inverter"): int,
                Required("nr_inverters"): int,
                Required("module"): str,
                Required("inverter"): str,
            }
        ],
    }
)

PLANT_SCHEMAS = [STRING_SYS, MICRO_SYS]
