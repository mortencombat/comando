import logging
import os

from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from importlib import resources
from logging.handlers import RotatingFileHandler
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import comando

from comando.controller import Controller

from .config import devices
from .router import router


def setup_logging() -> None:
    # Convert string levels to logging constants
    file_level = getattr(
        logging, os.getenv("COMANDO_FILE_LOG_LEVEL", "INFO").upper(), logging.INFO
    )
    console_level = getattr(
        logging, os.getenv("COMANDO_CONSOLE_LOG_LEVEL", "WARNING").upper(), logging.INFO
    )

    # Create root logger and set to lowest level of the two
    root_logger = logging.getLogger()
    root_logger.setLevel(min(file_level, console_level))

    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Setup file handler
    file_handler = RotatingFileHandler(
        filename=resources.files(comando) / "comando.log",
        encoding="utf-8",
        mode="a",
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5,
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # Remove any existing handlers and add new ones
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


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

    # Serve the comando app as static files
    static_path = resources.files(comando) / "static"
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="comando")

    logger.info("FastAPI application setup complete")
    return app
