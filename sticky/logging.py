import contextvars
import logging.config
import typing
import uuid
from typing import Any

import structlog
from litestar.logging.config import BaseLoggingConfig, StructLoggingConfig
from litestar.plugins.structlog import StructlogConfig, StructlogPlugin
from litestar.status_codes import HTTP_404_NOT_FOUND
from litestar.types import GetLogger

from sticky.config import settings

Logger = structlog.stdlib.BoundLogger


class Logging[RendererType]:
    """Hubben logging configurator of `structlog` and `logging`.

    Customized implementation inspired by the following documentation:
    https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging
    """

    timestamper = structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False)

    @classmethod
    def get_level(cls) -> str:
        return settings.LOG_LEVEL

    @classmethod
    def get_processors(cls) -> list[Any]:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            cls.timestamper,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]

        return processors

    @classmethod
    def get_renderer(cls) -> RendererType:
        raise NotImplementedError()

    @classmethod
    def get_stdlib_config(cls) -> dict:
        level = cls.get_level()

        return {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "sticky": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        cls.get_renderer(),
                    ],
                    "foreign_pre_chain": [
                        structlog.contextvars.merge_contextvars,
                        structlog.stdlib.add_log_level,
                        structlog.stdlib.add_logger_name,
                        structlog.stdlib.PositionalArgumentsFormatter(),
                        structlog.stdlib.ExtraAdder(),
                        cls.timestamper,
                        structlog.processors.UnicodeDecoder(),
                        structlog.processors.StackInfoRenderer(),
                        structlog.processors.format_exc_info,
                    ],
                },
            },
            "handlers": {
                "default": {
                    "level": level,
                    "class": "logging.StreamHandler",
                    "formatter": "sticky",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": level,
                    "propagate": False,
                },
                # Propagate third-party loggers to the root one
                **{
                    logger: {
                        "handlers": [],
                        "propagate": True,
                    }
                    for logger in ["sqlalchemy", "uvicorn", "logtide", "litestar_queues"]
                },
            },
        }

    @classmethod
    def configure_stdlib(cls) -> None:
        logging.config.dictConfig(cls.get_stdlib_config())

    @classmethod
    def configure_structlog(cls) -> None:
        structlog.configure_once(
            processors=cls.get_processors(),
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    @classmethod
    def configure(cls) -> None:
        cls.configure_stdlib()
        cls.configure_structlog()


class Development(Logging[structlog.dev.ConsoleRenderer]):
    @classmethod
    def get_renderer(cls) -> structlog.dev.ConsoleRenderer:
        return structlog.dev.ConsoleRenderer(colors=True)


class Production(Logging[structlog.dev.ConsoleRenderer]):
    @classmethod
    def get_renderer(cls) -> structlog.dev.ConsoleRenderer:
        return structlog.dev.ConsoleRenderer(colors=False)


def get_renderer_class() -> type[Logging]:
    if settings.is_production():
        return Production
    else:
        return Development


def configure() -> None:
    get_renderer_class().configure()


class LitestarLoggingConfig(BaseLoggingConfig):
    def configure(self) -> GetLogger:
        get_renderer_class().configure_stdlib()
        return structlog.get_logger


plugin_config = StructlogConfig(
    structlog_logging_config=StructLoggingConfig(
        processors=get_renderer_class().get_processors(),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
        standard_lib_logging_config=LitestarLoggingConfig(),  # pyright: ignore[reportArgumentType]
        log_exceptions="always",
        disable_stack_trace={HTTP_404_NOT_FOUND},
    ),
    enable_middleware_logging=False,  # disable HTTP logs
)

plugin = StructlogPlugin(plugin_config)


class TraceID:
    _trace_id: typing.ClassVar[contextvars.ContextVar[str | None]] = (
        contextvars.ContextVar("sticky.trace_id", default=None)
    )

    @classmethod
    def set(cls) -> str:
        correlation_id = str(uuid.uuid4())
        cls._trace_id.set(correlation_id)
        return correlation_id

    @classmethod
    def get(cls) -> str | None:
        return cls._trace_id.get()

    @classmethod
    def clear(cls) -> None:
        cls._trace_id.set(None)
