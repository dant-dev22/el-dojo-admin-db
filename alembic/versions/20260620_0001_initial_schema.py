"""Migración inicial del esquema de Fase 1."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260620_0001"
down_revision = None
branch_labels = None
depends_on = None


MYSQL_TABLE_ARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}


def upgrade() -> None:
    """Crea todas las tablas del dominio inicial."""

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=3), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
        **MYSQL_TABLE_ARGS,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("super_admin", "org_admin", "branch_admin", "student", name="user_role"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.UniqueConstraint("email", name="uq_users_email"),
        **MYSQL_TABLE_ARGS,
    )

    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("qr_secret", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT", name="fk_branches_organization_id_organizations"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_branches_organization_id", "branches", ["organization_id"])

    op.create_table(
        "disciplines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT", name="fk_disciplines_organization_id_organizations"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_disciplines_organization_id", "disciplines", ["organization_id"])

    op.create_table(
        "ranks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("discipline_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("max_degrees", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.CheckConstraint("order_index >= 0", name="rank_order_index_non_negative"),
        sa.CheckConstraint("max_degrees >= 0", name="rank_max_degrees_non_negative"),
        sa.ForeignKeyConstraint(["discipline_id"], ["disciplines.id"], ondelete="RESTRICT", name="fk_ranks_discipline_id_disciplines"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_ranks_discipline_id", "ranks", ["discipline_id"])

    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("discipline_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructor_name", sa.String(length=150), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.CheckConstraint("capacity IS NULL OR capacity > 0", name="class_capacity_positive"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT", name="fk_classes_branch_id_branches"),
        sa.ForeignKeyConstraint(["discipline_id"], ["disciplines.id"], ondelete="RESTRICT", name="fk_classes_discipline_id_disciplines"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT", name="fk_classes_organization_id_organizations"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_classes_organization_id", "classes", ["organization_id"])
    op.create_index("ix_classes_branch_id", "classes", ["branch_id"])
    op.create_index("ix_classes_discipline_id", "classes", ["discipline_id"])

    op.create_table(
        "admin_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT", name="fk_admin_assignments_branch_id_branches"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT", name="fk_admin_assignments_organization_id_organizations"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT", name="fk_admin_assignments_user_id_users"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_admin_assignments_user_id", "admin_assignments", ["user_id"])
    op.create_index("ix_admin_assignments_organization_id", "admin_assignments", ["organization_id"])
    op.create_index("ix_admin_assignments_branch_id", "admin_assignments", ["branch_id"])

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("unique_code", sa.String(length=8), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("birth_place", sa.String(length=150), nullable=False),
        sa.Column("height_cm", sa.Integer(), nullable=True),
        sa.Column("photo_url", sa.String(length=500), nullable=True),
        sa.Column("enrollment_date", sa.Date(), nullable=False),
        sa.Column("primary_class_id", sa.Integer(), nullable=True),
        sa.Column("monthly_fee", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("next_payment_date", sa.Date(), nullable=True),
        sa.Column(
            "payment_status",
            sa.Enum("up_to_date", "due_soon", "overdue", name="student_payment_status"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("active", "frozen", "inactive", name="student_status"),
            nullable=False,
        ),
        sa.Column("guardian_name", sa.String(length=150), nullable=True),
        sa.Column("guardian_phone", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("height_cm IS NULL OR height_cm > 0", name="student_height_positive"),
        sa.CheckConstraint("monthly_fee IS NULL OR monthly_fee >= 0", name="student_monthly_fee_non_negative"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT", name="fk_students_branch_id_branches"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT", name="fk_students_organization_id_organizations"),
        sa.ForeignKeyConstraint(["primary_class_id"], ["classes.id"], ondelete="RESTRICT", name="fk_students_primary_class_id_classes"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT", name="fk_students_user_id_users"),
        sa.UniqueConstraint("unique_code", name="uq_students_unique_code"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_students_organization_id", "students", ["organization_id"])
    op.create_index("ix_students_branch_id", "students", ["branch_id"])
    op.create_index("ix_students_user_id", "students", ["user_id"])
    op.create_index("ix_students_primary_class_id", "students", ["primary_class_id"])
    op.create_index("ix_students_deleted_at", "students", ["deleted_at"])

    op.create_table(
        "device_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.Enum("ios", "android", name="device_platform"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT", name="fk_device_tokens_user_id_users"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_device_tokens_user_id", "device_tokens", ["user_id"])

    op.create_table(
        "class_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.CheckConstraint("day_of_week BETWEEN 0 AND 6", name="class_schedule_day_of_week_range"),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="RESTRICT", name="fk_class_schedules_class_id_classes"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_class_schedules_class_id", "class_schedules", ["class_id"])

    op.create_table(
        "class_enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="RESTRICT", name="fk_class_enrollments_class_id_classes"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT", name="fk_class_enrollments_student_id_students"),
        sa.UniqueConstraint("student_id", "class_id", name="uq_class_enrollments_student_class"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_class_enrollments_student_id", "class_enrollments", ["student_id"])
    op.create_index("ix_class_enrollments_class_id", "class_enrollments", ["class_id"])

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=True),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("check_in_at", sa.DateTime(), nullable=False),
        sa.Column("method", sa.Enum("qr", "manual", name="attendance_method"), nullable=False),
        sa.Column("registered_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT", name="fk_attendance_branch_id_branches"),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="RESTRICT", name="fk_attendance_class_id_classes"),
        sa.ForeignKeyConstraint(["registered_by"], ["users.id"], ondelete="RESTRICT", name="fk_attendance_registered_by_users"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT", name="fk_attendance_student_id_students"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_attendance_student_id", "attendance", ["student_id"])
    op.create_index("ix_attendance_class_id", "attendance", ["class_id"])
    op.create_index("ix_attendance_branch_id", "attendance", ["branch_id"])
    op.create_index("ix_attendance_registered_by", "attendance", ["registered_by"])
    op.create_index("ix_attendance_student_check_in_at", "attendance", ["student_id", "check_in_at"])

    op.create_table(
        "weight_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("recorded_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.CheckConstraint("weight_kg > 0", name="weight_log_weight_positive"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"], ondelete="RESTRICT", name="fk_weight_logs_recorded_by_users"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT", name="fk_weight_logs_student_id_students"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_weight_logs_student_id", "weight_logs", ["student_id"])
    op.create_index("ix_weight_logs_recorded_by", "weight_logs", ["recorded_by"])
    op.create_index("ix_weight_logs_student_recorded_at", "weight_logs", ["student_id", "recorded_at"])

    op.create_table(
        "student_ranks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("discipline_id", sa.Integer(), nullable=False),
        sa.Column("rank_id", sa.Integer(), nullable=False),
        sa.Column("degree", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("awarded_date", sa.Date(), nullable=False),
        sa.Column("awarded_by", sa.Integer(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.CheckConstraint("degree >= 0", name="student_rank_degree_non_negative"),
        sa.ForeignKeyConstraint(["awarded_by"], ["users.id"], ondelete="RESTRICT", name="fk_student_ranks_awarded_by_users"),
        sa.ForeignKeyConstraint(["discipline_id"], ["disciplines.id"], ondelete="RESTRICT", name="fk_student_ranks_discipline_id_disciplines"),
        sa.ForeignKeyConstraint(["rank_id"], ["ranks.id"], ondelete="RESTRICT", name="fk_student_ranks_rank_id_ranks"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT", name="fk_student_ranks_student_id_students"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_student_ranks_student_id", "student_ranks", ["student_id"])
    op.create_index("ix_student_ranks_discipline_id", "student_ranks", ["discipline_id"])
    op.create_index("ix_student_ranks_rank_id", "student_ranks", ["rank_id"])
    op.create_index("ix_student_ranks_awarded_by", "student_ranks", ["awarded_by"])
    op.create_index("ix_student_ranks_is_current", "student_ranks", ["is_current"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=False),
        sa.Column("method", sa.Enum("cash", "transfer", "card", "other", name="payment_method"), nullable=False),
        sa.Column("status", sa.Enum("paid", "pending", "void", name="payment_record_status"), nullable=False),
        sa.Column("recorded_by", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.CheckConstraint("amount > 0", name="payment_amount_positive"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT", name="fk_payments_branch_id_branches"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT", name="fk_payments_organization_id_organizations"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"], ondelete="RESTRICT", name="fk_payments_recorded_by_users"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT", name="fk_payments_student_id_students"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_payments_student_id", "payments", ["student_id"])
    op.create_index("ix_payments_organization_id", "payments", ["organization_id"])
    op.create_index("ix_payments_branch_id", "payments", ["branch_id"])
    op.create_index("ix_payments_recorded_by", "payments", ["recorded_by"])

    op.create_table(
        "tournaments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("discipline_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.ForeignKeyConstraint(["discipline_id"], ["disciplines.id"], ondelete="RESTRICT", name="fk_tournaments_discipline_id_disciplines"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT", name="fk_tournaments_organization_id_organizations"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_tournaments_organization_id", "tournaments", ["organization_id"])
    op.create_index("ix_tournaments_discipline_id", "tournaments", ["discipline_id"])

    op.create_table(
        "tournament_participations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("result", sa.String(length=100), nullable=True),
        sa.Column("weight_division", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT", name="fk_tournament_participations_student_id_students"),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"], ondelete="RESTRICT", name="fk_tournament_participations_tournament_id_tournaments"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_tournament_participations_tournament_id", "tournament_participations", ["tournament_id"])
    op.create_index("ix_tournament_participations_student_id", "tournament_participations", ["student_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column(
            "type",
            sa.Enum("payment_due", "payment_overdue", "general", name="notification_type"),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.Enum("push", "email", name="notification_channel"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "sent", "failed", name="notification_status"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("UTC_TIMESTAMP()")),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT", name="fk_notifications_student_id_students"),
        **MYSQL_TABLE_ARGS,
    )
    op.create_index("ix_notifications_student_id", "notifications", ["student_id"])
    op.create_index("ix_notifications_status", "notifications", ["status"])


def downgrade() -> None:
    """Revierte completamente el esquema inicial."""

    op.drop_index("ix_notifications_status", table_name="notifications")
    op.drop_index("ix_notifications_student_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_tournament_participations_student_id", table_name="tournament_participations")
    op.drop_index("ix_tournament_participations_tournament_id", table_name="tournament_participations")
    op.drop_table("tournament_participations")

    op.drop_index("ix_tournaments_discipline_id", table_name="tournaments")
    op.drop_index("ix_tournaments_organization_id", table_name="tournaments")
    op.drop_table("tournaments")

    op.drop_index("ix_payments_recorded_by", table_name="payments")
    op.drop_index("ix_payments_branch_id", table_name="payments")
    op.drop_index("ix_payments_organization_id", table_name="payments")
    op.drop_index("ix_payments_student_id", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_student_ranks_is_current", table_name="student_ranks")
    op.drop_index("ix_student_ranks_awarded_by", table_name="student_ranks")
    op.drop_index("ix_student_ranks_rank_id", table_name="student_ranks")
    op.drop_index("ix_student_ranks_discipline_id", table_name="student_ranks")
    op.drop_index("ix_student_ranks_student_id", table_name="student_ranks")
    op.drop_table("student_ranks")

    op.drop_index("ix_weight_logs_student_recorded_at", table_name="weight_logs")
    op.drop_index("ix_weight_logs_recorded_by", table_name="weight_logs")
    op.drop_index("ix_weight_logs_student_id", table_name="weight_logs")
    op.drop_table("weight_logs")

    op.drop_index("ix_attendance_student_check_in_at", table_name="attendance")
    op.drop_index("ix_attendance_registered_by", table_name="attendance")
    op.drop_index("ix_attendance_branch_id", table_name="attendance")
    op.drop_index("ix_attendance_class_id", table_name="attendance")
    op.drop_index("ix_attendance_student_id", table_name="attendance")
    op.drop_table("attendance")

    op.drop_index("ix_class_enrollments_class_id", table_name="class_enrollments")
    op.drop_index("ix_class_enrollments_student_id", table_name="class_enrollments")
    op.drop_table("class_enrollments")

    op.drop_index("ix_class_schedules_class_id", table_name="class_schedules")
    op.drop_table("class_schedules")

    op.drop_index("ix_device_tokens_user_id", table_name="device_tokens")
    op.drop_table("device_tokens")

    op.drop_index("ix_students_deleted_at", table_name="students")
    op.drop_index("ix_students_primary_class_id", table_name="students")
    op.drop_index("ix_students_user_id", table_name="students")
    op.drop_index("ix_students_branch_id", table_name="students")
    op.drop_index("ix_students_organization_id", table_name="students")
    op.drop_table("students")

    op.drop_index("ix_admin_assignments_branch_id", table_name="admin_assignments")
    op.drop_index("ix_admin_assignments_organization_id", table_name="admin_assignments")
    op.drop_index("ix_admin_assignments_user_id", table_name="admin_assignments")
    op.drop_table("admin_assignments")

    op.drop_index("ix_classes_discipline_id", table_name="classes")
    op.drop_index("ix_classes_branch_id", table_name="classes")
    op.drop_index("ix_classes_organization_id", table_name="classes")
    op.drop_table("classes")

    op.drop_index("ix_ranks_discipline_id", table_name="ranks")
    op.drop_table("ranks")

    op.drop_index("ix_disciplines_organization_id", table_name="disciplines")
    op.drop_table("disciplines")

    op.drop_index("ix_branches_organization_id", table_name="branches")
    op.drop_table("branches")

    op.drop_table("users")
    op.drop_table("organizations")
