import logging

from dataclasses import dataclass
from enum import Enum, IntEnum

import httpx

from comando.controller import device, sensor

COMMAND_TPL: str = "https://{host}/httpapi.asp?command={cmd}"
POLL_INTERVAL: float = 1.0

logger = logging.getLogger(__name__)


class PlayerMode(IntEnum):
    UNRECOGNIZED = -1
    NONE = 0
    AIRPLAY = 1
    DLNA = 2
    SPOTIFY_CONNECT = 31
    TIDAL_CONNECT = 32
    AUX_IN = 40
    BLUETOOTH = 41
    OPTICAL_IN = 43
    SLAVE = 99


class PlayerStatus(Enum):
    STOPPED = "stop"
    PLAYING = "play"
    LOADING = "loading"
    PAUSED = "pause"


@device(ttl=0.5)
@dataclass
class WiiM:
    identifier: str
    host: str

    async def connect(self) -> None:
        """Connect to the WiiM device."""
        pass

    async def disconnect(self) -> None:
        """Disconnect from the WiiM device."""
        pass

    async def _make_request(self, command: str) -> dict:
        """Make an HTTP request to the WiiM device.

        Args:
            command: The command to send to the device

        Returns:
            dict: The JSON response from the device

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails with a 4XX or 5XX status
            httpx.RequestError: If the HTTP request fails due to network issues
            ValueError: If the response is not valid JSON
        """
        url = COMMAND_TPL.format(host=self.host, cmd=command)
        # Define headers to prevent caching
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        try:
            async with httpx.AsyncClient(verify=False) as client:
                logger.debug("Making request to %s", url)
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error while making request: %s", e)
            raise
        except httpx.RequestError as e:
            logger.error("Network error while making request: %s", e)
            raise
        except ValueError as e:
            logger.error("Invalid JSON response from WiiM device: %s", e)
            raise

    @sensor
    async def _player_status(self) -> dict[str, str]:
        """Get the current player status from the WiiM device.

        Returns:
            dict[str, str]: The player status information

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails with a 4XX or 5XX status
            httpx.RequestError: If the HTTP request fails due to network issues
            ValueError: If the response is not valid JSON
        """
        return await self._make_request("getPlayerStatus")

    @sensor
    async def player_mode(self) -> PlayerMode:
        """Get the current player mode of the WiiM device.

        Returns:
            PlayerMode: The current player mode:
                - NONE: No playback mode active
                - AIRPLAY: AirPlay streaming
                - DLNA: DLNA streaming
                - SPOTIFY_CONNECT: Spotify Connect
                - TIDAL_CONNECT: Tidal Connect
                - AUX_IN: Auxiliary input
                - BLUETOOTH: Bluetooth connection
                - OPTICAL_IN: Optical input
                - SLAVE: Slave mode
                - UNRECOGNIZED: Unknown mode

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails with a 4XX or 5XX status
            httpx.RequestError: If the HTTP request fails due to network issues
            ValueError: If the response is not valid JSON
        """
        status = await self._player_status
        try:
            return PlayerMode(int(status.get("mode", -1)))
        except (ValueError, KeyError):
            return PlayerMode.UNRECOGNIZED

    @sensor(poll_interval=POLL_INTERVAL)
    async def player_status(self) -> PlayerStatus:
        """Get the current playback status of the WiiM device.

        Returns:
            PlayerStatus: The current playback status:
                - STOPPED: Playback is stopped
                - PLAYING: Currently playing
                - LOADING: Loading content
                - PAUSED: Playback is paused

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails with a 4XX or 5XX status
            httpx.RequestError: If the HTTP request fails due to network issues
            ValueError: If the response is not valid JSON
        """
        status = await self._player_status
        try:
            return PlayerStatus(status.get("status", "stop"))
        except ValueError:
            return PlayerStatus.STOPPED

    @sensor
    async def playlist_count(self) -> int:
        """Get the total number of items in the current playlist.

        Returns:
            int: The total number of items in the playlist, or 0 if unavailable

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails with a 4XX or 5XX status
            httpx.RequestError: If the HTTP request fails due to network issues
            ValueError: If the response is not valid JSON
        """
        status = await self._player_status
        try:
            return int(status.get("plicount", 0))
        except (ValueError, KeyError):
            return 0

    @sensor
    async def playlist_index(self) -> int:
        """Get the current index in the playlist (1-based).

        Returns:
            int: The current playlist position, or 0 if unavailable

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails with a 4XX or 5XX status
            httpx.RequestError: If the HTTP request fails due to network issues
            ValueError: If the response is not valid JSON
        """
        status = await self._player_status
        try:
            return int(status.get("plicurr", 0))
        except (ValueError, KeyError):
            return 0
