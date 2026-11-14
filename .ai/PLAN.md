# Plan de implementación del backend SEMA

> Punto de entrada y protocolo: [CONTEXT.md](CONTEXT.md). Referencia técnica: [ARCHITECTURE.md](ARCHITECTURE.md).

## Resumen de avance

| Fase | Estado |
|---|---|
| 1. Fundación | Pendiente |
| 2. Core de datos y seeders | Pendiente |
| 3. Feature `usuarios` | Pendiente |
| 4. Autenticación JWT | Pendiente |
| 5. Persistencia de datos e históricos | Pendiente (entidades por definir) |
| 6. Plantilla y documentación | Pendiente |

## 1. Objetivo

Construir el backend de SEMA: una API REST (FastAPI + SQLite) que **persiste datos e históricos** y **controla usuarios**. El análisis y las consultas a APIs externas viven en el frontend (offline).

**Fuera de alcance:** analítica, recomendaciones de cultivos, clientes de APIs externas, caché de APIs, `pandas`.

## 2. Decisiones

Heredadas del proyecto de origen. Ver la tabla completa en [CONTEXT.md](CONTEXT.md), sección 6. Las que condicionan este plan:

- SQLite con `sqlite3`, sin ORM; migraciones SQL numeradas; borrado lógico (`deleted_at`).
- JWT con `get_current_user`, registro protegido, primer usuario desde variables de entorno.
- Listados paginados (`PageSchema[T]`), fechas en UTC, `extra="forbid"` en los schemas de entrada.
- CORS obligatorio (frontend React/PWA en otro origen).

## 3. Dependencias

La fuente de verdad será `backend/requirements.txt`, con versiones fijas verificadas al instalar.

| Paquete | Para qué |
|---|---|
| `fastapi`, `uvicorn[standard]` | API y servidor |
| `pydantic`, `pydantic-settings`, `email-validator` | Schemas, configuración desde `.env`, validación de emails |
| `tzdata` | Zonas horarias (Windows no las trae) |
| `python-multipart` | Formulario de login OAuth2 |
| `PyJWT`, `pwdlib[argon2]` | JWT y hash de contraseñas |
| `pytest`, `httpx2` (verificar), `ruff` | Pruebas y linter con reglas `S` |

Quedan fuera `requests`, `responses` y `pandas`.

## 4. Flujo de cada fase

1. Se presenta el plan de la fase y se espera la aprobación.
2. Se implementa en la rama de trabajo asignada.
3. Se verifica (`ruff` + `pytest` + prueba manual) y se actualiza la documentación.
4. Brayan revisa y decide el commit, el push y la integración.

No se avanza sin cumplir el criterio de "listo" de la fase actual.

## 5. Fases

### Fase 1: Fundación
- [ ] Crear `backend/` con estructura de carpetas y `__init__.py`
- [ ] `requirements.txt` con versiones fijas, `.gitignore` (`.env`, `data/*.db`, `__pycache__`, `.venv/`)
- [ ] `.env.example` con todas las variables documentadas
- [ ] `core/config.py` (pydantic-settings; `TIMEZONE` validada al arrancar)
- [ ] `core/database.py`: conexión por petición, migraciones con tabla `schema_migrations`, `utc_now_iso()`, `local_now()`, `to_local()`
- [ ] `core/exceptions.py`, `core/error_handlers.py` (formato uniforme, 500 con `error_id` y CORS) y `core/log_config.py`
- [ ] `main.py`: app, CORS desde `CORS_ORIGINS`, handlers, `GET /health`
- [ ] `pyproject.toml` con `ruff` (reglas `S`) y `pytest`

**Listo cuando:** el servidor arranca, `/docs` muestra Swagger, el preflight de CORS desde `http://localhost:5173` funciona, un 500 conserva los headers de CORS y `ruff check .` pasa.

### Fase 2: Core de datos y seeders
- [ ] `core/base_schema.py`: `AuditSchema`, `PageSchema[T]`, `SortDirection`
- [ ] `core/base_repository.py`: `get_by_id`, `list_all`, `count`, `create`, `update`, `soft_delete`, `exists_by`, con lista blanca de columnas y de `order_by`
- [ ] `manage.py`: `migrate`, `migrate:status`, `db:seed`, `migrate:fresh [--seed]` (los dos últimos bloqueados en producción)
- [ ] `core/base_seeder.py` y `app/seeders/`
- [ ] Tests: CRUD, timestamps, soft delete, inyección SQL (sección 6)

**Listo cuando:** los tests pasan y no hay SQL armado con datos externos fuera de `BaseRepository`.

### Fase 3: Feature `usuarios`
- [ ] Migración `001_create_usuarios.sql` con índice único parcial en `email` (solo activos)
- [ ] `schemas.py`: `UsuarioCreate`, `UsuarioUpdate` (rechaza `null`), `UsuarioOut` (sin `password_hash`); email normalizado a minúsculas
- [ ] `repository.py`, `service.py` (hash, duplicados → 409, no encontrado → 404) y `router.py` con los 5 endpoints
- [ ] `UsuarioSeeder` (usuarios de ejemplo `@sema.example`, idempotente)
- [ ] Tests del service y de los endpoints (incluye caracteres especiales guardados en la BD)

**Listo cuando:** los 5 endpoints funcionan con los códigos HTTP correctos, se puede reutilizar el email de un usuario eliminado y `password_hash` no aparece en ninguna respuesta.

### Fase 4: Autenticación JWT
- [ ] `core/security.py`: `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`
- [ ] `features/auth/`: `get_current_user` (valida el token **y** que el usuario exista y no esté eliminado), `POST /auth/login` (formulario OAuth2), `GET /auth/me`
- [ ] Proteger todo `/usuarios`
- [ ] Bootstrap del primer usuario desde `FIRST_USER_EMAIL` / `FIRST_USER_PASSWORD`
- [ ] Validación de arranque: no inicia con el `JWT_SECRET` de ejemplo (o menor de 32 caracteres) si `ENVIRONMENT=production`
- [ ] Tests: sin token, token inválido o expirado y token de usuario eliminado → 401; login incorrecto → 401 con mensaje genérico

**Listo cuando:** el botón **Authorize** de Swagger funciona y los tests pasan.

### Fase 5: Persistencia de datos e históricos
**Bloqueada hasta definir las entidades** (ver [CONTEXT.md](CONTEXT.md), sección 9). Esbozo de lo que habrá que decidir y construir:

- [ ] Definir entidades, campos y relaciones con `usuarios` (¿el histórico es por usuario?)
- [ ] Migraciones, schemas, repository, service y router de cada entidad, siguiendo el molde de `usuarios`
- [ ] Soporte para datos que se generaron offline y llegan después:
  - identificador generado en el cliente (UUID o `client_id`) y creación idempotente
  - fecha original del registro (del cliente) separada de `created_at` (de recepción)
  - subida por lotes y respuesta con el resultado de cada elemento
  - regla de conflictos (por ejemplo, gana el `updated_at` más reciente)
- [ ] Consulta de históricos con filtros (rango de fechas) y paginación
- [ ] Tests y colección de Postman de cada endpoint

**Listo cuando:** se define con el equipo de frontend y se documenta el contrato de la sincronización.

### Fase 6: Plantilla y documentación
- [ ] `features/_template/` con los archivos base comentados
- [ ] `backend/README.md` con instalación, ejecución, comandos y formato de errores
- [ ] Verificar que `.ai/` refleja el estado real

**Listo cuando:** una feature nueva puede crearse siguiendo la guía de `ARCHITECTURE.md`, sección 9, con cambios mínimos en la revisión.

## 6. Seguridad SQL: reglas obligatorias

1. **Valores siempre con `?`.** Nunca f-strings, `%`, `.format()` ni `+` con datos externos.
2. **Lista blanca de identificadores:** cada repositorio declara `table` y `columns`.
3. **`order_by` en lista blanca** y dirección solo `ASC` o `DESC`.
4. **Paginación acotada:** `limit` entre 1 y 100, `offset >= 0`.
5. **Pydantic primero:** ningún dato llega al repositorio sin un schema tipado.
6. **Linter:** `ruff` con reglas `S`. Solo `core/base_repository.py` puede usar `# noqa: S608`.
7. **Tests de inyección:** `1 OR 1=1`, `x'; DROP TABLE usuarios;--` y columnas falsas en `order_by` fallan de forma controlada sin alterar la BD.

## 7. Criterios de revisión de PR

- [ ] El router no tiene lógica de negocio
- [ ] El service no conoce HTTP
- [ ] No hay SQL fuera de un repositorio ni armado con datos externos
- [ ] Schemas de entrada y salida separados, sin datos sensibles en la salida
- [ ] Rutas protegidas con `get_current_user` salvo que sean públicas a propósito
- [ ] Tests nuevos para el código nuevo
- [ ] `ruff check .` y `pytest` en verde

## 8. Riesgos

| Riesgo | Mitigación |
|---|---|
| Entidades del histórico sin definir | Cerrar la definición con el frontend antes de la fase 5 |
| Sincronización offline mal diseñada (duplicados, conflictos) | IDs del cliente + creación idempotente + regla de conflictos documentada |
| CORS falla en el evento | Probar con el React real desde la fase 1; `CORS_ORIGINS` por `.env` |
| Wifi inestable en el evento | El frontend funciona offline; el backend admite sincronización diferida |
| Fuga de secretos | `.env` en `.gitignore`; validación de `JWT_SECRET` al arrancar |
| Sobreingeniería | Solo se crean los archivos que la feature necesita |
