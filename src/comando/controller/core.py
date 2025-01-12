from __future__ import annotations

import asyncio
import inspect
import logging
import time

from functools import wraps
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    Protocol,
    runtime_checkable,
)

logger = logging.getLogger(__name__)


class Controller:
    """
    Controller class that manages devices and their events.
    Implements the singleton pattern.
    """

    _instance = None

    @classmethod
    def get_instance(cls) -> Controller:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.devices: set[DeviceProtocol] = set()
        self.event_subscribers: dict[str, set[Callable[[Any], Awaitable[None]]]] = {}
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self):
        """Initialize the controller and set up the event loop."""
        logger.info("Connecting devices")
        self.event_loop = asyncio.get_running_loop()
        for device in self.devices:
            try:
                await device.connect()
            except Exception as e:
                logger.warning(f"Failed to connect device {device.identifier}: {e}")
        logger.info("Controller started")

    async def stop(self):
        """Cleanup and stop all devices."""
        for device in self.devices:
            try:
                await device.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting device {device.identifier}: {e}")

        self.devices.clear()
        self.event_subscribers.clear()
        logger.info("Controller stopped")

    def register_device(self, device: DeviceProtocol) -> None:
        """
        Register a device with the controller.

        Args:
            device: Instance of a class decorated with @device that implements DeviceProtocol
        """

        if not isinstance(device, DeviceProtocol) or not hasattr(
            device, "_device_config"
        ):
            raise TypeError(
                f"Device {device.__class__.__name__} does not adhere to DeviceProtocol and/or does not use @device decorator"
            )

        # Validate identifier characters (allowing alphanumeric and underscores)
        if not device.identifier.replace("_", "").isalnum():
            raise ValueError(
                f"Device name '{device.name}' contains invalid characters. Use only alphanumeric and underscores."
            )

        if device in self.devices:
            raise ValueError(
                f"Device with identifier '{device.identifier}' already registered"
            )

        self.devices.add(device)
        logger.info(
            f"Registered device: {device.identifier} ({device.__class__.__name__})"
        )

    def get_device[T: DeviceProtocol](
        self, identifier: str, device_type: type[T] | None = None
    ) -> T | DeviceProtocol:
        """
        Get a registered device by name.

        Args:
            name: Name of the device to retrieve
            device_type: Optional type hint for the device

        Returns:
            The device instance
        """
        for device in self.devices:
            if device.identifier != identifier:
                continue
            if device_type and not isinstance(device, device_type):
                raise TypeError(
                    f"Device '{identifier}' is not of type {device_type.__name__}"
                )
            return device

        raise KeyError(f"No device registered with identifier '{identifier}'")

    def subscribe(self, device_name: str, event_name: str, callback: callable) -> None:
        """
        Subscribe to device events.

        Args:
            device_name: Name of the device to subscribe to
            event_name: Name of the event to subscribe to
            callback: Async callback function to be called when event occurs
        """
        if not inspect.iscoroutinefunction(callback):
            raise ValueError("Callback must be an async function")

        key = f"{device_name}.{event_name}"
        if key not in self.event_subscribers:
            self.event_subscribers[key] = set()
        self.event_subscribers[key].add(callback)

    def unsubscribe(
        self, device_name: str, event_name: str, callback: callable
    ) -> None:
        """
        Unsubscribe from device events.

        Args:
            device_name: Name of the device
            event_name: Name of the event
            callback: Callback function to unsubscribe
        """
        key = f"{device_name}.{event_name}"
        if key in self.event_subscribers:
            self.event_subscribers[key].discard(callback)
            if not self.event_subscribers[key]:
                del self.event_subscribers[key]

    async def handle_event(
        self, device: DeviceProtocol, event_name: str, value: Any
    ) -> None:
        """
        Handle events from devices and dispatch to subscribers.

        Args:
            device_name: Name of the device that raised the event
            event_name: Name of the event
            value: Event value/data
        """

        key = f"{device.identifier}.{event_name}"
        logger.debug(f"Event raised: {key} = {value}")
        subscribers = self.event_subscribers.get(key, set())

        for callback in subscribers:
            try:
                await callback(value)
            except Exception as e:
                logger.error(f"Error in event callback for {key}: {e}")

    def list_devices(self) -> list[DeviceProtocol]:
        """Return a list of all registered devices."""
        return [device.identifier for device in self.devices]

    def list_subscriptions(self) -> dict[str, set[callable]]:
        """Return a dictionary of all event subscriptions."""
        return dict(self.event_subscribers)


@runtime_checkable
class DeviceProtocol(Protocol):
    """Protocol defining the required interface for devices"""

    identifier: str

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...


def device(
    ttl: Optional[float] = None,
    timeout: Optional[float] = None,
    **kwargs,
) -> Callable:
    """
    Class decorator for device configuration. Sets device-wide defaults and implements
    raise_event method automatically.

    Args:
        ttl (float, optional): Default time to live for cached sensor values in seconds.
        timeout (float, optional): Default timeout for sensor operations in seconds.
        **kwargs: Additional device-wide configuration parameters.
    """

    def decorator(cls):
        # Store all configuration in a single dictionary
        nonlocal ttl, timeout  # Add this line to access outer scope variables

        config = {"ttl": ttl, "timeout": timeout, **kwargs}
        cls._device_config = config

        async def raise_event(self, event_name: str, value: any) -> None:
            """
            Raises an event with the given name and value.
            This method is automatically added by the @device decorator.

            Args:
                event_name (str): Name of the event to raise
                value (any): Value associated with the event
            """
            controller = Controller.get_instance()
            await controller.handle_event(self, event_name, value)

        def __hash__(self):
            return hash(self.identifier)

        @property
        def sensors(self) -> list[str]:
            return [
                attr_name
                for attr_name, attr in inspect.getmembers(self.__class__)
                if type(attr).__name__ == "SensorProperty"
            ]

        @property
        def timeout(self) -> int:
            return self._device_config.get("timeout")

        cls.raise_event = raise_event
        cls.__hash__ = __hash__
        cls.sensors = sensors
        cls.timeout = timeout

        # Add _polling_tasks initialization to __init__
        original_init = cls.__init__

        def __init__(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self._polling_tasks: dict[str, asyncio.Task] = {}

        cls.__init__ = __init__

        # Modify connect/disconnect to handle polling tasks
        original_connect = cls.connect

        async def connect(self) -> None:
            await original_connect(self)
            self._polling_tasks = {}

            # Start polling tasks for all sensor properties that have poll_interval
            for attr_name, attr in inspect.getmembers(self.__class__):
                if (
                    type(attr).__name__ == "SensorProperty"
                    and attr.poll_interval is not None
                ):
                    task = asyncio.create_task(attr._polling_loop(self))
                    logger.debug(f"Created polling loop for {attr_name}")
                    self._polling_tasks[attr_name] = task

        cls.connect = connect

        original_disconnect = cls.disconnect

        async def disconnect(self) -> None:
            # Cancel any active polling tasks
            for task in self._polling_tasks.values():
                task.cancel()
            try:
                await asyncio.gather(
                    *self._polling_tasks.values(), return_exceptions=True
                )
            except Exception:
                pass
            self._polling_tasks.clear()
            await original_disconnect(self)

        cls.disconnect = disconnect

        return cls

    # Handle both @device and @device() syntax
    if callable(ttl):
        c = ttl
        ttl = None
        return decorator(c)

    return decorator


def sensor(
    ttl: Optional[float] = None,
    timeout: Optional[float] = None,
    poll_interval: Optional[float] = None,
) -> Callable:
    """
    Decorator that monitors changes in sensor values, implements caching with TTL,
    and raises events when they change.

    Args:
        ttl: Time to live for cached values in seconds
        timeout: Timeout for sensor operations in seconds
        poll_interval: Interval in seconds to automatically poll the sensor
    """

    def decorator(func: Callable) -> Callable:
        cache = {}

        class SensorProperty:
            def __init__(self, fget, fset=None):
                self.fget = fget
                self.fset = fset
                self.poll_interval = (
                    poll_interval  # Store poll_interval as instance variable
                )
                wraps(fget)(self)

            async def _polling_loop(self, obj):
                """Background polling loop for the sensor."""
                while True:
                    try:
                        await self.__get__(obj)  # Poll the sensor
                        await asyncio.sleep(poll_interval)
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Error polling sensor {func.__name__}: {e}")
                        await asyncio.sleep(1)  # Brief delay on error

            def __get__(self, obj, objtype=None):
                if obj is None:
                    return self

                async def async_get():
                    # Use obj.__class__ instead of objtype
                    if not hasattr(obj.__class__, "_device_config"):
                        raise TypeError(
                            f"Class '{obj.__class__.__name__}' using @sensor decorator must be decorated with @device"
                        )

                    # Get effective TTL and timeout (property values or device defaults)
                    effective_ttl = ttl
                    effective_timeout = timeout
                    if hasattr(obj.__class__, "_device_config"):
                        if effective_ttl is None:
                            effective_ttl = obj.__class__._device_config.get("ttl")
                        if effective_timeout is None:
                            effective_timeout = obj.__class__._device_config.get(
                                "timeout"
                            )

                    instance_key = (id(obj), func.__name__)
                    current_time = time.monotonic()

                    async def get_sensor_value():
                        if inspect.iscoroutinefunction(self.fget):
                            return await self.fget(obj)
                        return self.fget(obj)

                    def should_use_cache():
                        if effective_ttl is None:
                            return False
                        if instance_key not in cache:
                            return False
                        last_value, last_time = cache[instance_key]
                        return (current_time - last_time) < effective_ttl

                    logger.debug(f"Reading {func.__name__} sensor")

                    try:
                        # Use cached value if available and not expired
                        if should_use_cache():
                            value = cache[instance_key][0]
                            logger.debug(
                                f"Using cached value for {func.__name__}: {value}"
                            )
                            return value

                        # Get fresh value with timeout if specified
                        if effective_timeout is not None:
                            current_value = await asyncio.wait_for(
                                get_sensor_value(), timeout=effective_timeout
                            )
                        else:
                            current_value = await get_sensor_value()

                        # Log the resolved value
                        logger.debug(f"Read value for {func.__name__}: {current_value}")

                        # Always update the cache timestamp when we get a fresh value
                        if (
                            instance_key not in cache
                            or cache[instance_key][0] != current_value
                        ):
                            # Value changed or is new - raise event
                            cache[instance_key] = (current_value, current_time)
                            event_name = f"{func.__name__}_changed"
                            asyncio.create_task(
                                obj.raise_event(event_name, current_value)
                            )
                        else:
                            # Value hasn't changed, but update timestamp
                            cache[instance_key] = (current_value, current_time)

                        return current_value

                    except asyncio.TimeoutError as e:
                        raise TimeoutError(
                            f"Sensor {func.__name__} operation timed out after {effective_timeout} seconds"
                        ) from e

                return async_get()

            def __set__(self, obj, value):
                if self.fset is None:
                    raise AttributeError("can't set attribute")
                self.fset(obj, value)
                instance_key = (id(obj), func.__name__)
                if instance_key in cache:
                    del cache[instance_key]

            def setter(self, fset):
                return type(self)(self.fget, fset)

        return SensorProperty(func)

    if callable(ttl):
        f = ttl
        ttl = None
        return decorator(f)

    return decorator
