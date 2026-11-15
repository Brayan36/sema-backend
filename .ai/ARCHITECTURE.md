# Arquitectura del backend SEMA

> Referencia técnica. Plan por fases: [PLAN.md](PLAN.md). Protocolo y estado: [CONTEXT.md](CONTEXT.md).

**Estado (2026-11-14):**

| Pieza | Estado |
|---|---|
| `core/` (config, database, base_repository, base_schema, errores, logging, base_seeder) | ✅ Implementado |
| `core/security.py`: hash de contraseñas | ✅ Implementado |
| `core/security.py`: JWT, y `features/auth/` | 📝 Diseño (fase 4, la implementa un compañero) |
| `manage.py` y seeders | ✅ Implementado |
| Feature `usuarios` | ✅ Implementada (todavía sin protección de token) |
| Feature `roles` | ✅ Implementada (todavía sin protección de token) |
| Gestión de usuarios: modelo físico | 🚧 Migraciones creadas; faltan features CRUD de roles, permisos y asignaciones |
| `features/_template/` | ✅ Molde de feature con CRUD completo y probado (no registrado en `main.py`) |

Lo implementado vive en `backend/`: **el código gana sobre este documento** y el documento se corrige. Las secciones de diseño (autenticación) son guía y pueden ajustarse respetando las reglas.

## 1. Arquitectura: modular por feature, capas por dentro, core compartido

- **Por feature (por fuera):** todo lo de un tema vive en una carpeta (`usuarios`, `auth`, ...). Cada persona trabaja en la suya sin chocar en Git.
- **Por capas (por dentro):** router, schemas, service y repository (Principio de Responsabilidad Única).
- **Core compartido:** lo repetible (BD, CRUD genérico, errores, seguridad) se escribe una vez en `core/`.

```
Frontend (React/PWA, offline) ──HTTP──► main.py (CORS, handlers, routers)
                                          │
                  features/auth      features/usuarios      features/<entidad>
                  router→service     router→service         router→service
                                          │
                                       repository
                                          │
        core/ config · database · base_repository · base_schema · security · exceptions
                                          │
                                    SQLite (data/)
```

No hay capa de clientes externos ni de análisis: el backend no consulta APIs ni calcula recomendaciones.

## 2. Estructura de carpetas (objetivo)

```
.ai/                           # este contexto
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py · database.py · base_repository.py · base_schema.py · list_filters.py
│   │   ├── base_seeder.py · security.py · exceptions.py
│   │   └── error_handlers.py · log_config.py
│   ├── features/
│   │   ├── _template/         # molde para features nuevas (README, repository, schemas, service, router, migración de ejemplo)
│   │   ├── auth/              # login y protección de rutas (fase 4, vacía por ahora)
│   │   ├── usuarios/          # repository, schemas, service, router (molde de las features)
│   │   └── <entidad>/         # una carpeta por entidad de datos (fase 5, por definir)
│   └── seeders/
├── migrations/                # scripts SQL numerados
├── tests/                     # misma estructura que app/
├── data/                      # archivo .db (no va a Git)
├── manage.py                  # comandos de BD
├── requirements.txt · pyproject.toml · .env.example · .gitignore · README.md
```

Cada paquete lleva un `__init__.py`.

## 3. Capas de una feature

Cada feature crea **solo los archivos que necesita**.

| Archivo | Responsabilidad | No puede |
|---|---|---|
| `router.py` | Recibir HTTP, validar con schemas, llamar al service | Tener lógica de negocio o SQL |
| `schemas.py` | Forma del JSON de entrada y salida (contrato con el frontend) | Tener lógica |
| `service.py` | Lógica de negocio | Conocer HTTP (`Request`, `HTTPException`, códigos) |
| `repository.py` | Acceso a la BD | Tener lógica de negocio |
| `dependencies.py` | Dependencias de FastAPI de la feature (si hacen falta) | — |

## 4. Reglas de dependencias

```
Dentro de una feature:  router → service → repository
Entre features:         service de A → service de B (nunca el repository de B)
Core:                   las features usan core; core NUNCA importa features
main.py:                único que conoce a todos
```

## 5. El core

### 5.1 `config.py`
`pydantic-settings` lee `.env`. Nadie más lee `os.environ`. Variables: `environment`, `timezone`, `db_path`, `cors_origins` (lista JSON), `jwt_secret`, `jwt_algorithm`, `jwt_expire_minutes`, `first_user_email`, `first_user_password`. `TIMEZONE` se valida al arrancar.

### 5.2 `database.py`
- Una conexión por petición, con commit o rollback juntos al final. Los repositorios **nunca** hacen commit.
- **En un router se pide con `connection: DbConnection`**, que es `Depends(get_db, scope="function")`. El `scope` hace que el commit ocurra **antes** de enviar la respuesta. Con `Depends(get_db)` a secas, FastAPI lo ejecuta después y un `GET` inmediato del cliente podría no ver lo que acaba de guardar (hay un test que lo verifica).
- `connect()` configura `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`, `journal_mode = WAL`, `busy_timeout = 5000` y `check_same_thread=False` (seguro porque la conexión no se comparte entre peticiones).
- **Ids:** toda tabla usa `id INTEGER PRIMARY KEY AUTOINCREMENT`: entero de 64 bits y positivo, el *unsigned big integer* práctico de SQLite.
- **Migraciones:** archivos `migrations/001_*.sql`. `run_migrations()` crea `schema_migrations`, corre los pendientes en orden y cada uno en una transacción con su registro. Una migración ya integrada **nunca se edita**; se crea otra. Sin rollback: en desarrollo se usa `migrate:fresh`.
- Fechas: se guardan en UTC ISO 8601. `local_now()` y `to_local()` solo para lógica que depende de la hora local.

### 5.3 `base_schema.py`
`AuditSchema` (`id`, `created_at`, `updated_at`; `deleted_at` no se expone), `PageSchema[T]` (`items`, `total`, `limit`, `offset`) y `SortDirection = Literal["asc", "desc"]`.

### 5.4 `base_repository.py`
Cada repositorio declara `table`, `columns` (escribibles y filtrables) y `sortable`. `BaseRepository` ofrece `get_by_id`, `get_by(column, value, include_deleted=False)`, `list_all`, `count`, `create`, `update`, `soft_delete` y `exists_by(..., exclude_id, include_deleted)`; valida su propia declaración; agrega timestamps; y todas las lecturas filtran `deleted_at IS NULL`. Devuelve `dict`; el service lo convierte a schema.

`get_by` devuelve el primer registro activo (menor `id`) cuya columna vale el valor pedido, o `None`. Ejemplo: `repository.get_by("email", "ana@sema.example")`. La columna debe estar en `columns`; si no, `InvalidFieldError` (400).

**Filtros de `list_all` y `count`** (argumentos de solo palabra clave; los valores siempre van con `?`):

| Argumento | Ejemplo | Efecto |
|---|---|---|
| `filters` | `{"user_id": 3}` | Igualdad. `None` → `IS NULL`. Lista → `IN` (máx. 100 valores; vacía → sin resultados) |
| `ranges` | `{"created_at": (desde, hasta)}` | Rango inclusivo; cada límite puede ser `None`. Los `datetime` se pasan a UTC. Mínimo > máximo → `InvalidFieldError` |
| `search` | `"maíz"` | `LIKE` parcial en las columnas de `searchable`, escapando `%`, `_` y `\`. Sin distinguir mayúsculas solo en ASCII (límite de SQLite) |

Se filtra por las `columns` del repositorio más `id`, `created_at` y `updated_at`; `deleted_at` nunca. Todo pasa por la lista blanca. `count` acepta los mismos filtros, así que el `total` de `PageSchema` cuenta lo filtrado: el service debe pasar **los mismos criterios** a `list_all` y a `count`. En los routers, `Depends(list_filters)` (`core/list_filters.py`) agrega los parámetros `q`, `created_from` y `created_to`; un filtro propio (por ejemplo `estado`) se agrega como `Query` y se pasa en `filters`. Si una entidad necesita otra forma de filtrar (por ejemplo `OR` entre columnas), se amplía el core con tests de inyección, no con SQL en el service.

Los **valores** siempre van con `?`. Los **identificadores** se interpolan solo después de pasar la lista blanca; por eso este es el único archivo que puede usar `# noqa: S608`.

### 5.5 `security.py`
Funciones puras: `hash_password` / `verify_password` (`pwdlib`, argon2) y `create_access_token` / `decode_access_token` (PyJWT; `sub` como string; `algorithms=[...]` explícito al decodificar).

### 5.6 Errores
Los services lanzan excepciones propias (`AppError` y subclases) sin saber de HTTP; un handler central las traduce a un JSON uniforme:

```json
{ "error": { "code": "NOT_FOUND", "message": "Usuario 7 no existe" } }
```

| Situación | HTTP | `code` |
|---|---|---|
| Datos inválidos, campos extra, `null` en PATCH | 422 | `VALIDATION_ERROR` (agrega `details`) |
| Body ilegible (no UTF-8) | 400 | `BAD_REQUEST` |
| Campo u orden no permitido | 400 | `INVALID_FIELD` |
| Sin token, token inválido o expirado, login fallido | 401 | `UNAUTHORIZED` (+ `WWW-Authenticate: Bearer`) |
| No existe o está eliminado | 404 | `NOT_FOUND` |
| Duplicado (service o `UNIQUE` de la BD) | 409 | `CONFLICT` |
| Error no controlado | 500 | `INTERNAL_ERROR` + `error_id` |

**Errores 500:** el cliente recibe un mensaje genérico y un `error_id`; el log guarda el mismo `error_id` con la traza; la transacción se deshace; y la respuesta conserva los headers de CORS gracias al middleware `catch_unexpected_errors`. **El orden en `main.py` importa:** `register_error_handlers(app)` va **antes** de `add_middleware(CORSMiddleware, ...)`. Hay que probarlo con un test.

`sqlite3.IntegrityError`: `UNIQUE` → 409; `NOT NULL`, `FOREIGN KEY` y `CHECK` → 500 (son errores del código).

### 5.7 `manage.py` y seeders
Comandos (solo `argparse`): `migrate`, `migrate:status`, `db:seed [--class X]`, `migrate:fresh [--seed]`. Los dos últimos se bloquean con `ENVIRONMENT=production`. Los seeders extienden `BaseSeeder`, insertan **a través de los repositorios**, son idempotentes (`exists_by(..., include_deleted=True)`) y se registran en la lista `SEEDERS`.

## 6. Seguridad SQL

Valores con `?`; identificadores solo de la lista blanca; dirección de orden validada con `Literal`; paginación acotada (`limit` 1 a 100); todo dato pasa primero por un schema; `ruff` con reglas `S`; tests de inyección. Detalle en [PLAN.md](PLAN.md), sección 6.

## 7. Autenticación y CORS

> La autenticación es la fase 4 y la implementa un compañero. Lo de abajo es el diseño acordado.

**Flujo:** `POST /auth/login` (formulario: `username` = email, `password`) → `{access_token, token_type: "bearer"}`. El frontend envía `Authorization: Bearer <token>`. `get_current_user` extrae el token, lo decodifica y consulta al usuario en la BD (existe y no está eliminado), o responde 401. Un usuario eliminado pierde el acceso de inmediato.

**¿Dependencia y no middleware?** Una dependencia solo afecta a las rutas que la piden: no bloquea `/docs`, `/health`, el login ni el preflight `OPTIONS` de CORS, y Swagger muestra el botón **Authorize**.

```python
router = APIRouter(prefix="/usuarios", tags=["usuarios"], dependencies=[Depends(get_current_user)])
```

| Ruta | Protegida |
|---|---|
| `/health`, `POST /auth/login`, `/docs`, `/openapi.json` | No |
| `GET /auth/me`, todo `/usuarios`, **toda feature nueva** | Sí |

**Primer usuario:** al arrancar, si no hay usuarios activos y existen `FIRST_USER_EMAIL` y `FIRST_USER_PASSWORD`, se crea ese usuario.

**Reglas:** los schemas de salida nunca incluyen `password_hash`; el login siempre responde "Credenciales inválidas"; `JWT_SECRET` solo en `.env` y, con `ENVIRONMENT=production`, la app no arranca si es el de ejemplo o tiene menos de 32 caracteres. Fuera de alcance por ahora: refresh tokens y recuperación de contraseña *(por definir)*. Roles y permisos se modelan en esta etapa, pero su aplicación mediante JWT se implementa después.

**CORS:** `allow_origins=settings.cors_origins` (nunca `*` con credenciales), métodos `GET, POST, PATCH, DELETE, OPTIONS` y headers `Authorization, Content-Type`. En desarrollo: `http://localhost:5173`. En el evento se agrega el origen real **solo en el `.env`**.

## 8. Convenciones

| Elemento | Convención | Ejemplo |
|---|---|---|
| Core y nombres de archivo | Inglés | `BaseRepository`, `get_by_id` |
| Carpeta de feature | Español, plural, minúsculas | `usuarios` |
| Archivos de capa | Inglés, fijos | `router.py`, `service.py` |
| Clases de feature | Dominio en español + rol en inglés | `UsuarioService` |
| Schemas | `<Entidad>Create`, `<Entidad>Update`, `<Entidad>Out` | `UsuarioCreate` |
| Métodos de service | Español, verbo | `crear`, `listar`, `obtener`, `actualizar`, `eliminar` |
| Tablas | Español, plural, snake_case | `usuarios` |
| Auditoría | Inglés, siempre | `id`, `created_at`, `updated_at`, `deleted_at` |
| Fechas | UTC, ISO 8601; el frontend las muestra en hora local | `2026-10-24T22:15:00Z` |
| JSON y rutas | snake_case / español, plural | `/usuarios/{id}` |

| Operación | Método | Éxito |
|---|---|---|
| Crear | `POST /recurso` | 201 + objeto |
| Listar | `GET /recurso` | 200 + `PageSchema` |
| Obtener | `GET /recurso/{id}` | 200 + objeto |
| Actualizar parcial | `PATCH /recurso/{id}` | 200 + objeto |
| Eliminar (lógico) | `DELETE /recurso/{id}` | 204 sin body |

## 9. Cómo agregar una feature

1. **Rama** nueva desde la rama base de trabajo.
2. **Copiar** `features/_template/` y reemplazar `ejemplo`/`Ejemplo` por el nombre de la entidad. Los pasos exactos están en `features/_template/README.md` (se probaron creando una feature de punta a punta). Borrar lo que no se use.
3. **Migración** `migrations/00X_create_<tabla>.sql` con `id`, `created_at`, `updated_at`, `deleted_at`. Aplicar con `manage.py migrate`.
4. **Schemas** (`Create`, `Update`, `Out`). Compartirlos con el frontend antes de seguir: son el contrato.
5. **Repository** extendiendo `BaseRepository` (`table`, `columns`, `sortable`).
6. **Service** con la lógica; lanza excepciones del core, nunca `HTTPException`.
7. **Router** con endpoints de 1 o 2 líneas y listado paginado. La conexión se pide con `connection: DbConnection` (nunca `Depends(get_db)`). Cuando exista la autenticación, agregar `dependencies=[Depends(get_current_user)]`.
8. **Registrar** el router en `main.py`.
9. **Tests** en `tests/features/<feature>/`: service sin HTTP y endpoints con `TestClient`.
10. **Verificar:** `ruff format .`, `ruff check .`, `pytest -q` y prueba en Swagger.

## 10. Entidades de datos e históricos *(por definir)*

El backend guardará **varias entidades**, cada una con su caso de uso y **CRUD completo**, con el mismo molde de `usuarios`. Alcance acordado:

| Tema | Decisión |
|---|---|
| Operaciones | Crear, listar (paginado), obtener, actualizar parcial y borrado lógico, por entidad |
| Lotes | No hay creación por lotes |
| Sincronización offline | Sin lógica especial por ahora. El frontend procesa offline y envía lo que corresponda con las operaciones CRUD normales |
| Ids | `INTEGER PRIMARY KEY AUTOINCREMENT` generado por el servidor |
| Motor | SQLite |

Pendiente de definir con el equipo: qué entidades son, qué campos tienen, cómo se relacionan con `usuarios` y si cada usuario ve solo sus propios registros. Si el frontend necesitara ids propios o resolución de conflictos, se abriría una fase nueva.

## 11. Pruebas

- `pytest` y `TestClient` (necesita `httpx2` con Starlette 1.x). Cada test usa una BD SQLite temporal; **nunca** se toca `data/sema.db`.
- Fixtures: `app` (con BD temporal) y `client` (ejecuta el lifespan). Cuando exista la autenticación, un fixture de auth entregará los headers `Authorization`.
- Nombres de test en inglés que describen el comportamiento; estructura preparar → ejecutar → verificar; `parametrize` para casos como la inyección SQL.
- Estructura de `tests/` igual a la de `app/`.

## 12. Checklist de PR

Igual que [PLAN.md](PLAN.md), sección 7, más: la feature no importa el repository de otra feature, las migraciones nuevas no editan las existentes, y se probó en Swagger.

## 13. Fuera de alcance

Análisis de datos, APIs externas, ORM, async en la BD, refresh tokens, Docker, despliegue en la nube, DDD, CQRS, `BaseService` genérico.
