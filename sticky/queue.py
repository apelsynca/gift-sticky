import structlog
from litestar_queues import QueueConfig, QueuedTaskRecord, QueuePlugin
from litestar_queues.backends.redis import RedisBackendConfig

from sticky.config import settings
from sticky.logging import Logger

log: Logger = structlog.get_logger()


def sanitize_and_log_task_error(exc: BaseException, record: QueuedTaskRecord) -> str:
    """
    Hooks into task execution failures to log the exact error
    and format the message stored in the database.
    """
    log.error(
        "Task failed",
        task_name=record.task_name,
        task_id=record.id,
        exc_info=exc,  # This automatically appends the full traceback to your log
    )

    return f"Internal Error: {exc!s}"


queue_plugin = QueuePlugin(
    config=QueueConfig(
        queue_backend=RedisBackendConfig(url=settings.redis_url),
        task_modules=("sticky.tasks",),
        initialize_schedules=True,
        error_sanitizer=sanitize_and_log_task_error,
    )
)
