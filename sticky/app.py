from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin

from sticky.exception_handlers import EXCEPTION_HANDLERS
from sticky.health.endpoints import router as health_router
from sticky.logging import Logger
from sticky.logging import plugin as structlog_plugin
from sticky.postgres import db_config

log: Logger = structlog.get_logger()


@asynccontextmanager
async def log_start_finish(_: Litestar) -> AsyncGenerator[None]:
    log.info("Starting Sticky API")
    yield
    log.info("Sticky API stopped")


def create_app() -> Litestar:
    return Litestar(
        lifespan=[log_start_finish],
        route_handlers=[health_router],
        openapi_config=OpenAPIConfig(title="Sticky API", version="0.9.0"),
        plugins=[structlog_plugin, SQLAlchemyPlugin(db_config)],
        exception_handlers=EXCEPTION_HANDLERS,
    )


app = create_app()
