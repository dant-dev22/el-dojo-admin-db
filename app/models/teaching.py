"""Modelos de clases, horarios, inscripciones y asistencia."""

from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AttendanceMethod, db_enum
from app.models.mixins import CreatedAtMixin, TimestampMixin


class MartialClass(TimestampMixin, Base):
    """Clase ofertada por una sucursal."""

    __tablename__ = "classes"
    __table_args__ = (
        Index("ix_classes_organization_id", "organization_id"),
        Index("ix_classes_branch_id", "branch_id"),
        Index("ix_classes_discipline_id", "discipline_id"),
        CheckConstraint("capacity IS NULL OR capacity > 0", name="class_capacity_positive"),
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
    discipline_id: Mapped[int] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    instructor_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    capacity: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    organization = relationship("Organization", back_populates="classes")
    branch = relationship("Branch", back_populates="classes")
    discipline = relationship("Discipline", back_populates="classes")
    students = relationship("Student", back_populates="primary_class")
    schedules = relationship("ClassSchedule", back_populates="class_obj")
    enrollments = relationship("ClassEnrollment", back_populates="class_obj")
    attendance_records = relationship("Attendance", back_populates="class_obj")


class ClassSchedule(CreatedAtMixin, Base):
    """Bloque semanal recurrente de una clase."""

    __tablename__ = "class_schedules"
    __table_args__ = (
        Index("ix_class_schedules_class_id", "class_id"),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="class_schedule_day_of_week_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    day_of_week: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(nullable=False)
    end_time: Mapped[time] = mapped_column(nullable=False)

    class_obj = relationship("MartialClass", back_populates="schedules")


class ClassEnrollment(CreatedAtMixin, Base):
    """Inscripción activa o histórica de un alumno a una clase."""

    __tablename__ = "class_enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "class_id", name="uq_class_enrollments_student_class"),
        Index("ix_class_enrollments_student_id", "student_id"),
        Index("ix_class_enrollments_class_id", "class_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    student = relationship("Student", back_populates="class_enrollments")
    class_obj = relationship("MartialClass", back_populates="enrollments")


class Attendance(CreatedAtMixin, Base):
    """Registro de check-in del alumno."""

    __tablename__ = "attendance"
    __table_args__ = (
        Index("ix_attendance_student_id", "student_id"),
        Index("ix_attendance_class_id", "class_id"),
        Index("ix_attendance_branch_id", "branch_id"),
        Index("ix_attendance_student_check_in_at", "student_id", "check_in_at"),
        Index("ix_attendance_registered_by", "registered_by"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    class_id: Mapped[int | None] = mapped_column(
        ForeignKey("classes.id", ondelete="RESTRICT"),
        nullable=True,
    )
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    check_in_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    method: Mapped[AttendanceMethod] = mapped_column(
        db_enum(AttendanceMethod, name="attendance_method"),
        nullable=False,
    )
    registered_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    student = relationship("Student", back_populates="attendance_records")
    class_obj = relationship("MartialClass", back_populates="attendance_records")
    branch = relationship("Branch", back_populates="attendance_records")
    registered_by_user = relationship("User", back_populates="attendance_records")
