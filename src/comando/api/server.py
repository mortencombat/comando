import logging
import os

from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from logging.handlers import RotatingFileHandler
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from comando.controller import Controller

from .config import devices
from .router import router


def setup_logging() -> None:
    loglevel = os.getenv("COMANDO_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, loglevel, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            RotatingFileHandler(
                filename="comando.log",
                encoding="utf-8",
                mode="a",
                maxBytes=1024 * 1024,  # 1 MB
                backupCount=5,
            ),
            logging.StreamHandler(),
        ],
    )


setup_logging()
logger = logging.getLogger(__name__)


def lifespan_factory() -> Callable[[FastAPI], _AsyncGeneratorContextManager[Any]]:
    """Factory to create a lifespan async context manager for Comando."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Initializing Comando controller and devices")
        controller = Controller.get_instance()

        for device in devices:
            logger.debug(
                f"Registering device: {device.identifier} ({device.__class__.__name__})"
            )
            controller.register_device(device)

        logger.info("Starting controller")
        await controller.start()

        yield

        # Shutdown
        if controller:
            logger.info("Shutting down controller")
            await controller.stop()
            logger.info("Controller shutdown complete")

    return lifespan


def create_app() -> FastAPI:
    """Creates and configures a FastAPI application."""
    logger.info("Creating FastAPI application")

    lifespan = lifespan_factory()
    app = FastAPI(title="Comando", lifespan=lifespan)

    # CORS middleware configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add middleware to disable caching
    @app.middleware("http")
    async def add_cache_control_header(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    app.include_router(router)

    logger.info("FastAPI application setup complete")
    return app
