"""Agrega first_name y last_name a users."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260720_0002"
down_revision = "20260620_0001"
branch_labels = None
depends_on = None


def _has_column(column_names: set[str], column_name: str) -> bool:
    return column_name in column_names


def upgrade() -> None:
    """Agrega nombres visibles al usuario autenticable."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}

    if not _has_column(user_columns, "first_name"):
        op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=True))

    if not _has_column(user_columns, "last_name"):
        op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Revierte el agregado de nombres visibles en users."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}

    if _has_column(user_columns, "last_name"):
        op.drop_column("users", "last_name")

    if _has_column(user_columns, "first_name"):
        op.drop_column("users", "first_name")
