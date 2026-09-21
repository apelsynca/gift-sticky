from litestar import get
from litestar.params import FromQuery

from sticky.routing import Router


@get("", description="Get hello world response")
async def greet(limit: FromQuery[int | None] = None) -> str:
    return f"Hello, world!\nLimit: {limit}"


router = Router(path="/hello-world", route_handlers=[greet])
