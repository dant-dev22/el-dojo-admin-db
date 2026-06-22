"""Registro central de modelos para SQLAlchemy y Alembic."""

from app.models.curriculum import Discipline, Rank
from app.models.events import Tournament, TournamentParticipation
from app.models.finance import Notification, Payment
from app.models.organization import Branch, Organization
from app.models.student import Student, StudentRank, WeightLog
from app.models.teaching import Attendance, ClassEnrollment, ClassSchedule, MartialClass
from app.models.user import AdminAssignment, DeviceToken, User

__all__ = [
    "AdminAssignment",
    "Attendance",
    "Branch",
    "ClassEnrollment",
    "ClassSchedule",
    "DeviceToken",
    "Discipline",
    "MartialClass",
    "Notification",
    "Organization",
    "Payment",
    "Rank",
    "Student",
    "StudentRank",
    "Tournament",
    "TournamentParticipation",
    "User",
    "WeightLog",
]
