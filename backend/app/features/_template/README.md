# Plantilla de feature (`_template`)

Molde para crear una entidad nueva con **CRUD completo**: crear, listar (paginado), obtener, actualizar parcial y borrado lógico. Es una feature real y probada (`tests/features/test_template.py`), pero **no está registrada** en `main.py` ni tiene tabla: no responde ninguna ruta.

La entidad de ejemplo se llama **Ejemplo** (tabla `ejemplos`, campos `nombre` y `descripcion`).

## Cómo crear una feature a partir de esta plantilla

Ejemplo: la entidad `cultivo`.

1. **Rama:** `git switch -c feature/cultivos`.
2. **Copiar** esta carpeta como `app/features/cultivos/` (sin `README.md` ni `migration.sql.example`) y **reemplazar**, en todos los archivos copiados:
   - `ejemplos` → `cultivos`, `ejemplo` → `cultivo`, `Ejemplo` → `Cultivo`, `EJEMPLO` → `CULTIVO`
   - `app.features._template` → `app.features.cultivos`
3. **Campos:** cambiar `nombre` y `descripcion` por los de la entidad, en los tres lugares que deben coincidir:
   - `repository.py` → `columns`, `sortable` y `searchable`
   - `schemas.py` → `...Create`, `...Update`, `...Out`, `Orden...` y `CAMPOS_NO_NULOS`
   - la migración (paso 4)
4. **Migración:** copiar `migration.sql.example` a `migrations/00X_create_cultivos.sql` (siguiente número libre), ajustar columnas y aplicar con `py manage.py migrate`.
5. **Schemas:** compartirlos con el frontend antes de seguir. Son el contrato.
6. **Service:** reemplazar `_validar_nombre_disponible` por las reglas reales. Borrarlo si no hay campos únicos. Si necesita otra feature, usar **su service**, nunca su repository.
7. **Router:** registrarlo en `app/main.py`:
   ```python
   from app.features.cultivos.router import router as cultivos_router

   app.include_router(cultivos_router)
   ```
   Cuando exista la autenticación, agregar `dependencies=[Depends(get_current_user)]` al `APIRouter`.
8. **Tests:** copiar `tests/features/test_template.py` a `tests/features/cultivos/` y adaptarlo.
9. **Filtros:** el listado ya trae `q`, `created_from` y `created_to`. Un filtro propio (por ejemplo `estado`) se agrega como parámetro `Query` en el router y se pasa al service como `filters={"estado": estado}`.
10. **Verificar** desde `backend/`: `py -m ruff format .`, `py -m ruff check .`, `py -m pytest -q` y probar en Swagger (`/docs`).

## Qué hace cada archivo

| Archivo | Responsabilidad |
|---|---|
| `repository.py` | Declara tabla, columnas, orden permitido y columnas de búsqueda (`searchable`). El CRUD y los filtros se heredan de `BaseRepository` |
| `schemas.py` | Contrato JSON de entrada y salida, con validaciones |
| `service.py` | Lógica de negocio. No conoce HTTP |
| `router.py` | Endpoints de una línea. Solo traduce HTTP |
| `migration.sql.example` | Plantilla de la tabla (no se ejecuta desde aquí) |

Cada feature crea **solo los archivos que necesita**. Detalle completo en [../../../../.ai/ARCHITECTURE.md](../../../../.ai/ARCHITECTURE.md).
