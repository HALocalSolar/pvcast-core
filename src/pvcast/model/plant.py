"""PV plant model."""

from __future__ import annotations


class PVPlant:
    """Implements the entire PV model chain based on the parameters set in
    config.yaml.

    This class is basically a wrapper around pvlib. Each entry in the plant
    list in config.yaml file should be instantiated as a PVModelChain object.
    In case of a PV system with microinverters, each microinverter is
    represented by one PVModelChain object.

    :param config: The PV plant configuration dictionary.
    :param loc: The location of the PV plant.
    """

    def __init__(self) -> None:
        """Class constructor."""
