# Plan de implementación del backend SEMA

> Punto de entrada y protocolo: [CONTEXT.md](CONTEXT.md). Referencia técnica: [ARCHITECTURE.md](ARCHITECTURE.md).

## Resumen de avance

| Fase | Estado |
|---|---|
| 1. Fundación | ✅ Completada (código importado del proyecto de entrenamiento y adaptado) |
| 2. Core de datos y seeders | ✅ Completada (incluye `get_by`, WAL y `DbConnection`) |
| 3. Feature `usuarios` | ✅ Completada |
| 4. Autenticación JWT | ⏭️ Pendiente. **La implementa un compañero** |
| 5. Entidades de datos e históricos | Pendiente (entidades por definir) |
| 6. Plantilla y documentación | ✅ `_template/` y README listos (falta adaptar Postman) |

Alcance de esta etapa: **eventos CRUD completos por entidad**, sobre SQLite. Sin creación por lotes ni sincronización especial.

## 1. Objetivo

Construir el backend de SEMA: una API REST (FastAPI + SQLite) que **persiste datos e históricos** y **controla usuarios**. El análisis y las consultas a APIs externas viven en el frontend (offline).

**Fuera de alcance:** analítica, recomendaciones de cultivos, clientes de APIs externas, caché de APIs, `pandas`.

## 2. Decisiones

Heredadas del proyecto de origen. Ver la tabla completa en [CONTEXT.md](CONTEXT.md), sección 6. Las que condicionan este plan:

- SQLite con `sqlite3`, sin ORM; migraciones SQL numeradas; borrado lógico (`deleted_at`).
- JWT con `get_current_user`, registro protegido, primer usuario desde variables de entorno.
- Listados paginados (`PageSchema[T]`), fechas en UTC, `extra="forbid"` en los schemas de entrada.
- CORS obligatorio (frontend React/PWA en otro origen).
- **Ids:** `INTEGER PRIMARY KEY AUTOINCREMENT` en todas las tablas (entero de 64 bits y positivo; el equivalente práctico a *unsigned big integer* en SQLite).
- **Alcance de datos:** varias entidades, cada una con su caso de uso y **CRUD completo**. Sin creación por lotes.
- **SQLite** "para efectos prácticos": la arquitectura de repositorios permitiría cambiar de motor tocando solo `core/database.py` y los repositorios.
- **JWT:** lo implementa un compañero (fase 4).

## 3. Dependencias

La fuente de verdad es `backend/requirements.txt`, con versiones fijas (verificadas el 2026-11-14 con Python 3.13: `ruff` y `pytest` en verde).

| Paquete | Para qué |
|---|---|
| `fastapi`, `uvicorn[standard]` | API y servidor |
| `pydantic`, `pydantic-settings`, `email-validator` | Schemas, configuración desde `.env`, validación de emails |
| `tzdata` | Zonas horarias (Windows no las trae) |
| `python-multipart` | Formulario de login OAuth2 (fase 4) |
| `PyJWT` (fase 4), `pwdlib[argon2]` | JWT y hash de contraseñas |
| `pytest`, `httpx2`, `ruff` | Pruebas (`httpx2` lo usa el `TestClient` de Starlette 1.x) y linter con reglas `S` |

Quedan fuera `requests`, `responses` y `pandas`.

## 4. Flujo de cada fase

1. Se presenta el plan de la fase y se espera la aprobación.
2. Se implementa en la rama de trabajo asignada.
3. Se verifica (`ruff` + `pytest` + prueba manual) y se actualiza la documentación.
4. Brayan revisa y decide el commit, el push y la integración.

No se avanza sin cumplir el criterio de "listo" de la fase actual.

## 5. Fases

### Fase 1: Fundación ✅
- [x] Estructura de `backend/` con los `__init__.py`
- [x] `requirements.txt` podado (sin `requests`, `responses` ni `pandas`), `.gitignore`, `.env.example`
- [x] `core/config.py` (pydantic-settings; `TIMEZONE` validada al arrancar)
- [x] `core/database.py`: conexión por petición, migraciones con `schema_migrations`, `utc_now_iso()`, `local_now()`, `to_local()`
- [x] `core/exceptions.py`, `core/error_handlers.py` (formato uniforme, 500 con `error_id` y CORS) y `core/log_config.py`
- [x] `main.py`: app, CORS desde `CORS_ORIGINS`, handlers, `GET /health`
- [x] `pyproject.toml` con `ruff` (reglas `S`) y `pytest`
- [x] Ajuste propio: SQLite con `journal_mode=WAL` y `busy_timeout=5000`
- [x] Ajuste propio: alias `DbConnection` (`scope="function"`): el commit ocurre **antes** de responder

**Listo cuando:** el servidor arranca, `/docs` muestra Swagger, el preflight de CORS desde `http://localhost:5173` funciona, un 500 conserva los headers de CORS y `ruff check .` pasa. *(Verificado con tests y con el servidor real. Falta probar con el proyecto React real.)*

### Fase 2: Core de datos y seeders ✅
- [x] `core/base_schema.py`: `AuditSchema`, `PageSchema[T]`, `SortDirection`
- [x] `core/base_repository.py`: `get_by_id`, **`get_by`**, `list_all`, `count`, `create`, `update`, `soft_delete`, `exists_by`, con lista blanca de columnas y de `order_by`
- [x] `manage.py`: `migrate`, `migrate:status`, `db:seed`, `migrate:fresh [--seed]` (los dos últimos bloqueados en producción)
- [x] `core/base_seeder.py` y `app/seeders/`
- [x] Tests: CRUD, timestamps, soft delete, inyección SQL (también en `get_by` y en los filtros)
- [x] Filtros de listado: `filters` (igualdad, `NULL`, `IN`), `ranges` (inclusivo, fechas a UTC) y `search` (parcial, con escape de `%` y `_`); `count` con los mismos filtros

**Listo cuando:** los tests pasan y no hay SQL armado con datos externos fuera de `BaseRepository`. *(Cumplido.)*

### Fase 3: Feature `usuarios` ✅
- [x] Migración `001_create_usuarios.sql` con índice único parcial en `email` (solo activos)
- [x] `schemas.py`: `UsuarioCreate`, `UsuarioUpdate` (rechaza `null`), `UsuarioOut` (sin `password_hash`); email normalizado a minúsculas
- [x] `repository.py`, `service.py` (hash, duplicados → 409, no encontrado → 404) y `router.py` con los 5 endpoints
- [x] Listado con filtros `q` (nombre y email), `created_from` y `created_to`
- [x] `UsuarioSeeder` (4 usuarios `@sema.example` + 1 eliminado, idempotente)
- [x] Tests del service y de los endpoints (incluye caracteres especiales guardados en la BD)

**Listo cuando:** los 5 endpoints funcionan con los códigos HTTP correctos, se puede reutilizar el email de un usuario eliminado y `password_hash` no aparece en ninguna respuesta. *(Cumplido.)*

### Fase 4: Autenticación JWT ⏭️ Pendiente
**Responsable:** un compañero del equipo backend. La carpeta `app/features/auth/` ya existe (vacía). El hash de contraseñas ya está en `core/security.py`. Diseño en [ARCHITECTURE.md](ARCHITECTURE.md), sección 7.

- [ ] `core/security.py`: `create_access_token`, `decode_access_token`
- [ ] `features/auth/`: `get_current_user` (valida el token **y** que el usuario exista y no esté eliminado), `POST /auth/login` (formulario OAuth2), `GET /auth/me`
- [ ] Proteger todo `/usuarios` y actualizar sus tests con un fixture que entregue los headers `Authorization`
- [ ] Bootstrap del primer usuario desde `FIRST_USER_EMAIL` / `FIRST_USER_PASSWORD`
- [ ] Validación de arranque: no inicia con el `JWT_SECRET` de ejemplo (o menor de 32 caracteres) si `ENVIRONMENT=production`
- [ ] Tests: sin token, token inválido o expirado y token de usuario eliminado → 401; login incorrecto → 401 con mensaje genérico

**Listo cuando:** el botón **Authorize** de Swagger funciona y los tests pasan.

### Fase 5: Entidades de datos e históricos
**Bloqueada hasta definir las entidades** (ver [CONTEXT.md](CONTEXT.md), sección 9). Alcance acordado: **cada entidad tiene sus eventos CRUD completos**, con el mismo molde de `usuarios`. Sin creación por lotes ni sincronización especial.

- [ ] Definir cada entidad: campos, relaciones con `usuarios` y caso de uso
- [ ] Por entidad: migración, `schemas.py`, `repository.py`, `service.py`, `router.py`, seeder (opcional) y tests
- [x] Filtros de listado en el core (hecho): `filters`, `ranges` y `search` en `list_all` y `count`, y los parámetros `q`, `created_from`, `created_to` con `list_filters`. Por entidad solo falta declarar `searchable` y, si hace falta, un filtro propio con `Query`
- [ ] Registrar los routers en `main.py` y protegerlos con `get_current_user` (cuando exista)

**Listo cuando:** cada entidad pasa su checklist de PR y el contrato JSON está acordado con el frontend.

### Fase 6: Plantilla y documentación
- [x] `backend/README.md` con instalación, ejecución, comandos y formato de errores
- [x] `features/_template/`: molde con CRUD completo (entidad de ejemplo `Ejemplo`), instrucciones en su `README.md` y probado en `tests/features/test_template.py`
- [ ] Verificar que `.ai/` refleja el estado real después de cada fase
- [ ] Adaptar la colección de Postman (viene del proyecto de entrenamiento; se hará después)

**Listo cuando:** una feature nueva puede crearse siguiendo `ARCHITECTURE.md`, sección 9, con cambios mínimos en la revisión.

## 5.1 Estructura heredada del proyecto de entrenamiento

El código de las fases 1 a 3 viene del repositorio `SEMA-ENTRENAMIENTO-BACKEND` (carpeta `backend/`). Se adaptó así: se quitaron `nasa_api_key`, `requests`, `responses` y las excepciones de servicios externos; se renombraron los usuarios de ejemplo; y se agregaron `get_by`, WAL y `DbConnection`. El resto se mantuvo tal cual.

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
| Duplicados o conflictos si el frontend reenvía datos offline | Fuera de alcance por ahora (solo CRUD). Reabrir si el frontend lo necesita |
| Lectura inmediata tras escribir (commit después de responder) | Resuelto con `DbConnection` y un test |
| CORS falla en el evento | Probar con el React real desde la fase 1; `CORS_ORIGINS` por `.env` |
| Wifi inestable en el evento | El frontend funciona offline; el backend corre en una red local |
| Fuga de secretos | `.env` en `.gitignore`; validación de `JWT_SECRET` al arrancar |
| Sobreingeniería | Solo se crean los archivos que la feature necesita |
