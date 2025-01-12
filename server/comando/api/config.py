import logging

from importlib import resources

import tomllib

logger = logging.getLogger(__name__)


def get_devices() -> None:
    # Read configuration
    try:
        config_path = resources.files("comando").joinpath("comando.toml")
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return

    # Create devices
    from comando.device.playback.appletv import AppleTV
    from comando.device.playback.wiim import WiiM
    from comando.device.processor.minidsp import MiniDSP
    from comando.device.switch.vertex import Vertex2

    device_map = {
        "appletv": AppleTV,
        "vertex2": Vertex2,
        "wiim": WiiM,
        "minidsp": MiniDSP,
    }
    devices = []
    for device_config in config["devices"]:
        if "identifier" not in device_config:
            logger.warning("Skipped device with missing identifier")
            continue
        if device_config["identifier"] not in device_map:
            logger.warning(
                f"Unsupported device identifier: {device_config["identifier"]}"
            )
            continue
        devices.append(device_map[device_config["identifier"]](**device_config))

    return devices


devices = get_devices()
