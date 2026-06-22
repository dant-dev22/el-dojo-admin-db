"""Mixins y helpers reutilizables para los modelos."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    """Devuelve un datetime UTC sin zona para alinear con DATETIME de MySQL."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_created_column() -> Mapped[datetime]:
    """Columna created_at consistente para tablas con sello de creación."""

    return mapped_column(
        DateTime(),
        nullable=False,
        default=utc_now,
        server_default=text("UTC_TIMESTAMP()"),
    )


def utc_updated_column() -> Mapped[datetime]:
    """Columna updated_at consistente para tablas auditables."""

    return mapped_column(
        DateTime(),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=text("UTC_TIMESTAMP()"),
        server_onupdate=text("UTC_TIMESTAMP()"),
    )


class CreatedAtMixin:
    """Añade created_at en UTC."""

    created_at: Mapped[datetime] = utc_created_column()


class TimestampMixin(CreatedAtMixin):
    """Añade created_at y updated_at en UTC."""

    updated_at: Mapped[datetime] = utc_updated_column()


def currency_column() -> Mapped[str]:
    """ISO 4217 en mayúscula, con longitud suficiente para casos estándar."""

    return mapped_column(String(3), nullable=False, default="USD", server_default="USD")


def monetary_column(nullable: bool = True) -> Mapped[Decimal | None]:
    """Importes monetarios con precisión suficiente para cuotas y pagos."""

    return mapped_column(Numeric(10, 2), nullable=nullable)
