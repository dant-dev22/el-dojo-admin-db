"""Enumeraciones del dominio almacenadas como ENUM nativo en MySQL."""

from __future__ import annotations

from enum import Enum

from sqlalchemy import Enum as SqlEnum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    BRANCH_ADMIN = "branch_admin"
    STUDENT = "student"


class PaymentStatus(str, Enum):
    UP_TO_DATE = "up_to_date"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"


class StudentStatus(str, Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    INACTIVE = "inactive"


class AttendanceMethod(str, Enum):
    QR = "qr"
    MANUAL = "manual"


class PaymentMethod(str, Enum):
    CASH = "cash"
    TRANSFER = "transfer"
    CARD = "card"
    OTHER = "other"


class PaymentRecordStatus(str, Enum):
    PAID = "paid"
    PENDING = "pending"
    VOID = "void"


class DevicePlatform(str, Enum):
    IOS = "ios"
    ANDROID = "android"


class NotificationType(str, Enum):
    PAYMENT_DUE = "payment_due"
    PAYMENT_OVERDUE = "payment_overdue"
    GENERAL = "general"


class NotificationChannel(str, Enum):
    PUSH = "push"
    EMAIL = "email"


class NotificationStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


def db_enum(enum_class: type[Enum], *, name: str) -> SqlEnum:
    """Crea un ENUM SQLAlchemy usando los valores reales del Enum.

    SQLAlchemy, si no se configura, tiende a usar los nombres de los miembros
    (`ORG_ADMIN`) en vez de sus valores (`org_admin`). El esquema y la migración
    inicial de este proyecto usan los valores en minúsculas, así que este helper
    mantiene ORM y base de datos alineados.
    """

    return SqlEnum(
        enum_class,
        name=name,
        values_callable=lambda enum_members: [member.value for member in enum_members],
    )
