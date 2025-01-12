from __future__ import annotations

import asyncio
import logging

from dataclasses import dataclass, field
from typing import Optional

import pyatv

from comando.controller import device, sensor

logger = logging.getLogger(__name__)


class DeviceListener(pyatv.interface.DeviceListener, pyatv.interface.PushListener):
    """Handles connection state changes for an Apple TV device."""

    def __init__(self, device: AppleTV):
        self.device = device

    def connection_lost(self, exception: Exception) -> None:
        """Called when connection is lost unexpectedly."""
        logger.warning(f"Connection lost to {self.device.identifier}: {exception}")
        self._handle_disconnect()

    def connection_closed(self) -> None:
        """Called when connection is closed normally."""
        logger.debug(f"Connection closed to {self.device.identifier}")
        self._handle_disconnect()

    def _handle_disconnect(self) -> None:
        """Clean up device state after disconnect."""
        self.device._atv = None
        self.device._listener = None

    def playstatus_update(self, updater, playstatus: pyatv.interface.Playing) -> None:
        """Called when play status is updated."""
        asyncio.create_task(
            self.device.raise_event(
                "playstatus_changed", "; ".join(str(playstatus).strip().split("\n"))
            )
        )

    def playstatus_error(self, updater, exception: Exception) -> None:
        """Called when there is an error getting play status."""
        logger.debug(f"Play status error for {self.device.identifier}: {exception}")


@device
@dataclass
class AppleTV:
    identifier: str
    device_id: str
    credentials: str
    _atv: Optional[pyatv.interface.AppleTV] = field(default=None, repr=False)
    _connected: bool = field(default=False, repr=False)
    _listener: Optional[DeviceListener] = field(default=None, repr=False)

    async def connect(self) -> None:
        """Connect to the Apple TV device."""
        if self._connected:
            logger.debug(f"Already connected to {self.identifier}")
            return

        loop = asyncio.get_event_loop()
        r = await pyatv.scan(identifier=self.device_id, loop=loop)
        if not r:
            raise RuntimeError(
                f"Apple TV '{self.identifier}' not found (id: {self.device_id})"
            )

        config = r[0]
        config.set_credentials(pyatv.Protocol.Companion, self.credentials)

        self._atv = await pyatv.connect(config, loop=loop)
        self._listener = DeviceListener(self)
        self._atv.listener = self._listener
        self._atv.push_updater.listener = self._listener
        self._atv.push_updater.start()
        logger.info(f"Connected to {self.identifier}")

    async def disconnect(self) -> None:
        """Disconnect from the Apple TV device."""
        if self._atv:
            self._atv.close()

    @property
    def is_connected(self) -> bool:
        """Return True if device is connected."""
        return self._atv is not None

    @sensor
    async def power_state(self) -> bool | None:
        if not self._atv:
            await self.connect()

        try:
            power_state = self._atv.power.power_state
            return power_state == pyatv.const.PowerState.On
        except Exception as e:
            logger.error(f"Failed to get power state for {self.identifier}: {e}")
            return None

    @sensor
    async def playstatus(self) -> dict | None:
        """Return the current play status of the device."""
        if not self._atv:
            await self.connect()

        try:
            status = await self._atv.metadata.playing()
            return {
                "title": status.title,
                "artist": status.artist,
                "album": status.album,
                "media_type": str(status.media_type),
                "device_state": str(status.device_state),
                "repeat": str(status.repeat),
                "shuffle": str(status.shuffle),
                "position": status.position,
                "total_time": status.total_time,
            }
        except Exception as e:
            logger.error(f"Failed to get play status for {self.identifier}: {e}")
            return None
