from datetime import datetime
from enum import Enum, Flag, auto
from typing import Protocol


class Status(Enum):
    ON = auto()
    OFF = auto()


class Feature(Flag):
    PLAYBACK = auto()
    SWITCH = auto()
    TV = auto()
    PROCESSOR = auto()
    AUDIO = auto()


class Sensor(Protocol):
    @property
    def name(self) -> str:
        """Name of the sensor."""
        ...

    @property
    def value(self) -> float | int | str | bool:
        """Value of the sensor."""
        ...


class Command(Protocol):
    @property
    def name(self) -> str:
        """Name of the command."""
        ...

    def execute(self) -> None:
        """Execute the command."""
        ...


class Device(Protocol):
    @property
    def features(self) -> Feature:
        """Capabilities of the device."""
        ...

    @property
    def status(self) -> Status:
        """Status of the device."""
        ...

    @property
    def last_seen(self) -> datetime:
        """Last time the device was seen."""
        ...

    def poll(self) -> None:
        """Poll the device to check availability."""
        ...

    def on(self) -> None:
        """Turn the device on."""
        ...

    def off(self) -> None:
        """Turn the device off."""
        ...

    def sensors(self) -> list[Sensor]:
        """Sensors of the device."""
        ...

    def commands(self) -> list[Command]:
        """Commands of the device."""
        ...
