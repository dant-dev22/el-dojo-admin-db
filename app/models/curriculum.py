"""Modelos de disciplinas y rangos."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin


class Discipline(CreatedAtMixin, Base):
    """Disciplina configurable por organización."""

    __tablename__ = "disciplines"
    __table_args__ = (
        Index("ix_disciplines_organization_id", "organization_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    organization = relationship("Organization", back_populates="disciplines")
    ranks = relationship("Rank", back_populates="discipline")
    classes = relationship("MartialClass", back_populates="discipline")
    student_ranks = relationship("StudentRank", back_populates="discipline")
    tournaments = relationship("Tournament", back_populates="discipline")


class Rank(CreatedAtMixin, Base):
    """Rangos posibles dentro de una disciplina."""

    __tablename__ = "ranks"
    __table_args__ = (
        Index("ix_ranks_discipline_id", "discipline_id"),
        CheckConstraint("order_index >= 0", name="rank_order_index_non_negative"),
        CheckConstraint("max_degrees >= 0", name="rank_max_degrees_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    discipline_id: Mapped[int] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order_index: Mapped[int] = mapped_column(nullable=False)
    max_degrees: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")

    discipline = relationship("Discipline", back_populates="ranks")
    student_ranks = relationship("StudentRank", back_populates="rank")
