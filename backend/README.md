# SEMA Backend

API REST del proyecto **SEMA** (Sistema Espacial de Monitoreo Agrícola), construida con **FastAPI** y **SQLite**.

El backend **persiste datos e históricos** y **controla usuarios**. El análisis de información y las consultas a APIs externas se hacen en el frontend (funciona offline).

> **Estado:** arquitectura base lista. La autenticación JWT está pendiente. El avance por fases está en [../.ai/PLAN.md](../.ai/PLAN.md).

## Qué funciona hoy

| Funcionalidad | Estado |
|---|---|
| Servidor, Swagger (`/docs`) y `GET /health` | ✅ Disponible |
| CORS para el frontend (`CORS_ORIGINS`) | ✅ Disponible |
| Formato de error uniforme (incluye 500 con `error_id`) | ✅ Disponible |
| Migraciones automáticas y `manage.py` (`migrate`, `db:seed`, `migrate:fresh`) | ✅ Disponible |
| `BaseRepository`: CRUD genérico con borrado lógico y `get_by` | ✅ Disponible |
| Feature `usuarios` (CRUD con paginación, **sin token todavía**) | ✅ Disponible |
| Login y JWT (`/auth/login`, `/auth/me`, rutas protegidas) | 🔜 Pendiente |
| Entidades de datos e históricos | 🔜 Por definir |

## Documentación relacionada

| Documento | Contenido |
|---|---|
| [../.ai/ARCHITECTURE.md](../.ai/ARCHITECTURE.md) | Arquitectura en detalle y guía para agregar features. **Leer antes de programar** |
| [../.ai/PLAN.md](../.ai/PLAN.md) | Plan de implementación por fases |
| [../.ai/CONTEXT.md](../.ai/CONTEXT.md) | Contexto, protocolo de trabajo y estado actual |

## Stack

- Python 3.12 o superior
- FastAPI + Pydantic v2
- SQLite (`sqlite3`, sin ORM)
- PyJWT + contraseñas con argon2 (pwdlib)
- `pytest` + `ruff`

## Instalación

Requisitos: **Python 3.12 o superior** y Git.

- Windows: `py --version`. En Windows se usa **`py`**, no `python`: en muchos equipos `python` abre la Microsoft Store.
- Linux / macOS: `python3 --version`. En los comandos de este README, `py` se reemplaza por `python3`.

Desde la carpeta `backend/`, elegir **una** opción.

### Opción A: sin entorno virtual

**Windows (PowerShell)**
```powershell
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

**Linux / macOS**
```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Se usa `py -m pip` (y no `pip` a secas) para instalar en el mismo Python que ejecuta la app. Sin aislamiento, si otro proyecto necesita otra versión de una librería, una instalación pisa a la otra. En ese caso, usar la opción B.

### Opción B: con entorno virtual (opcional)

**Windows (PowerShell)**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

El entorno se activa en cada terminal nueva. `.venv/` está en `.gitignore`.

Después de instalar, editar `.env` con los valores propios.

## Variables de entorno

| Variable | Ejemplo | Descripción |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` o `production`. Con `production` se bloquean `db:seed` y `migrate:fresh` |
| `TIMEZONE` | `America/Bogota` | Zona horaria para la lógica que depende de la hora local. Si no existe, la app no arranca. **No** cambia las fechas de la API: esas salen en UTC |
| `DB_PATH` | `data/sema.db` | Ruta del archivo SQLite, relativa a `backend/` (se crea sola) |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Orígenes permitidos del frontend, en formato JSON |
| `JWT_SECRET` | *(cadena aleatoria de 32+ caracteres)* | Secreto para firmar tokens. **Nunca subirlo a Git** |
| `JWT_ALGORITHM` | `HS256` | Algoritmo de firma |
| `JWT_EXPIRE_MINUTES` | `60` | Duración del token en minutos |
| `FIRST_USER_EMAIL` | `admin@sema.example` | Email del primer usuario (lo usará la fase de autenticación) |
| `FIRST_USER_PASSWORD` | *(mínimo 8 caracteres)* | Contraseña del primer usuario |

Para generar un `JWT_SECRET` seguro:
```bash
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Ejecutar

```bash
py -m uvicorn app.main:app --reload
```

| URL | Qué es |
|---|---|
| http://localhost:8000/health | Verifica que la API está viva |
| http://localhost:8000/docs | Documentación interactiva (Swagger) |
| http://localhost:8000/redoc | Documentación alternativa |

Para que otro equipo de la red (por ejemplo, el frontend) llegue a la API, agregar `--host 0.0.0.0` y poner su origen en `CORS_ORIGINS`.

Al arrancar, la app aplica las migraciones pendientes de `migrations/`.

## Base de datos: migraciones y datos de ejemplo

`manage.py` reúne los comandos de la base de datos, al estilo de `php artisan`. Se ejecutan desde `backend/`:

| Comando | Qué hace |
|---|---|
| `py manage.py migrate` | Aplica las migraciones pendientes (la app también lo hace al arrancar) |
| `py manage.py migrate:status` | Muestra las migraciones aplicadas (`[x]`) y las pendientes (`[ ]`) |
| `py manage.py db:seed` | Llena la BD con datos de ejemplo. Se puede repetir sin duplicar |
| `py manage.py db:seed --class UsuarioSeeder` | Ejecuta solo un seeder |
| `py manage.py migrate:fresh --seed` | **Borra la BD**, la crea desde cero y la llena con datos de ejemplo |
| `py manage.py --help` | Ayuda |

`migrate:fresh` y `db:seed` están bloqueados con `ENVIRONMENT=production`.

**Una migración ya integrada nunca se edita:** para cambiar algo se crea una nueva con el siguiente número.

### Identificadores

Todas las tablas usan `id INTEGER PRIMARY KEY AUTOINCREMENT`. En SQLite es un entero de 64 bits que solo toma valores positivos (1, 2, 3...), es decir, en la práctica un *unsigned big integer*. No se declara como `BIGINT UNSIGNED` porque SQLite solo usa la columna como id de la fila si el tipo es exactamente `INTEGER PRIMARY KEY`.

### Usuarios de ejemplo

Todos usan la contraseña **`Sema2026!`** (solo para desarrollo):

| Email | Estado |
|---|---|
| `admin@sema.example` | Activo |
| `backend@sema.example` | Activo |
| `demo@sema.example` | Activo |
| `frontend@sema.example` | Activo |
| `eliminado@sema.example` | **Eliminado** (tiene `deleted_at`), para ver el borrado lógico |

### Ver la BD en un visor SQL

El archivo está en `backend/data/sema.db`. Se abre con **DB Browser for SQLite** o con la extensión **SQLite Viewer** de VS Code. En `usuarios`, `password_hash` empieza por `$argon2id$...`: la contraseña nunca se guarda en texto plano. La tabla `schema_migrations` registra qué migraciones se aplicaron y cuándo.

> Si `migrate:fresh` no puede borrar la BD, cerrar antes el visor SQL y el servidor: Windows bloquea los archivos abiertos.

## Endpoints disponibles

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado de la API |
| `POST` | `/usuarios` | Crear usuario |
| `GET` | `/usuarios?limit=&offset=&order_by=&direction=&q=&created_from=&created_to=` | Listar usuarios activos (paginado, ordenado y filtrado) |
| `GET` | `/usuarios/{id}` | Obtener usuario |
| `PATCH` | `/usuarios/{id}` | Actualizar usuario (parcial) |
| `DELETE` | `/usuarios/{id}` | Eliminar usuario (borrado lógico) |

**Hoy los endpoints de `/usuarios` funcionan sin token.** La protección llega con la fase de autenticación (`/auth/login`, `/auth/me` y `get_current_user`).

### Listar con paginación, orden y filtros

| Parámetro | Por defecto | Valores |
|---|---|---|
| `limit` | `20` | de 1 a 100 |
| `offset` | `0` | 0 o más (cuántos registros saltar) |
| `order_by` | `id` | `id`, `nombre`, `email`, `created_at` |
| `direction` | `asc` | `asc`, `desc` |
| `q` | *(sin filtro)* | Texto a buscar en `nombre` y `email`. Parcial y sin distinguir mayúsculas (solo ASCII: no ignora el caso de tildes ni de la ñ). `%` y `_` se buscan como texto normal |
| `created_from` | *(sin filtro)* | Creados desde esta fecha y hora, inclusive. ISO 8601 en UTC con `Z`: `2026-11-14T00:00:00Z`. Sin zona horaria se asume UTC |
| `created_to` | *(sin filtro)* | Creados hasta esta fecha y hora, inclusive |

Los filtros se combinan con AND, y `total` cuenta **solo lo que cumple los filtros**. Si `created_from` es posterior a `created_to`, responde **400**. En una URL, el `+` de un offset horario debe ir como `%2B` (con `Z` no hace falta).
`GET /usuarios?limit=2&order_by=nombre` responde:
```json
{
  "items": [
    { "id": 1, "nombre": "Admin SEMA", "email": "admin@sema.example",
      "created_at": "2026-11-14T19:09:45Z", "updated_at": "2026-11-14T19:09:45Z" },
    { "id": 2, "nombre": "Equipo Backend", "email": "backend@sema.example",
      "created_at": "2026-11-14T19:09:45Z", "updated_at": "2026-11-14T19:09:45Z" }
  ],
  "total": 4,
  "limit": 2,
  "offset": 0
}
```
`total` es la cantidad de usuarios activos: con `limit` y `offset` el frontend arma la paginación (página 2 → `offset=2`).

### Reglas de los datos de usuario

- `email` se guarda en minúsculas y sin espacios, y es único entre los usuarios activos. Si ya existe, responde **409**. Un usuario eliminado no bloquea su email.
- `nombre`: de 2 a 100 caracteres, sin espacios al inicio ni al final.
- `password`: de 8 a 128 caracteres. Se guarda con hash y **nunca** aparece en una respuesta.
- `PATCH` cambia solo los campos enviados. Un campo con `null` o un campo desconocido responde **422**.
- **Fechas:** `created_at` y `updated_at` salen en **UTC**, ISO 8601 (`"2026-11-14T19:09:45Z"`). Mostrarlas en hora local es trabajo del frontend:
  ```js
  new Date("2026-11-09T00:17:45Z").toLocaleString("es-CO", { timeZone: "America/Bogota" })
  ```
- El body debe ser JSON en **UTF-8** (si no, responde **400**). Tildes, ñ, otros alfabetos y emojis se guardan intactos.

### Formato de error

Todas las respuestas de error tienen la misma forma:
```json
{ "error": { "code": "NOT_FOUND", "message": "Usuario 7 no existe" } }
```

Los errores de validación (422) agregan `details` con cada campo inválido:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Datos de entrada inválidos",
    "details": [{ "field": "body.email", "message": "value is not a valid email address" }]
  }
}
```

Los errores internos (500) nunca muestran detalles. Traen un `error_id` que también aparece en la consola del servidor con la traza completa:
```json
{ "error": { "code": "INTERNAL_ERROR", "message": "Error interno", "error_id": "74adeaa35cb2" } }
```
**Si el frontend ve un 500:** copiar el `error_id` y buscarlo en la consola donde corre `uvicorn`.

## Estructura

```
backend/
├── app/
│   ├── main.py          # arma la app: CORS, errores, routers
│   ├── core/            # infraestructura compartida (BD, errores, clases base)
│   ├── features/        # una carpeta por funcionalidad
│   │   ├── _template/   # molde para entidades nuevas (CRUD completo)
│   │   ├── auth/        # (pendiente) login y protección de rutas
│   │   └── usuarios/    # CRUD de usuarios: el molde para las demás features
│   └── seeders/         # datos de ejemplo para desarrollo
├── migrations/          # scripts SQL numerados
├── tests/               # misma estructura que app/
├── data/                # base de datos local (no se sube a Git)
└── manage.py            # comandos de BD
```

Dentro de cada feature el flujo siempre es `router → service → repository`. La explicación completa está en [../.ai/ARCHITECTURE.md](../.ai/ARCHITECTURE.md).

### `BaseRepository`: lo que ya trae cada repositorio

Cada repositorio solo declara su tabla y columnas (ver `features/usuarios/repository.py`) y hereda:

| Método | Qué hace |
|---|---|
| `get_by_id(id)` | Un registro activo, o `None` |
| `get_by(column, value, include_deleted=False)` | El primer registro activo con ese valor en la columna, o `None` |
| `list_all(limit, offset, order_by, direction, *, filters, ranges, search)` | Listado paginado, ordenado y filtrado |
| `count(*, filters, ranges, search)` | Cantidad de registros activos que cumplen los filtros |
| `exists_by(column, value, exclude_id, include_deleted)` | ¿Existe un registro con ese valor? |
| `create(data)` | Inserta y agrega `created_at` y `updated_at` |
| `update(id, data)` | Actualiza solo los campos recibidos |
| `soft_delete(id)` | Borrado lógico (`deleted_at`) |

Las columnas se validan contra una lista blanca: cualquier otra lanza `InvalidFieldError` (400).

**Filtros de `list_all` y `count`** (los valores siempre viajan como parámetros `?`):

| Argumento | Ejemplo | Efecto |
|---|---|---|
| `filters` | `{"estado": "activo"}` | Igualdad. `None` → `IS NULL`. Una lista → `IN` (hasta 100 valores) |
| `ranges` | `{"created_at": (desde, hasta)}` | Rango inclusivo. Cualquier límite puede ser `None`. Los `datetime` se convierten a UTC |
| `search` | `"maíz"` | Texto parcial en las columnas de `searchable` |

Se puede filtrar por las `columns` del repositorio más `id`, `created_at` y `updated_at`. Para habilitar la búsqueda, el repositorio declara `searchable = ("nombre", "email")`. En un router, `Depends(list_filters)` (de `app/core/list_filters.py`) agrega `q`, `created_from` y `created_to`.

## Agregar una feature nueva (resumen)

El molde es [`app/features/_template/`](app/features/_template/README.md), con CRUD completo y los pasos exactos.

1. Crear la rama `feature/<nombre>`.
2. Copiar `_template/` y reemplazar `ejemplo` por el nombre de la entidad. Si guarda datos, agregar una migración nueva en `migrations/` (hay una de ejemplo en `_template/`).
3. Escribir `schemas.py` y compartirlo con el frontend (es el contrato).
4. Escribir `repository.py` (extiende `BaseRepository`).
5. Escribir `service.py` con la lógica.
6. Escribir `router.py` y registrarlo en `main.py`. La conexión se pide con `connection: DbConnection`.
7. Agregar tests, correr `ruff check .` y `pytest`.

La guía detallada está en [../.ai/ARCHITECTURE.md](../.ai/ARCHITECTURE.md), sección 9. Otro ejemplo completo: `app/features/usuarios/`.

## Calidad

```bash
py -m ruff format .     # formato automático
py -m ruff check .      # estilo y seguridad (incluye detección de SQL inseguro)
py -m pytest -q         # pruebas
```

Los tests usan una BD temporal: nunca tocan `data/sema.db`. Un cambio solo se integra con `ruff check .` y `pytest` en verde.

## Reglas de oro

1. **Nada de lógica en los routers.**
2. **Nada de SQL fuera de los repositorios**, y siempre con parámetros `?`. Nunca f-strings con datos externos.
3. **Nunca devolver datos sensibles** (por ejemplo, `password_hash`).
4. **Toda ruta nueva va protegida** cuando exista la autenticación, salvo que sea pública a propósito.
5. **Nunca subir `.env`** ni archivos `.db` a Git.
6. **Una feature no importa el repository de otra**, solo su service.
