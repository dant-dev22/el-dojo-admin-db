"""Modelos relacionados con usuarios y administración."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DevicePlatform, UserRole
from app.models.mixins import CreatedAtMixin, TimestampMixin


class User(TimestampMixin, Base):
    """Usuario autenticable del sistema."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    admin_assignments = relationship("AdminAssignment", back_populates="user")
    students = relationship("Student", back_populates="user")
    recorded_weight_logs = relationship("WeightLog", back_populates="recorded_by_user")
    awarded_ranks = relationship("StudentRank", back_populates="awarded_by_user")
    attendance_records = relationship("Attendance", back_populates="registered_by_user")
    payments_recorded = relationship("Payment", back_populates="recorded_by_user")
    device_tokens = relationship("DeviceToken", back_populates="user")


class AdminAssignment(CreatedAtMixin, Base):
    """Asignación de alcance administrativo sobre una organización o sucursal."""

    __tablename__ = "admin_assignments"
    __table_args__ = (
        Index("ix_admin_assignments_user_id", "user_id"),
        Index("ix_admin_assignments_organization_id", "organization_id"),
        Index("ix_admin_assignments_branch_id", "branch_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    branch_id: Mapped[int | None] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=True,
    )

    user = relationship("User", back_populates="admin_assignments")
    organization = relationship("Organization", back_populates="admin_assignments")
    branch = relationship("Branch", back_populates="admin_assignments")


class DeviceToken(CreatedAtMixin, Base):
    """Tokens para notificaciones push por usuario."""

    __tablename__ = "device_tokens"
    __table_args__ = (
        Index("ix_device_tokens_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[DevicePlatform] = mapped_column(
        Enum(DevicePlatform, name="device_platform"),
        nullable=False,
    )

    user = relationship("User", back_populates="device_tokens")
