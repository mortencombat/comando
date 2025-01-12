import logging

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import httpx

from comando.controller import device, sensor

COMMAND_TPL: str = "http://{host}:{port}/devices/{cmd}"
POLL_INTERVAL: float = 1.0

logger = logging.getLogger(__name__)


class Source(Enum):
    TOSLINK = "Toslink"
    HDMI = "HDMI"
    SPDIF = "SPDIF"


@device(ttl=0.5)
@dataclass
class MiniDSP:
    identifier: str
    host: str
    port: int
    serial: int
    _device_index: Optional[int] = None
    _device_status: Dict[str, Any] = None

    async def _request(
        self,
        command: str | None = None,
        method: str = "GET",
        json: Dict[str, Any] | None = None,
    ) -> dict:
        """Make an HTTP request to the MiniDSP device.

        Args:
            command: The command to send to the device
            method: HTTP method ("GET" or "POST")
            json: Optional JSON data for POST requests

        Returns:
            dict: The JSON response from the device

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails with a 4XX or 5XX status
            httpx.RequestError: If the HTTP request fails due to network issues
            ValueError: If the response is not valid JSON
        """
        url = COMMAND_TPL.format(host=self.host, port=self.port, cmd=command or "")

        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }

        try:
            async with httpx.AsyncClient(verify=False) as client:
                logger.debug("Making %s request to %s", method, url)
                response = await client.request(method, url, headers=headers, json=json)
                response.raise_for_status()
                return response.json() if method == "GET" else {}
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error while making request: %s", e)
            raise
        except httpx.RequestError as e:
            logger.error("Network error while making request: %s", e)
            raise
        except ValueError as e:
            logger.error("Invalid JSON response from MiniDSP device: %s", e)
            raise

    async def _apply_config(self, config: Dict[str, Any]) -> None:
        """Apply a configuration to the MiniDSP device.

        Args:
            config: Configuration dictionary to apply

        Raises:
            RuntimeError: If device is not connected
        """
        if self._device_index is None:
            raise RuntimeError("Device not connected")

        await self._request(
            method="POST",
            command=f"{self._device_index}/config",
            json=config,
        )

    async def connect(self) -> None:
        """Connect to the MiniDSP device."""
        try:
            devices = await self._request()

            # Find our device by serial number
            for idx, dev in enumerate(devices):
                if dev.get("version", {}).get("serial") == self.serial:
                    self._device_index = idx
                    logger.info(
                        f"Connected to MiniDSP device with serial {self.serial} at index {idx}"
                    )
                    return

            raise ValueError(f"Device with serial {self.serial} not found")

        except Exception as e:
            logger.error(f"Failed to connect to MiniDSP: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the MiniDSP device."""
        self._device_index = None

    async def _status(self) -> Dict[str, Any]:
        """Get the current device status."""
        if self._device_index is None:
            raise RuntimeError("Device not connected")

        self._device_status = await self._request(command=str(self._device_index))
        return self._device_status

    @sensor(poll_interval=POLL_INTERVAL)
    async def volume(self) -> float:
        """Current master volume in dB."""
        status = await self._status
        return status["master"]["volume"]

    @volume.setter
    async def volume(self, value: float) -> None:
        """Current master volume in dB."""
        await self._apply_config({"master_status": {"volume": value}})

    @sensor(poll_interval=POLL_INTERVAL)
    async def mute(self) -> bool:
        """Current master mute state."""
        status = await self._status
        return status["master"]["mute"]

    @mute.setter
    async def mute(self, value: bool) -> None:
        """Current master mute state."""
        await self._apply_config({"master_status": {"mute": value}})

    @sensor(poll_interval=POLL_INTERVAL)
    async def dirac(self) -> bool:
        """Current master Dirac state."""
        status = await self._status
        return status["master"]["dirac"]

    @dirac.setter
    async def dirac(self, value: bool) -> None:
        """Current master Dirac state."""
        await self._apply_config({"master_status": {"dirac": value}})

    @sensor(poll_interval=POLL_INTERVAL)
    async def preset(self) -> int:
        """Current active preset number."""
        status = await self._status
        return status["master"]["preset"]

    @preset.setter
    async def preset(self, value: int) -> None:
        """Current active preset number."""
        await self._apply_config({"master_status": {"preset": value}})

    @sensor(poll_interval=POLL_INTERVAL)
    async def source(self) -> Source | str:
        """Current active input source.

        Returns Source enum value if known, or raw string if unknown."""
        status = await self._status
        source_str = status["master"]["source"]
        try:
            return Source(source_str)
        except ValueError:
            logger.warning("Unknown source value received: %s", source_str)
            return source_str

    @source.setter
    async def source(self, value: Source) -> None:
        """Current active input source."""
        await self._apply_config({"master_status": {"source": value.value}})

    @sensor
    async def input_levels(self) -> tuple[float]:
        """Current input levels in dB."""
        status = await self._status
        return tuple(status["input_levels"])

    @sensor
    async def output_levels(self) -> tuple[float]:
        """Current output levels in dB."""
        status = await self._status
        return tuple(status["output_levels"])
