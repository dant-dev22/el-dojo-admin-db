# Directrices para IA - ElDojo Data Layer

## Objetivo del proyecto

Este repositorio es la fuente de verdad del esquema de base de datos para ElDojo, una plataforma multi-tenant de dojos de artes marciales con foco inicial en BJJ.

La responsabilidad principal del proyecto es:

- definir modelos ORM con SQLAlchemy 2.x;
- versionar cambios estructurales con Alembic;
- mantener consistencia del esquema MySQL 8;
- proveer datos semilla minimos para desarrollo.

La IA debe tratar este repositorio como una capa de datos, no como un backend HTTP ni como una app frontend.

## Stack tecnico

- Python 3.11+
- MySQL 8
- SQLAlchemy 2.x
- Alembic
- PyMySQL
- python-dotenv

## Estructura importante

- `app/core/config.py`: carga `DATABASE_URL` desde `.env`
- `app/db/base.py`: `Base` declarativa y convencion de nombres de constraints
- `app/db/session.py`: engine y `SessionLocal`
- `app/models/`: definicion de entidades ORM
- `alembic/env.py`: configuracion de migraciones
- `alembic/versions/`: historial de migraciones
- `scripts/seed.py`: seed base para desarrollo
- `schema.sql`: referencia legible del DDL
- `README.md`: reglas de negocio, setup y flujo operativo

## Reglas de oro para una IA

1. Considera este repo como la fuente de verdad del esquema.
2. Nunca propongas `create_all()` como mecanismo principal de despliegue.
3. Todo cambio estructural debe reflejarse en modelos y en una migracion Alembic.
4. Migra primero la base de datos y despues despliega el backend que depende del cambio.
5. Conserva la compatibilidad con MySQL 8 y con SQLAlchemy 2.x.
6. Respeta las reglas multi-tenant ya modeladas en organizaciones y sucursales.

## Convenciones tecnicas

### Modelado

- Usa tipado moderno de SQLAlchemy con `Mapped[...]` y `mapped_column(...)`.
- Hereda de `Base` definida en `app/db/base.py`.
- Reutiliza mixins de `app/models/mixins.py` cuando aplique:
  - `CreatedAtMixin`
  - `TimestampMixin`
  - `currency_column()`
  - `monetary_column()`
- Manten nombres de tablas y relaciones coherentes con el dominio existente.

### Constraints e indices

- La metadata usa una convencion de nombres estable para `pk`, `fk`, `ix`, `uq`, `ck`.
- Prefiere declarar `Index(...)` y `CheckConstraint(...)` de forma explicita cuando una regla de negocio ya existe en el dominio.
- Las llaves foraneas usan `ondelete="RESTRICT"` para proteger historial; no cambies esto sin justificacion fuerte.

### Fechas y dinero

- `created_at` y `updated_at` se manejan en UTC.
- La implementacion actual usa `UTC_TIMESTAMP()` y datetimes naive alineados con MySQL `DATETIME`.
- Los montos monetarios deben mantenerse con `Numeric(10, 2)`.
- La moneda por defecto es `USD`, salvo que el requerimiento funcional cambie de manera explicita.

### Configuracion

- La conexion sale de `DATABASE_URL`.
- El valor por defecto esperado es MySQL con driver `mysql+pymysql`.
- No hardcodees credenciales nuevas en codigo fuera de ejemplos o `.env.example`.

## Reglas del dominio que la IA debe respetar

- La jerarquia tenant es `organizations -> branches`.
- Alumnos y clases pertenecen a una sucursal.
- La edad no se almacena; se calcula a partir de `birth_date`.
- El ultimo peso del alumno se deriva del registro mas reciente en `weight_logs`.
- El borrado de alumnos es logico mediante `deleted_at`.
- `students.unique_code` es unico; la generacion del formato pertenece al backend, no a esta capa.
- `notifications` y `device_tokens` derivan el contexto tenant desde `student_id` o `user_id`.
- La semilla actual incluye una organizacion demo, una sucursal, disciplina BJJ, rangos y un admin.

## Flujo correcto para cambios de esquema

Si una solicitud implica cambiar la base de datos, la IA debe seguir este orden:

1. Entender el cambio funcional y su impacto en datos.
2. Actualizar primero los modelos en `app/models/`.
3. Crear o ajustar la migracion en `alembic/versions/`.
4. Revisar que el cambio sea compatible con datos existentes y con `ON DELETE RESTRICT`.
5. Verificar si el seed tambien necesita actualizarse.
6. Sugerir aplicar migraciones con `python -m alembic upgrade head`.

Nunca dejes un cambio estructural solo en modelos o solo en SQL manual si debe quedar versionado en Alembic.

## Flujo correcto para seed

- El seed debe ser idempotente siempre que sea razonable.
- Antes de insertar, busca si el registro ya existe.
- Usa `SessionLocal()` y confirma cambios con `session.commit()`.
- Los hashes del seed pueden ser de ejemplo, pero cualquier nota de seguridad debe dejar claro que en produccion se usa Argon2 o BCrypt desde el backend.

## Que debe evitar una IA

- No convertir este repo en un backend web.
- No introducir frameworks ajenos al alcance del proyecto.
- No duplicar reglas ya modeladas en otro lugar sin necesidad.
- No cambiar nombres de tablas, enums o columnas existentes sin migracion explicita.
- No reemplazar borrado logico por borrado fisico en alumnos.
- No debilitar foreign keys ni restricciones historicas sin un requerimiento formal.
- No asumir PostgreSQL ni SQLite como destino principal.

## Comandos utiles

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item .env.example .env
python -m alembic upgrade head
python -m scripts.seed
```

## Criterio de respuesta esperado de una IA

Cuando una IA proponga cambios para este proyecto, idealmente debe:

- mencionar archivos afectados;
- distinguir entre cambio de modelo, migracion y seed;
- explicar impacto en integridad de datos;
- respetar la fuente de verdad del esquema;
- evitar soluciones que salten Alembic.

## Resumen operativo corto

Piensa en este repositorio como "DB schema first". Si cambias estructura, cambia modelos + migracion + validacion del seed cuando aplique. Si cambias logica de negocio dependiente del esquema, preserva multi-tenant, historial, UTC y restricciones existentes.
