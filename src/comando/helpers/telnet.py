import asyncio
import logging
import socket

from contextlib import asynccontextmanager
from dataclasses import KW_ONLY, dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


class ConnectionState:
    """Helper class to store mutable state for frozen TelnetConnection."""

    def __init__(self, thread_safe: bool):
        self.socket: Optional[socket.socket] = None
        self.lock: Optional[asyncio.Lock] = asyncio.Lock() if thread_safe else None

    @property
    def is_connected(self) -> bool:
        return self.socket is not None


@dataclass(frozen=True)
class Telnet:
    host: str
    port: int
    _: KW_ONLY
    timeout: int = None
    thread_safe: bool = False
    _state: ConnectionState = field(init=False, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "_state", ConnectionState(self.thread_safe))

    @asynccontextmanager
    async def session(self):
        """
        Creates an async context manager for a single connection session.
        If thread_safe is True, waits for the lock to be available.
        """

        if self._state.lock:
            await self._state.lock.acquire()

        try:
            self.connect()
            yield self
        finally:
            self.disconnect()
            if self._state.lock:
                self._state.lock.release()

    def connect(self) -> None:
        """
        Establishes a telnet connection to the specified host and port.

        Raises:
            RuntimeError: If already connected
        """
        if self._state.is_connected:
            raise RuntimeError("Already connected")

        self._state.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.timeout:
            self._state.socket.settimeout(self.timeout)
        self._state.socket.connect((self.host, self.port))

    def disconnect(self) -> None:
        """Closes the telnet connection if it exists."""
        if self._state.socket is not None:
            self._state.socket.close()
            self._state.socket = None

    def send_message(self, message: str, buffer_size: int = 4096) -> str:
        """
        Sends a message through the telnet connection and returns the response.

        Args:
            message: The message to send
            buffer_size: Size of the receiving buffer (default: 1024)

        Returns:
            The response received from the server

        Raises:
            ConnectionError: If not connected when trying to send a message
        """

        if not self._state.is_connected:
            raise ConnectionError("Not connected to telnet server")

        self._state.socket.send(message.encode("ascii") + b"\r\n")
        logger.debug("message sent to socket, awaiting response...")
        r = self._state.socket.recv(buffer_size)
        logger.debug(f"response recieved: {r}")
        return r.decode("ascii").strip()

    def __del__(self):
        """Ensures the connection is closed when the object is destroyed."""

        self.disconnect()
