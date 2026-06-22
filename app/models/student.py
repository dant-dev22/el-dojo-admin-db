"""Modelos relacionados con alumnos, peso y rangos obtenidos."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PaymentStatus, StudentStatus, db_enum
from app.models.mixins import CreatedAtMixin, TimestampMixin, currency_column, monetary_column


class Student(TimestampMixin, Base):
    """Alumno inscrito en una sucursal."""

    __tablename__ = "students"
    __table_args__ = (
        Index("ix_students_organization_id", "organization_id"),
        Index("ix_students_branch_id", "branch_id"),
        Index("ix_students_user_id", "user_id"),
        Index("ix_students_primary_class_id", "primary_class_id"),
        Index("ix_students_deleted_at", "deleted_at"),
        CheckConstraint("height_cm IS NULL OR height_cm > 0", name="student_height_positive"),
        CheckConstraint("monthly_fee IS NULL OR monthly_fee >= 0", name="student_monthly_fee_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    unique_code: Mapped[str] = mapped_column(String(8), nullable=False, unique=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date(), nullable=False)
    birth_place: Mapped[str] = mapped_column(String(150), nullable=False)
    height_cm: Mapped[int | None] = mapped_column(nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enrollment_date: Mapped[date] = mapped_column(Date(), nullable=False)
    primary_class_id: Mapped[int | None] = mapped_column(
        ForeignKey("classes.id", ondelete="RESTRICT"),
        nullable=True,
    )
    monthly_fee: Mapped[Decimal | None] = monetary_column(nullable=True)
    currency: Mapped[str] = currency_column()
    next_payment_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        db_enum(PaymentStatus, name="student_payment_status"),
        nullable=False,
    )
    status: Mapped[StudentStatus] = mapped_column(
        db_enum(StudentStatus, name="student_status"),
        nullable=False,
    )
    guardian_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    guardian_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    organization = relationship("Organization", back_populates="students")
    branch = relationship("Branch", back_populates="students")
    user = relationship("User", back_populates="students")
    primary_class = relationship("MartialClass", back_populates="students")
    weight_logs = relationship("WeightLog", back_populates="student")
    ranks = relationship("StudentRank", back_populates="student")
    class_enrollments = relationship("ClassEnrollment", back_populates="student")
    attendance_records = relationship("Attendance", back_populates="student")
    payments = relationship("Payment", back_populates="student")
    notifications = relationship("Notification", back_populates="student")
    tournament_participations = relationship("TournamentParticipation", back_populates="student")


class WeightLog(CreatedAtMixin, Base):
    """Historial de peso del alumno."""

    __tablename__ = "weight_logs"
    __table_args__ = (
        Index("ix_weight_logs_student_id", "student_id"),
        Index("ix_weight_logs_recorded_by", "recorded_by"),
        Index("ix_weight_logs_student_recorded_at", "student_id", "recorded_at"),
        CheckConstraint("weight_kg > 0", name="weight_log_weight_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    weight_kg: Mapped[float] = mapped_column(nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    recorded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    student = relationship("Student", back_populates="weight_logs")
    recorded_by_user = relationship("User", back_populates="recorded_weight_logs")


class StudentRank(CreatedAtMixin, Base):
    """Asignación histórica de rango para un alumno."""

    __tablename__ = "student_ranks"
    __table_args__ = (
        Index("ix_student_ranks_student_id", "student_id"),
        Index("ix_student_ranks_discipline_id", "discipline_id"),
        Index("ix_student_ranks_rank_id", "rank_id"),
        Index("ix_student_ranks_awarded_by", "awarded_by"),
        Index("ix_student_ranks_is_current", "is_current"),
        CheckConstraint("degree >= 0", name="student_rank_degree_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    discipline_id: Mapped[int] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rank_id: Mapped[int] = mapped_column(
        ForeignKey("ranks.id", ondelete="RESTRICT"),
        nullable=False,
    )
    degree: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    awarded_date: Mapped[date] = mapped_column(Date(), nullable=False)
    awarded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    is_current: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    student = relationship("Student", back_populates="ranks")
    discipline = relationship("Discipline", back_populates="student_ranks")
    rank = relationship("Rank", back_populates="student_ranks")
    awarded_by_user = relationship("User", back_populates="awarded_ranks")
