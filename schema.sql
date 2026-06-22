-- Schema de referencia para MySQL 8
-- Engine: InnoDB
-- Charset: utf8mb4

CREATE TABLE organizations (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(3) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    updated_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    UNIQUE KEY uq_organizations_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('super_admin', 'org_admin', 'branch_admin', 'student') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    updated_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE branches (
    id INT NOT NULL AUTO_INCREMENT,
    organization_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    country VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    timezone VARCHAR(64) NOT NULL,
    qr_secret VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    updated_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_branches_organization_id (organization_id),
    CONSTRAINT fk_branches_organization_id_organizations
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE disciplines (
    id INT NOT NULL AUTO_INCREMENT,
    organization_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_disciplines_organization_id (organization_id),
    CONSTRAINT fk_disciplines_organization_id_organizations
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ranks (
    id INT NOT NULL AUTO_INCREMENT,
    discipline_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    order_index INT NOT NULL,
    max_degrees INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_ranks_discipline_id (discipline_id),
    CONSTRAINT ck_ranks_rank_order_index_non_negative CHECK (order_index >= 0),
    CONSTRAINT ck_ranks_rank_max_degrees_non_negative CHECK (max_degrees >= 0),
    CONSTRAINT fk_ranks_discipline_id_disciplines
        FOREIGN KEY (discipline_id) REFERENCES disciplines (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE classes (
    id INT NOT NULL AUTO_INCREMENT,
    organization_id INT NOT NULL,
    branch_id INT NOT NULL,
    discipline_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT NULL,
    instructor_name VARCHAR(150) NULL,
    capacity INT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    updated_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_classes_organization_id (organization_id),
    KEY ix_classes_branch_id (branch_id),
    KEY ix_classes_discipline_id (discipline_id),
    CONSTRAINT ck_classes_class_capacity_positive CHECK (capacity IS NULL OR capacity > 0),
    CONSTRAINT fk_classes_organization_id_organizations
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_classes_branch_id_branches
        FOREIGN KEY (branch_id) REFERENCES branches (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_classes_discipline_id_disciplines
        FOREIGN KEY (discipline_id) REFERENCES disciplines (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE admin_assignments (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    organization_id INT NOT NULL,
    branch_id INT NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_admin_assignments_user_id (user_id),
    KEY ix_admin_assignments_organization_id (organization_id),
    KEY ix_admin_assignments_branch_id (branch_id),
    CONSTRAINT fk_admin_assignments_user_id_users
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_admin_assignments_organization_id_organizations
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_admin_assignments_branch_id_branches
        FOREIGN KEY (branch_id) REFERENCES branches (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE students (
    id INT NOT NULL AUTO_INCREMENT,
    organization_id INT NOT NULL,
    branch_id INT NOT NULL,
    unique_code VARCHAR(8) NOT NULL,
    user_id INT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    birth_place VARCHAR(150) NOT NULL,
    height_cm INT NULL,
    photo_url VARCHAR(500) NULL,
    enrollment_date DATE NOT NULL,
    primary_class_id INT NULL,
    monthly_fee DECIMAL(10,2) NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    next_payment_date DATE NULL,
    payment_status ENUM('up_to_date', 'due_soon', 'overdue') NOT NULL,
    status ENUM('active', 'frozen', 'inactive') NOT NULL,
    guardian_name VARCHAR(150) NULL,
    guardian_phone VARCHAR(50) NULL,
    notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    updated_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    deleted_at DATETIME NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_students_unique_code (unique_code),
    KEY ix_students_organization_id (organization_id),
    KEY ix_students_branch_id (branch_id),
    KEY ix_students_user_id (user_id),
    KEY ix_students_primary_class_id (primary_class_id),
    KEY ix_students_deleted_at (deleted_at),
    CONSTRAINT ck_students_student_height_positive CHECK (height_cm IS NULL OR height_cm > 0),
    CONSTRAINT ck_students_student_monthly_fee_non_negative CHECK (monthly_fee IS NULL OR monthly_fee >= 0),
    CONSTRAINT fk_students_organization_id_organizations
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_students_branch_id_branches
        FOREIGN KEY (branch_id) REFERENCES branches (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_students_user_id_users
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_students_primary_class_id_classes
        FOREIGN KEY (primary_class_id) REFERENCES classes (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE device_tokens (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    platform ENUM('ios', 'android') NOT NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_device_tokens_user_id (user_id),
    CONSTRAINT fk_device_tokens_user_id_users
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE class_schedules (
    id INT NOT NULL AUTO_INCREMENT,
    class_id INT NOT NULL,
    day_of_week INT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_class_schedules_class_id (class_id),
    CONSTRAINT ck_class_schedules_class_schedule_day_of_week_range CHECK (day_of_week BETWEEN 0 AND 6),
    CONSTRAINT fk_class_schedules_class_id_classes
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE class_enrollments (
    id INT NOT NULL AUTO_INCREMENT,
    student_id INT NOT NULL,
    class_id INT NOT NULL,
    enrolled_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    UNIQUE KEY uq_class_enrollments_student_class (student_id, class_id),
    KEY ix_class_enrollments_student_id (student_id),
    KEY ix_class_enrollments_class_id (class_id),
    CONSTRAINT fk_class_enrollments_student_id_students
        FOREIGN KEY (student_id) REFERENCES students (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_class_enrollments_class_id_classes
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE attendance (
    id INT NOT NULL AUTO_INCREMENT,
    student_id INT NOT NULL,
    class_id INT NULL,
    branch_id INT NOT NULL,
    check_in_at DATETIME NOT NULL,
    method ENUM('qr', 'manual') NOT NULL,
    registered_by INT NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_attendance_student_id (student_id),
    KEY ix_attendance_class_id (class_id),
    KEY ix_attendance_branch_id (branch_id),
    KEY ix_attendance_registered_by (registered_by),
    KEY ix_attendance_student_check_in_at (student_id, check_in_at),
    CONSTRAINT fk_attendance_student_id_students
        FOREIGN KEY (student_id) REFERENCES students (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_attendance_class_id_classes
        FOREIGN KEY (class_id) REFERENCES classes (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_attendance_branch_id_branches
        FOREIGN KEY (branch_id) REFERENCES branches (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_attendance_registered_by_users
        FOREIGN KEY (registered_by) REFERENCES users (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE weight_logs (
    id INT NOT NULL AUTO_INCREMENT,
    student_id INT NOT NULL,
    weight_kg FLOAT NOT NULL,
    recorded_at DATETIME NOT NULL,
    recorded_by INT NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_weight_logs_student_id (student_id),
    KEY ix_weight_logs_recorded_by (recorded_by),
    KEY ix_weight_logs_student_recorded_at (student_id, recorded_at),
    CONSTRAINT ck_weight_logs_weight_log_weight_positive CHECK (weight_kg > 0),
    CONSTRAINT fk_weight_logs_student_id_students
        FOREIGN KEY (student_id) REFERENCES students (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_weight_logs_recorded_by_users
        FOREIGN KEY (recorded_by) REFERENCES users (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE student_ranks (
    id INT NOT NULL AUTO_INCREMENT,
    student_id INT NOT NULL,
    discipline_id INT NOT NULL,
    rank_id INT NOT NULL,
    degree INT NOT NULL DEFAULT 0,
    awarded_date DATE NOT NULL,
    awarded_by INT NULL,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_student_ranks_student_id (student_id),
    KEY ix_student_ranks_discipline_id (discipline_id),
    KEY ix_student_ranks_rank_id (rank_id),
    KEY ix_student_ranks_awarded_by (awarded_by),
    KEY ix_student_ranks_is_current (is_current),
    CONSTRAINT ck_student_ranks_student_rank_degree_non_negative CHECK (degree >= 0),
    CONSTRAINT fk_student_ranks_student_id_students
        FOREIGN KEY (student_id) REFERENCES students (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_student_ranks_discipline_id_disciplines
        FOREIGN KEY (discipline_id) REFERENCES disciplines (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_student_ranks_rank_id_ranks
        FOREIGN KEY (rank_id) REFERENCES ranks (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_student_ranks_awarded_by_users
        FOREIGN KEY (awarded_by) REFERENCES users (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE payments (
    id INT NOT NULL AUTO_INCREMENT,
    student_id INT NOT NULL,
    organization_id INT NOT NULL,
    branch_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    paid_at DATETIME NOT NULL,
    method ENUM('cash', 'transfer', 'card', 'other') NOT NULL,
    status ENUM('paid', 'pending', 'void') NOT NULL,
    recorded_by INT NOT NULL,
    notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_payments_student_id (student_id),
    KEY ix_payments_organization_id (organization_id),
    KEY ix_payments_branch_id (branch_id),
    KEY ix_payments_recorded_by (recorded_by),
    CONSTRAINT ck_payments_payment_amount_positive CHECK (amount > 0),
    CONSTRAINT fk_payments_student_id_students
        FOREIGN KEY (student_id) REFERENCES students (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_payments_organization_id_organizations
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_payments_branch_id_branches
        FOREIGN KEY (branch_id) REFERENCES branches (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_payments_recorded_by_users
        FOREIGN KEY (recorded_by) REFERENCES users (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tournaments (
    id INT NOT NULL AUTO_INCREMENT,
    organization_id INT NOT NULL,
    discipline_id INT NULL,
    name VARCHAR(150) NOT NULL,
    location VARCHAR(150) NULL,
    event_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_tournaments_organization_id (organization_id),
    KEY ix_tournaments_discipline_id (discipline_id),
    CONSTRAINT fk_tournaments_organization_id_organizations
        FOREIGN KEY (organization_id) REFERENCES organizations (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_tournaments_discipline_id_disciplines
        FOREIGN KEY (discipline_id) REFERENCES disciplines (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tournament_participations (
    id INT NOT NULL AUTO_INCREMENT,
    tournament_id INT NOT NULL,
    student_id INT NOT NULL,
    result VARCHAR(100) NULL,
    weight_division VARCHAR(100) NULL,
    notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_tournament_participations_tournament_id (tournament_id),
    KEY ix_tournament_participations_student_id (student_id),
    CONSTRAINT fk_tournament_participations_tournament_id_tournaments
        FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_tournament_participations_student_id_students
        FOREIGN KEY (student_id) REFERENCES students (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE notifications (
    id INT NOT NULL AUTO_INCREMENT,
    student_id INT NULL,
    type ENUM('payment_due', 'payment_overdue', 'general') NOT NULL,
    channel ENUM('push', 'email') NOT NULL,
    title VARCHAR(150) NOT NULL,
    body TEXT NOT NULL,
    status ENUM('queued', 'sent', 'failed') NOT NULL,
    sent_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
    PRIMARY KEY (id),
    KEY ix_notifications_student_id (student_id),
    KEY ix_notifications_status (status),
    CONSTRAINT fk_notifications_student_id_students
        FOREIGN KEY (student_id) REFERENCES students (id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
