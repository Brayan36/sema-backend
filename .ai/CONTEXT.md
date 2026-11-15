# Contexto para retomar sesiones

> **Punto de entrada.** Leerlo completo antes de hacer cualquier cosa.
> Al cerrar cada sesión, actualizar las secciones 8 (Estado actual) y 10 (Bitácora).

---

## 1. Qué es este proyecto

- **SEMA (Sistema Espacial de Monitoreo Agrícola):** proyecto del equipo que participa en el evento de NASA en Medellín (fecha aproximada: finales de noviembre de 2026).
- **Este repositorio (`sema-backend`)** es el backend real de SEMA. Es una API REST (FastAPI + SQLite).
- Los documentos de origen hablaban de un backend "de entrenamiento". Ya no es así: es el proyecto real, y de esos documentos solo se aprovechó la arquitectura.

## 2. Alcance (cambio de rumbo de último momento)

**El backend hace:**
- **Persistencia de datos e históricos** de la aplicación. *(Entidades exactas por definir.)*
- **Control de usuarios:** registro protegido, login y protección de rutas con JWT.

**El backend NO hace:**
- Análisis de información ni recomendaciones de cultivos.
- Consultas a APIs externas (NASA POWER u otras).

Ese procesamiento ocurre **en el frontend**, por el uso de `localStorage` y el funcionamiento **offline**. El backend recibe, guarda y entrega los resultados y el histórico.

**Datos:** habrá **varias entidades**, cada una con su caso de uso y **sus eventos CRUD completos** (crear, listar, obtener, actualizar y borrado lógico), con el mismo molde de la feature `usuarios`. Por ahora **no** hay creación por lotes ni lógica de sincronización: el alcance es CRUD sobre SQLite. Si el frontend offline lo necesita más adelante (ids generados en el cliente, conflictos), se reabre como una fase nueva.

## 3. Equipo

- **Backend:** Brayan (autor de las decisiones) y Sebastián.
- **Frontend:** el resto del equipo, en otra app (React, preparada como PWA, con procesamiento offline). Como es otra app, **CORS es obligatorio**.
- Se prefiere la claridad sobre la sofisticación. Si algo se puede hacer más simple sin perder seguridad, se hace más simple.

## 4. Cómo retomar

1. Leer `.ai/README.md`, este archivo, `PLAN.md` y `ARCHITECTURE.md`, y después `backend/README.md`.
2. Revisar el código en `backend/app/core/`. **El código es la fuente de verdad.**
3. Verificar el entorno desde `backend/` (en Windows `py`, en Linux/macOS `python3`):
   ```
   git status; git branch --show-current
   python3 -m pip install -r requirements.txt
   python3 -m ruff check .        # "All checks passed!"
   python3 -m pytest -q           # 228 en verde
   python3 manage.py migrate:status
   ```
4. Confirmar con Brayan cuál es el siguiente paso antes de tocar archivos.

## 5. Protocolo de trabajo

1. **Primero un plan, después los cambios.** Se presenta lo que se va a hacer, se espera la aprobación y se ejecuta solo lo aprobado.
2. **Se trabaja fase por fase**, según `PLAN.md`. Lo que aparezca fuera del plan se propone como ajuste y se documenta.
3. **Ramas:** el agente trabaja en la rama que le asigna la sesión. Nunca hace push a otras ramas.
4. **Commits y push:** solo cuando Brayan lo pide. **No se crean PR** sin pedirlo.
5. **Cada entrega se verifica antes de reportarla:** `ruff format`, `ruff check`, `pytest` y una prueba manual cuando aplique (servidor real, `curl` o Swagger).
6. **Cada entrega actualiza la documentación** (tabla de abajo).
7. **Idioma:** documentación, mensajes de la API y comentarios en español. Código del core y nombres de archivo en inglés. Ver convenciones en `ARCHITECTURE.md`, sección 8.
8. **Reportar con honestidad:** qué se hizo, qué se verificó, qué quedó pendiente y qué no se pudo probar.

| Si cambió… | Actualizar |
|---|---|
| El avance de una fase | Checkboxes de `PLAN.md` + secciones 8 y 10 de este archivo |
| El diseño, una regla o una pieza del core | `ARCHITECTURE.md` |
| Cómo instalar, ejecutar o usar algo | `backend/README.md` |
| Un endpoint | La colección de Postman, si existe |
| Una decisión | Sección 6 de este archivo + sección 2 de `PLAN.md` |
| Algo que causó un error o confusión | Sección 7 (trampas conocidas) |

## 6. Decisiones clave (heredadas, vigentes salvo que se indique)

| Tema | Decisión |
|---|---|
| Stack | Python 3.12+, FastAPI, Pydantic v2, SQLite con `sqlite3` (sin ORM) |
| Arquitectura | Híbrida: features por fuera, capas por dentro (router → service → repository), sobre un **core** compartido |
| Borrado | Lógico, con `deleted_at` |
| Auth | JWT HS256, solo access token, `JWT_EXPIRE_MINUTES=60`, dependencia `get_current_user` (no middleware). Todo protegido salvo `/health`, `/auth/login` y `/docs` |
| Registro de usuarios | Solo un usuario autenticado crea otros. El primer usuario sale de variables de entorno |
| Services | Explícitos, sin `BaseService` genérico |
| Seguridad SQL | Parámetros `?`, lista blanca de identificadores, `ruff` con reglas `S`, tests de inyección |
| Errores 500 | Mensaje genérico + `error_id`, traza en el log, rollback y headers de CORS conservados |
| Fechas | Se guardan y entregan en UTC, ISO 8601. `TIMEZONE=America/Bogota` solo para lógica que dependa de la hora local |
| Listados | Paginados con `PageSchema[T]` |
| Validación de entrada | `extra="forbid"`; `null` explícito en un PATCH → 422 |
| Entorno de Python | Sin `venv` por defecto; `venv` queda como opción documentada en `backend/README.md` |
| **Nuevo:** sin analítica ni APIs externas | Decisión de Brayan: lo hace el frontend (offline / `localStorage`) |
| **Nuevo:** ids | `INTEGER PRIMARY KEY AUTOINCREMENT` (64 bits, positivo): el *unsigned big integer* práctico de SQLite. Ver la nota en `backend/README.md` |
| **Nuevo:** alcance de datos | Varias entidades, CRUD completo por entidad, sin creación por lotes |
| **Nuevo:** `BaseRepository.get_by(column, value)` | Aprobado por Brayan. Lista blanca de columnas, ignora eliminados salvo `include_deleted=True` |
| **Nuevo:** SQLite con WAL y `busy_timeout=5000` | Evita `database is locked` con peticiones concurrentes |
| **Nuevo:** conexión con `DbConnection` | El commit ocurre antes de responder (ver trampa 12) |
| **Nuevo:** JWT | Lo implementa un compañero. La estructura queda lista (`features/auth/`) |
| **Nuevo:** Postman | Se adapta después |
| **Nuevo:** roles por usuario | Para el MVP, cada usuario tiene un único rol. Se conserva `usuario_roles` y `usuario_id` es su clave primaria. |
| **Nuevo:** estado de cuenta | `is_active` es independiente de `deleted_at`: desactiva una cuenta sin eliminarla lógicamente. |

## 7. Trampas conocidas

| # | Problema | Solución |
|---|---|---|
| 1 | En Windows, `python` abre la Microsoft Store | Usar `py` |
| 2 | `TestClient` de Starlette 1.x avisa que `httpx` está obsoleto | La dependencia de pruebas es `httpx2` (verificada) |
| 3 | Un método llamado `list` tapa el `list` de Python | Llamarlo `list_all` |
| 4 | Starlette responde los 500 fuera de CORS (falso error de CORS) | Middleware `catch_unexpected_errors`; `register_error_handlers(app)` va **antes** de `add_middleware(CORSMiddleware)` |
| 5 | `re.match` con `$` acepta un salto de línea final | Usar `fullmatch` |
| 6 | `executescript` no acepta parámetros ni abre transacción | Anteponer `BEGIN;` y registrar la migración antes del `commit` |
| 7 | FastAPI puede usar la conexión SQLite en otro hilo de la misma petición | `check_same_thread=False` (conexión por petición) |
| 8 | `EmailStr` rechaza `.local`, `.test`, `localhost` | Datos de ejemplo con `@sema.example` |
| 9 | Un PATCH con `null` termina en 500 por columna `NOT NULL` | `model_validator` que rechaza `null` + `model_dump(exclude_unset=True)` |
| 10 | Windows no trae base de zonas horarias | Dependencia `tzdata`; validar `TIMEZONE` al arrancar |
| 11 | `migrate:fresh` no borra la BD si está abierta (Windows) | Cerrar visor SQL y servidor antes |
| 12 | Con FastAPI 0.162, el código posterior al `yield` de una dependencia corre **después** de enviar la respuesta: el `commit` de `get_db` llegaba tarde y un `GET` inmediato podía no ver el dato recién guardado | Pedir la conexión con `DbConnection` (`Depends(get_db, scope="function")`), nunca con `Depends(get_db)` a secas. Un test lo verifica y falla si se quita el `scope` |
| 13 | SQLite sin WAL ni `busy_timeout` puede fallar con `database is locked` si dos peticiones escriben a la vez | `connect()` activa `journal_mode=WAL` y `busy_timeout=5000`. Un test lo verifica |
| 14 | `id BIGINT UNSIGNED PRIMARY KEY` no crea el id automático en SQLite (solo `INTEGER PRIMARY KEY` lo hace) | Usar `INTEGER PRIMARY KEY AUTOINCREMENT`: ya es de 64 bits y positivo |

## 8. Estado actual

**Fecha de corte:** 2026-11-14 · **Rama de trabajo:** `feature/estructura-inicial-contexto-ia` · **Tests:** 228 en verde · **ruff:** sin errores

El código de las fases 1 a 3 se importó del proyecto de entrenamiento (`SEMA-ENTRENAMIENTO-BACKEND`) y se adaptó. Cambios principales: sin `nasa_api_key`, `requests` ni excepciones de servicios externos; usuarios de ejemplo renombrados; y se agregaron `get_by`, WAL con `busy_timeout` y `DbConnection`.

| Fase | Estado |
|---|---|
| Documentación de contexto (`.ai/`) | ✅ Creada y actualizada |
| 1. Fundación | ✅ Completada |
| 2. Core de datos y seeders | ✅ Completada |
| 3. Feature `usuarios` | ✅ Completada |
| 4. Autenticación JWT | ⏭️ Pendiente (la implementa un compañero) |
| 5. Gestión de usuarios: modelo físico | 🚧 En curso: migraciones de usuarios, roles, permisos y relaciones creadas; faltan las features CRUD de catálogos y asignaciones |
| 6. Plantilla y documentación | ✅ `_template/` y README listos |

### Inventario de lo implementado (`backend/`)

| Archivo | Responsabilidad |
|---|---|
| `app/main.py` | `create_app()`: logging, handlers de error, CORS (en ese orden), `/health`, router de `usuarios`, migraciones al arrancar |
| `app/core/config.py` | `Settings` desde `backend/.env`; `TIMEZONE` validada al arrancar |
| `app/core/database.py` | `connect()` (WAL, `busy_timeout`, claves foráneas), `get_db()`, `DbConnection`, `run_migrations()`, `migration_status()`, `utc_now_iso()`, `local_now()`, `to_local()` |
| `app/core/exceptions.py`, `error_handlers.py`, `log_config.py` | Errores propios, JSON uniforme, 500 con `error_id` y CORS, `IntegrityError` UNIQUE → 409 |
| `app/core/base_schema.py` | `AuditSchema`, `PageSchema[T]`, `SortDirection` |
| `app/core/base_repository.py` | CRUD genérico: `get_by_id`, `get_by`, `list_all` y `count` (con `filters`, `ranges`, `search`), `exists_by`, `create`, `update`, `soft_delete` |
| `app/core/list_filters.py` | Dependencia `list_filters`: parámetros `q`, `created_from`, `created_to` reutilizables en cualquier router |
| `app/core/base_seeder.py`, `app/seeders/` | Clase base y `UsuarioSeeder` (4 activos + 1 eliminado) |
| `app/core/security.py` | `hash_password`, `verify_password` (argon2). El JWT es de la fase 4 |
| `app/features/usuarios/` | `repository`, `schemas`, `service`, `router`: CRUD completo con listado filtrable (`q`, `created_from`, `created_to`) |
| `app/features/auth/` | Carpeta vacía, lista para la fase 4 |
| `app/features/_template/` | Molde de feature con CRUD completo (entidad `Ejemplo`): `README.md` con los pasos, `repository`, `schemas`, `service`, `router` y `migration.sql.example`. Probado en `tests/features/test_template.py`; no está registrado en `main.py` |
| `manage.py` | `migrate`, `migrate:status`, `db:seed`, `migrate:fresh [--seed]` |
| `migrations/001_create_usuarios.sql` | Tabla `usuarios` + índice único parcial de email |
| `tests/` | Core, seeders, manage, `main` y la feature `usuarios` |
| `requirements.txt`, `pyproject.toml`, `.env.example`, `.gitignore`, `README.md` | Configuración y documentación |

**No existe todavía:** autenticación, features CRUD de roles/permisos/asignaciones y colección de Postman.

## 9. Pendientes abiertos

- **Definir las entidades** (varias, cada una con su caso de uso): campos, relaciones con `usuarios` y qué es el "histórico". Sin esto no se puede empezar la fase 5.
- ¿Cada usuario ve solo sus propios registros o hay datos compartidos? Si es lo primero, se usa `filters={"user_id": ...}` desde el service.
- Filtros de listado: ya existen igualdad, lista, rango y búsqueda de texto (ver `ARCHITECTURE.md`, 5.4). Falta ver si alguna entidad necesita algo más (por ejemplo `OR` entre columnas u ordenar por varias columnas).
- Definir el catálogo inicial de permisos y las reglas de administración de roles. El modelo del MVP ya usa un único rol por usuario.
- Coordinar con el compañero de la fase 4: `get_current_user`, login, bootstrap del primer usuario y validación de `JWT_SECRET`.
- Si el frontend offline necesita ids generados en el cliente o resolución de conflictos, abrir una fase nueva (hoy fuera de alcance).
- Adaptar la colección de Postman.
- Probar CORS con el proyecto React real.
- Confirmar la fecha exacta del evento.

## 10. Bitácora

| Fecha | Sesión | Resultado |
|---|---|---|
| 2026-11-14 | Creación de `.ai/` | A partir de 4 documentos de un proyecto de entrenamiento previo, se adaptaron el contexto, el plan y la arquitectura. Cambio de alcance indicado por Brayan: sin análisis ni APIs externas (van en el frontend offline); el backend persiste datos e históricos y controla usuarios. Se descartaron `BaseApiClient`, `analysis.py` y la etapa NASA. Nombres de archivo en inglés |
| 2026-11-14 | Análisis del repo de entrenamiento | Se revisó el zip de `SEMA-ENTRENAMIENTO-BACKEND` (fases 1 a 3, sin JWT). Hallazgos: `BaseRepository` sin `get_by`, SQLite sin WAL y commit posterior a la respuesta |
| 2026-11-14 | Paso 1: estructura y core | Se importó `backend/` y se adaptó (sin NASA ni servicios externos, usuarios de ejemplo renombrados). Agregados: `get_by`, WAL + `busy_timeout`, `DbConnection` (commit antes de responder), `features/auth/` vacía. README y `requirements.txt` podado. Decisiones de Brayan: ids unsigned bigint, CRUD completo por entidad, sin lotes, JWT lo hace un compañero, Postman después. 158 tests, ruff limpio, probado con servidor real |
| 2026-11-14 | `features/_template/` | Molde de feature con CRUD completo (`Ejemplo`), con README de pasos y migración de ejemplo. Un test lo registra en una app de prueba y recorre el CRUD, y otro verifica que la migración coincide con el repositorio. Se comprobó creando una feature `cultivos` solo con los pasos del README. 171 tests |
| 2026-11-14 | Commit y filtros de listado | Commit `0922f98` "estructura inicial backend fast-api" (sin push). Después, filtros en el core: `filters` (igualdad, `NULL`, `IN`), `ranges` (inclusivo, fechas a UTC) y `search` (parcial, escapando `%`, `_` y `\`), todo con lista blanca y `?`; `count` con los mismos filtros para que `total` sea exacto. `list_filters` agrega `q`, `created_from` y `created_to` a `usuarios` y a la plantilla. Los tests de escape se comprobaron rompiendo el código a propósito. 228 tests, ruff limpio, servidor real probado |
| 2026-11-14 | Fase 1: modelo de gestión de usuarios | Se aprobó `correo`, campos opcionales `genero` y `telefono`, `is_active` independiente de `deleted_at`, y un único rol por usuario para el MVP. Las migraciones se separaron por tabla: evolución de `usuarios`, `roles`, `permisos`, `usuario_roles` y `rol_permisos`. JWT sigue fuera de esta etapa. |
| 2026-11-14 | Fase 2: feature usuarios | El CRUD de `usuarios` expone `genero`, `telefono` e `is_active`. Teléfono se valida como texto de 7 a 25 caracteres con dígitos, espacios, `+`, `-` y paréntesis. Los campos opcionales se pueden limpiar con `null` en PATCH; `is_active` sigue independiente del borrado lógico. |
| 2026-11-14 | Fase 3: feature roles | Se implementó el CRUD completo de `roles`: nombre único entre activos, descripción opcional, búsqueda, paginación y borrado lógico. Aún no hay JWT ni asignaciones de usuario a rol. |
