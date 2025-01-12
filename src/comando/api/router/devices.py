from typing import Any

from fastapi import APIRouter, HTTPException

from comando.controller import Controller

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/")
async def list_devices() -> list[str]:
    """List all registered devices"""
    return Controller.get_instance().list_devices()


@router.get("/{device_name}/sensors")
async def get_device_sensors(device_name: str) -> dict[str, Any]:
    """Get all sensor values for a specific device"""
    try:
        device = Controller.get_instance().get_device(device_name)

        # Get all sensor properties (decorated with @sensor)
        sensor_values = {}
        for attr_name in device.sensors:
            if attr_name.startswith("_"):
                continue
            try:
                sensor_values[attr_name] = await getattr(device, attr_name)
            except Exception as e:
                sensor_values[attr_name] = str(e)

        return sensor_values
    except KeyError as e:
        raise HTTPException(
            status_code=404, detail=f"Device '{device_name}' not found"
        ) from e
