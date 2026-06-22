"""Carga datos semilla mínimos para la Fase 1."""

from __future__ import annotations

import hashlib
from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.curriculum import Discipline, Rank
from app.models.organization import Branch, Organization
from app.models.user import AdminAssignment, User
from app.models.enums import UserRole


ADMIN_EMAIL = "dantedev22@gmail.com"
ADMIN_PASSWORD = "d4nt3r4d"
ORG_SLUG = "ELD"


def build_demo_password_hash(raw_password: str) -> str:
    """Genera un hash simple de ejemplo para la semilla.

    Nota: el backend real debería reemplazarlo por Argon2 o BCrypt.
    """

    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def run_seed() -> None:
    """Inserta organización, sucursal, disciplina, rangos y usuario admin."""

    with SessionLocal() as session:
        organization = session.scalar(
            select(Organization).where(Organization.slug == ORG_SLUG)
        )
        if organization is None:
            organization = Organization(
                name="El Dojo",
                slug=ORG_SLUG,
                is_active=True,
            )
            session.add(organization)
            session.flush()

        branch = session.scalar(
            select(Branch).where(
                Branch.organization_id == organization.id,
                Branch.name == "Matriz",
            )
        )
        if branch is None:
            branch = Branch(
                organization_id=organization.id,
                name="Matriz",
                country="Mexico",
                state="CDMX",
                city="Ciudad de Mexico",
                address="Av. Principal 123",
                timezone="America/Mexico_City",
                qr_secret="seed-secret-matriz",
                is_active=True,
            )
            session.add(branch)
            session.flush()

        discipline = session.scalar(
            select(Discipline).where(
                Discipline.organization_id == organization.id,
                Discipline.name == "BJJ",
            )
        )
        if discipline is None:
            discipline = Discipline(
                organization_id=organization.id,
                name="BJJ",
                is_active=True,
            )
            session.add(discipline)
            session.flush()

        existing_rank_names = {
            rank_name
            for rank_name in session.scalars(
                select(Rank.name).where(Rank.discipline_id == discipline.id)
            )
        }
        for order_index, rank_name in enumerate(
            ["Blanca", "Azul", "Morada", "Marron", "Negra"],
            start=1,
        ):
            if rank_name not in existing_rank_names:
                session.add(
                    Rank(
                        discipline_id=discipline.id,
                        name=rank_name,
                        order_index=order_index,
                        max_degrees=4,
                    )
                )

        user = session.scalar(select(User).where(User.email == ADMIN_EMAIL))
        if user is None:
            user = User(
                email=ADMIN_EMAIL,
                password_hash=build_demo_password_hash(ADMIN_PASSWORD),
                role=UserRole.ORG_ADMIN,
                is_active=True,
            )
            session.add(user)
            session.flush()

        assignment = session.scalar(
            select(AdminAssignment).where(
                AdminAssignment.user_id == user.id,
                AdminAssignment.organization_id == organization.id,
                AdminAssignment.branch_id.is_(None),
            )
        )
        if assignment is None:
            session.add(
                AdminAssignment(
                    user_id=user.id,
                    organization_id=organization.id,
                    branch_id=None,
                )
            )

        session.commit()

        print("Seed completado correctamente.")
        print(f"Organización: {organization.name} ({organization.slug})")
        print(f"Sucursal: {branch.name} [{branch.timezone}]")
        print(f"Disciplina: {discipline.name}")
        print(f"Admin: {ADMIN_EMAIL}")
        print("Password de ejemplo: d4nt3r4d")
        print(f"Fecha de referencia seed: {date.today().isoformat()}")


if __name__ == "__main__":
    run_seed()
