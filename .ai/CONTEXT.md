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

**Consecuencia de diseño:** como el frontend trabaja sin conexión, el backend tendrá que aceptar datos que se generaron antes y llegan después. Esto afecta los identificadores, las fechas y los conflictos. Ver `PLAN.md`, fase 5, y la sección 9 (pendientes).

## 3. Equipo

- **Backend:** Brayan (autor de las decisiones) y Sebastián.
- **Frontend:** el resto del equipo, en otra app (React, preparada como PWA, con procesamiento offline). Como es otra app, **CORS es obligatorio**.
- Se prefiere la claridad sobre la sofisticación. Si algo se puede hacer más simple sin perder seguridad, se hace más simple.

## 4. Cómo retomar

1. Leer `.ai/README.md`, este archivo, `PLAN.md` y `ARCHITECTURE.md`.
2. Revisar el código en `backend/app/core/` (cuando exista).
3. Verificar el entorno desde `backend/`: `git status`, versión de Python (3.12 o superior), instalar `requirements.txt`, `ruff check .` y `pytest -q`.
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
| Entorno de Python | Sin `venv` por defecto; `venv` queda como opción documentada *(por confirmar)* |
| **Nuevo:** sin analítica ni APIs externas | Decisión de Brayan: lo hace el frontend (offline / `localStorage`) |

## 7. Trampas conocidas (heredadas, verificar al reproducirlas)

| # | Problema | Solución |
|---|---|---|
| 1 | En Windows, `python` abre la Microsoft Store | Usar `py` |
| 2 | `TestClient` de Starlette 1.x avisa que `httpx` está obsoleto | Verificar la dependencia de pruebas vigente al instalar (el original usaba `httpx2`) |
| 3 | Un método llamado `list` tapa el `list` de Python | Llamarlo `list_all` |
| 4 | Starlette responde los 500 fuera de CORS (falso error de CORS) | Middleware `catch_unexpected_errors`; `register_error_handlers(app)` va **antes** de `add_middleware(CORSMiddleware)` |
| 5 | `re.match` con `$` acepta un salto de línea final | Usar `fullmatch` |
| 6 | `executescript` no acepta parámetros ni abre transacción | Anteponer `BEGIN;` y registrar la migración antes del `commit` |
| 7 | FastAPI puede usar la conexión SQLite en otro hilo de la misma petición | `check_same_thread=False` (conexión por petición) |
| 8 | `EmailStr` rechaza `.local`, `.test`, `localhost` | Datos de ejemplo con `@sema.example` |
| 9 | Un PATCH con `null` termina en 500 por columna `NOT NULL` | `model_validator` que rechaza `null` + `model_dump(exclude_unset=True)` |
| 10 | Windows no trae base de zonas horarias | Dependencia `tzdata`; validar `TIMEZONE` al arrancar |
| 11 | `migrate:fresh` no borra la BD si está abierta (Windows) | Cerrar visor SQL y servidor antes |

## 8. Estado actual

**Fecha de corte:** 2026-11-14 · **Rama de trabajo:** `ccr-100e636c-48me4o` · **Código:** ninguno todavía

El repositorio solo contiene `LICENSE` y esta carpeta `.ai/`. **Todas las fases están pendientes.** Ver `PLAN.md`.

| Fase | Estado |
|---|---|
| Documentación de contexto (`.ai/`) | ✅ Creada (pendiente de revisión de Brayan) |
| 1. Fundación | Pendiente |
| 2. Core de datos y seeders | Pendiente |
| 3. Feature `usuarios` | Pendiente |
| 4. Autenticación JWT | Pendiente |
| 5. Persistencia de datos e históricos | Pendiente (requiere definir entidades) |
| 6. Plantilla y documentación | Pendiente |

## 9. Pendientes abiertos

- **Definir las entidades del histórico** y qué guarda cada una. Sin esto no se puede diseñar la fase 5.
- **Definir cómo sincroniza el frontend offline:** identificadores generados en el cliente (UUID o `client_id`), fecha original del registro vs. fecha de recepción, subida por lotes, idempotencia y resolución de conflictos.
- ¿Los usuarios tendrán roles o permisos? (el original los dejaba fuera de alcance).
- ¿Cada usuario ve solo su propio histórico o hay datos compartidos?
- Confirmar `venv` sí o no, y el sistema operativo del equipo (el original asumía Windows y `py`).
- Probar CORS con el proyecto React real.
- Confirmar la fecha exacta del evento.

## 10. Bitácora

| Fecha | Sesión | Resultado |
|---|---|---|
| 2026-11-14 | Creación de `.ai/` | A partir de 4 documentos de un proyecto de entrenamiento previo, se adaptaron el contexto, el plan y la arquitectura. Cambio de alcance indicado por Brayan: sin análisis ni APIs externas (van en el frontend offline); el backend persiste datos e históricos y controla usuarios. Se descartaron `BaseApiClient`, `analysis.py` y la etapa NASA. Nombres de archivo en inglés |
