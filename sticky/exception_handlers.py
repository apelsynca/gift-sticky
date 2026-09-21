import msgspec
from litestar import Request, Response
from litestar.exceptions import ValidationException
from litestar.serialization import default_serializer
from litestar.types import ExceptionHandlersMap

from sticky.exceptions import StickyError, StickyValidationError


def sticky_exception_handler(_: Request, exc: StickyError) -> Response:
    return Response(
        status_code=exc.status_code,
        content={"error": type(exc).__name__, "detail": exc.message},
        headers=exc.headers,
    )


def to_jsonable(obj: object) -> object:
    return msgspec.to_builtins(obj, enc_hook=default_serializer)


def sticky_validation_exception_handler(
    _: Request, exc: StickyValidationError
) -> Response:
    return Response(
        status_code=422,
        content={"error": type(exc).__name__, "detail": to_jsonable(exc.errors())},
    )


def validation_exception_handler(_: Request, exc: ValidationException) -> Response:
    return Response(
        status_code=422,
        content={"error": type(exc).__name__, "detail": to_jsonable(exc.extra)},
    )


EXCEPTION_HANDLERS: ExceptionHandlersMap = {
    ValidationException: validation_exception_handler,
    StickyValidationError: sticky_validation_exception_handler,
    StickyError: sticky_exception_handler,
}
