"""Modelos de organización y sucursal."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Organization(TimestampMixin, Base):
    """Nivel superior del tenant."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    branches = relationship("Branch", back_populates="organization")
    admin_assignments = relationship("AdminAssignment", back_populates="organization")
    disciplines = relationship("Discipline", back_populates="organization")
    students = relationship("Student", back_populates="organization")
    classes = relationship("MartialClass", back_populates="organization")
    payments = relationship("Payment", back_populates="organization")
    tournaments = relationship("Tournament", back_populates="organization")


class Branch(TimestampMixin, Base):
    """Sede operativa con su propia zona horaria IANA."""

    __tablename__ = "branches"
    __table_args__ = (
        Index("ix_branches_organization_id", "organization_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    qr_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    organization = relationship("Organization", back_populates="branches")
    admin_assignments = relationship("AdminAssignment", back_populates="branch")
    students = relationship("Student", back_populates="branch")
    classes = relationship("MartialClass", back_populates="branch")
    attendance_records = relationship("Attendance", back_populates="branch")
    payments = relationship("Payment", back_populates="branch")
