from litestar import get
from litestar.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from sticky.postgres import AsyncSession
from sticky.routing import Router


@get("/healthz", description="Health endpoint", include_in_schema=False)
async def healthz(db_session: AsyncSession) -> dict[str, str]:
    try:
        await db_session.execute(select(1))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=503, detail="Database is not available") from e

    return {"status": "ok"}


router = Router(path="/", route_handlers=[healthz])
