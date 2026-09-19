from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig, SQLAlchemyPlugin

from sticky.config import settings
from sticky.exception_handlers import EXCEPTION_HANDLERS
from sticky.health.endpoints import router as health_router
from sticky.logging import Logger
from sticky.logging import plugin as structlog_plugin
from sticky.models import Model
from sticky.postgres import db_session_dependency

log: Logger = structlog.get_logger()


@asynccontextmanager
async def log_start_finish(_: Litestar) -> AsyncGenerator[None]:
    log.info("Starting Sticky API")
    yield
    log.info("Sticky API stopped")


def create_app() -> Litestar:
    db_config = SQLAlchemyAsyncConfig(
        connection_string=settings.get_postgres_dsn("asyncpg"),
        metadata=Model.metadata,
        create_all=False,
    )

    app = Litestar(
        lifespan=[log_start_finish],
        dependencies={"session": db_session_dependency},
        route_handlers=[health_router],
        openapi_config=OpenAPIConfig(title="Sticky API", version="0.9.0"),
        plugins=[structlog_plugin, SQLAlchemyPlugin(db_config)],
        exception_handlers=EXCEPTION_HANDLERS,
    )

    return app


app = create_app()
