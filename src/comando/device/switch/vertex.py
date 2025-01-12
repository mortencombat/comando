from __future__ import annotations

import logging
import re
import socket

from comando.controller import DeviceProtocol, device, sensor
from comando.helpers.telnet import Telnet

logger = logging.getLogger(__name__)

"""
TODO:
Timeout should be applied correctly considering both device-wide and
sensor-specific values

Only one telnet connection at a time is supported by the Vertex. Ensure that commands are queued.
Consider moving this to a separate class.
"""


@device(timeout=5, ttl=1)
class Vertex2(DeviceProtocol):
    def __init__(self, identifier: str, host: str, port: int):
        self.identifier = identifier
        self._connection = Telnet(
            host, port, timeout=self._device_config["timeout"], thread_safe=True
        )

    async def disconnect(self) -> None:
        pass

    async def send_command(self, command: str) -> str:
        try:
            logger.debug(f"Sending command: {command}")
            async with self._connection.session():
                r = self._connection.send_message(command)
                logger.debug(f"Received response: {r}")
                return r
        except socket.timeout as e:
            logger.error(f"Timeout while communicating with Vertex2: {e}")
            raise ConnectionError(
                f"Timeout while communicating with Vertex2: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Failed to communicate with Vertex2: {e}")
            raise ConnectionError(f"Failed to communicate with Vertex2: {e}") from e

    @sensor
    async def input_tx0(self) -> int:
        r = await self.send_command("get inseltx0")
        match = re.match(r"inseltx0\s+(\d+)", r.strip())
        if not match:
            logger.error(f"Failed to parse response: '{r}'")
            raise ValueError(f"Unexpected response format: {r}")
        value = int(match.group(1))
        return value

    @sensor
    async def input_tx1(self) -> int:
        r = await self.send_command("get inseltx1")
        match = re.match(r"inseltx1\s+(\d+)", r.strip())
        if not match:
            logger.error(f"Failed to parse response: '{r}'")
            raise ValueError(f"Unexpected response format: {r}")
        value = int(match.group(1))
        return value

    @sensor
    async def cec(self) -> bool:
        r = await self.send_command("get cec")
        match = re.match(r"cec\s+(on|off)", r.strip())
        if not match:
            logger.error(f"Failed to parse response: '{r}'")
            raise ValueError(f"Unexpected response format: {r}")
        return match.group(1) == "on"

    @sensor
    async def osd(self) -> bool:
        r = await self.send_command("get osd")
        match = re.match(r"osd\s+(on|off)", r.strip())
        if not match:
            logger.error(f"Failed to parse response: '{r}'")
            raise ValueError(f"Unexpected response format: {r}")
        return match.group(1) == "on"
