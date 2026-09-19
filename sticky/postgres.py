from collections.abc import AsyncGenerator
from typing import Literal

from litestar.datastructures import State

from sticky.config import settings
from sticky.kit.database.postgres import AsyncEngine, AsyncSession
from sticky.kit.database.postgres import create_async_engine as _create_async_engine

type ProcessName = Literal["app"]


def create_async_engine(
    process_name: ProcessName, *, pool_logging_name: str | None = None
) -> AsyncEngine:
    return _create_async_engine(
        dsn=str(settings.get_postgres_dsn("asyncpg")),
        application_name=f"{settings.ENV.value}.{process_name}",
        pool_logging_name=pool_logging_name or process_name,
        pool_size=settings.DATABASE_POOL_SIZE,
        pool_recycle=settings.DATABASE_POOL_RECYCLE_SECONDS,
        command_timeout=settings.DATABASE_COMMAND_TIMEOUT_SECONDS,
    )


async def db_session_dependency(state: State) -> AsyncGenerator[AsyncSession]:
    async with state.async_sessionmaker() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
        else:
            await session.commit()


__all__ = [
    "AsyncEngine",
    "AsyncSession",
    "create_async_engine",
    "db_session_dependency",
]
