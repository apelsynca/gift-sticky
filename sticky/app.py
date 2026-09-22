from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar_queues import QueueConfig, QueuePlugin

from sticky.exception_handlers import EXCEPTION_HANDLERS
from sticky.health.endpoints import router as health_router
from sticky.hello_world.endpoints import router as hello_world_router
from sticky.logging import Logger
from sticky.logging import plugin as structlog_plugin
from sticky.middlewares import proxy_headers_middleware
from sticky.postgres import db_config
from sticky.sqladmin import sqladmin_plugin
from sticky.sticker_pack.endpoints import router as sticker_pack_router

log: Logger = structlog.get_logger()


@asynccontextmanager
async def log_start_finish(_: Litestar) -> AsyncGenerator[None]:
    log.info("Starting Sticky API")
    yield
    log.info("Sticky API stopped")


def create_app() -> Litestar:
    queue_plugin = QueuePlugin(
        config=QueueConfig(task_modules=("sticky.tasks",), initialize_schedules=True)
    )

    return Litestar(
        lifespan=[log_start_finish],
        route_handlers=[health_router, hello_world_router, sticker_pack_router],
        openapi_config=OpenAPIConfig(title="Sticky API", version="0.9.9"),
        plugins=[
            structlog_plugin,
            SQLAlchemyPlugin(db_config),
            queue_plugin,
            sqladmin_plugin,
        ],
        middleware=[proxy_headers_middleware],
        exception_handlers=EXCEPTION_HANDLERS,
    )


app = create_app()
