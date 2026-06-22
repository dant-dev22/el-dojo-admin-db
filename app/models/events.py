"""Modelos de torneos y participación de alumnos."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin


class Tournament(CreatedAtMixin, Base):
    """Evento competitivo asociado a una organización."""

    __tablename__ = "tournaments"
    __table_args__ = (
        Index("ix_tournaments_organization_id", "organization_id"),
        Index("ix_tournaments_discipline_id", "discipline_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    discipline_id: Mapped[int | None] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    event_date: Mapped[date] = mapped_column(Date(), nullable=False)

    organization = relationship("Organization", back_populates="tournaments")
    discipline = relationship("Discipline", back_populates="tournaments")
    participations = relationship("TournamentParticipation", back_populates="tournament")


class TournamentParticipation(CreatedAtMixin, Base):
    """Participación de un alumno en un torneo."""

    __tablename__ = "tournament_participations"
    __table_args__ = (
        Index("ix_tournament_participations_tournament_id", "tournament_id"),
        Index("ix_tournament_participations_student_id", "student_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    result: Mapped[str | None] = mapped_column(String(100), nullable=True)
    weight_division: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    tournament = relationship("Tournament", back_populates="participations")
    student = relationship("Student", back_populates="tournament_participations")
