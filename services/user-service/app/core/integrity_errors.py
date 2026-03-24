"""Map SQLAlchemy ``IntegrityError`` to HTTP status and safe client messages."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.exc import IntegrityError


def _walk_cause(exc: BaseException | None) -> Iterator[BaseException]:
    """Follow ``__cause__`` only (explicit chaining), cycle-safe."""
    seen: set[int] = set()
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        yield cur
        cur = cur.__cause__


def _type_names_along_integrity(exc: IntegrityError) -> set[str]:
    """Collect exception class names from the IntegrityError and its ``orig`` chain."""
    names: set[str] = set()
    for start in (exc, exc.orig):
        if start is None:
            continue
        for link in _walk_cause(start):
            names.add(type(link).__name__)
    return names


def http_status_and_detail(exc: IntegrityError) -> tuple[int, str]:
    """
    Classify driver-level integrity failures without leaking SQL or parameters.

    Matches asyncpg/psycopg exception class names on ``__cause__`` chains under
    ``IntegrityError.orig``.
    """
    names = _type_names_along_integrity(exc)
    blob = " ".join(names)

    if any("NotNullViolation" in n for n in names):
        return (
            422,
            "A required value was missing for one or more fields.",
        )
    if any("UniqueViolation" in n for n in names):
        return (
            409,
            "A record with this identifier already exists.",
        )
    if any("ForeignKeyViolation" in n for n in names):
        return (
            400,
            "Invalid reference: related record does not exist.",
        )
    if any("CheckViolation" in n for n in names):
        return (
            422,
            "One or more values do not satisfy database constraints.",
        )
    # Fallback when driver uses uncommon wrappers but message hints at constraint class
    if "NotNullViolation" in blob:
        return (422, "A required value was missing for one or more fields.")
    if "UniqueViolation" in blob:
        return (409, "A record with this identifier already exists.")
    return (
        409,
        "The request could not be completed due to a data constraint.",
    )
