from typing import Any, NamedTuple

from sqlalchemy import Select, Subquery, literal


class PaginationParams(NamedTuple):
    page: int
    limit: int


def count_subquery(statement: Select[Any]) -> Subquery:
    """Build a count-safe subquery from a Select.

    `.subquery()` materializes every mapped column of the underlying entity,
    including those marked `deferred=True`. For count queries we only need
    row cardinality, so project a literal to avoid referencing (or loading)
    unused columns.
    """
    return statement.with_only_columns(literal(1)).order_by(None).subquery()
