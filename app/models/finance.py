"""Modelos de pagos y notificaciones."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import NotificationChannel, NotificationStatus, NotificationType, PaymentMethod, PaymentRecordStatus
from app.models.mixins import CreatedAtMixin, currency_column, monetary_column


class Payment(CreatedAtMixin, Base):
    """Pago registrado para un alumno."""

    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_student_id", "student_id"),
        Index("ix_payments_organization_id", "organization_id"),
        Index("ix_payments_branch_id", "branch_id"),
        Index("ix_payments_recorded_by", "recorded_by"),
        CheckConstraint("amount > 0", name="payment_amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = monetary_column(nullable=False)
    currency: Mapped[str] = currency_column()
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)
    period_end: Mapped[date] = mapped_column(Date(), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method"),
        nullable=False,
    )
    status: Mapped[PaymentRecordStatus] = mapped_column(
        Enum(PaymentRecordStatus, name="payment_record_status"),
        nullable=False,
    )
    recorded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    student = relationship("Student", back_populates="payments")
    organization = relationship("Organization", back_populates="payments")
    branch = relationship("Branch", back_populates="payments")
    recorded_by_user = relationship("User", back_populates="payments_recorded")


class Notification(CreatedAtMixin, Base):
    """Notificación saliente relacionada o no con un alumno."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_student_id", "student_id"),
        Index("ix_notifications_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int | None] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=True,
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"),
        nullable=False,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status"),
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    student = relationship("Student", back_populates="notifications")
