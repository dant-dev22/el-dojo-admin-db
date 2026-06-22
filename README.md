# ElDojo Data Layer

Capa de base de datos de la Fase 1 para una plataforma multi-tenant de dojos de BJJ, pensada para extenderse a otras artes marciales.

## Stack

- MySQL 8
- SQLAlchemy 2.x
- Alembic
- PyMySQL
- Python 3.11+

## Estructura

```text
app/
  core/
  db/
  models/
alembic/
  versions/
scripts/
schema.sql
```

## Reglas modeladas

- Jerarquía multi-tenant: `organizations -> branches`
- Los alumnos y clases pertenecen a una sucursal
- `created_at` y `updated_at` se manejan en UTC
- La edad no se almacena; se calcula desde `birth_date`
- El último peso se obtiene del registro más reciente en `weight_logs`
- El borrado de alumnos es lógico mediante `deleted_at`
- `unique_code` del alumno queda como columna única; la generación del formato vive en backend
- Las llaves foráneas usan `ON DELETE RESTRICT` para proteger historial

## Suposiciones documentadas

- `notifications` y `device_tokens` siguen exactamente el contrato pedido; el contexto tenant se deriva desde `student_id` o `user_id`
- El hash del usuario admin en el seed es de ejemplo con SHA-256 para mantener la capa de datos autocontenida; en producción debe reemplazarse por Argon2 o BCrypt en el backend
- `currency` usa `USD` como valor por defecto razonable, pero puede cambiarse por organización o flujo de negocio

## 1. Crear base de datos y usuario en MySQL

Ejecuta estas sentencias con un usuario con permisos administrativos:

```sql
CREATE DATABASE eldojo_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'eldojo_app'@'localhost' IDENTIFIED BY 'eldojo_app_password';
CREATE USER 'eldojo_app'@'127.0.0.1' IDENTIFIED BY 'eldojo_app_password';

GRANT ALL PRIVILEGES ON eldojo_db.* TO 'eldojo_app'@'localhost';
GRANT ALL PRIVILEGES ON eldojo_db.* TO 'eldojo_app'@'127.0.0.1';

FLUSH PRIVILEGES;
```

## 2. Crear entorno virtual e instalar dependencias

En Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e .
```

## 3. Configurar variables de entorno

Copia el ejemplo:

```powershell
Copy-Item .env.example .env
```

Contenido esperado de `.env`:

```env
DATABASE_URL=mysql+pymysql://eldojo_app:eldojo_app_password@127.0.0.1:3306/eldojo_db
```

## 4. Ejecutar migraciones

```powershell
python -m alembic upgrade head
```

Si tu entorno expone el ejecutable directamente, también funciona:

```powershell
alembic upgrade head
```

Si quieres inspeccionar el DDL antes de aplicarlo, revisa `schema.sql`.

## 5. Cargar datos semilla

```powershell
python -m scripts.seed
```

Seed incluido:

- Organización: `El Dojo`
- Slug: `ELD`
- Sucursal: `Matriz`
- Timezone: `America/Mexico_City`
- Disciplina: `BJJ`
- Rangos: `Blanca`, `Azul`, `Morada`, `Marron`, `Negra`
- Usuario admin: `dantedev22@gmail.com`
- Password de ejemplo: `d4nt3r4d`

## Modelos incluidos

- `organizations`
- `branches`
- `users`
- `admin_assignments`
- `disciplines`
- `ranks`
- `students`
- `weight_logs`
- `student_ranks`
- `classes`
- `class_schedules`
- `class_enrollments`
- `attendance`
- `payments`
- `tournaments`
- `tournament_participations`
- `device_tokens`
- `notifications`

## Archivos clave

- Modelos ORM: `app/models/`
- Configuración de conexión: `app/core/config.py`
- Sesión SQLAlchemy: `app/db/session.py`
- Configuración Alembic: `alembic/env.py`
- Migración inicial: `alembic/versions/20260620_0001_initial_schema.py`
- Seed: `scripts/seed.py`
- DDL legible: `schema.sql`
