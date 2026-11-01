from litestar import post
from litestar.di import NamedDependency
from litestar_queues import QueueService

from sticky.admin_auth import require_admin
from sticky.routing import Router
from sticky.sticker_pack.tasks import update_sticker_pack_task


@post("/update", description="Start sticker pack update", guards=[require_admin])
async def update(queue_service: NamedDependency[QueueService]) -> dict[str, str]:
    result = await queue_service.enqueue(update_sticker_pack_task)

    return {"task_id": str(result.id), "status": result.status or "pending"}


router = Router(path="/sticker-pack", route_handlers=[update], include_in_schema=False)
