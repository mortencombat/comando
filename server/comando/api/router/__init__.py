from fastapi import APIRouter

from .devices import router as devices_router

router = APIRouter(prefix="/api")
router.include_router(devices_router)
