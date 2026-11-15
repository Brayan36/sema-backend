# Colección de Postman: SEMA Backend API

Otra forma de probar la API además de Swagger (`/docs`): requests listos para importar, cada uno con **tests automáticos**.

| Archivo | Qué es |
|---|---|
| `SEMA-Backend.postman_collection.json` | La colección (formato Postman v2.1): 97 requests, 335 verificaciones |
| `SEMA-Local.postman_environment.json` | Environment para la API en tu equipo: `http://localhost:8000` |
| `SEMA-Red-Local.postman_environment.json` | Para probar desde otro equipo de la red (por ejemplo, en el evento). Cambiar `CAMBIAR-POR-IP-DEL-BACKEND` por la IP de quien corre la API |

## Cómo usarla

1. **Preparar la BD con datos de ejemplo**, desde `backend/` (la colección usa los usuarios `admin` y `demo` que crea el seeder):
   ```bash
   .venv/bin/python manage.py migrate:fresh --seed        # Ubuntu (ver README del backend)
   py manage.py migrate:fresh --seed                      # Windows
   ```
2. **Levantar la API:**
   ```bash
   .venv/bin/python -m uvicorn app.main:app --reload      # Ubuntu
   py -m uvicorn app.main:app --reload                    # Windows
   ```
   Para llegar desde otro equipo de la red, agregar `--host 0.0.0.0`.
3. **Importar en Postman:** *Import* → arrastrar los 3 archivos `.json`.
4. **Elegir el environment** arriba a la derecha: **SEMA - Local**.
5. **Probar:**
   - Todo de una vez: clic derecho en la colección → **Run collection** → *Run*. Corre en orden y **limpia lo que creó**.
   - Un request suelto: primero ejecutar `01 - Auth → Login admin (guarda token)`, que guarda el token en `{{token}}`.

## Contenido

| Carpeta | Qué prueba |
|---|---|
| `00 - Health` | Que la API esté arriba |
| `01 - Auth` | Login, `/auth/me`, contraseña incorrecta, correo inexistente (mismo mensaje), sin token, token inválido |
| `02 - Usuarios: flujo CRUD` | Crear (correo normalizado) → listar → buscar con `q` → filtrar por fecha → obtener → actualizar parcial (`null` limpia opcionales) → desactivar (no puede iniciar sesión) → cambiar contraseña |
| `03 - Usuarios: validaciones y errores` | 409, 422 (correo, contraseña, teléfono, campo desconocido, `null`), 404, `limit` y `order_by` inválidos, rango de fechas invertido (400), intento de inyección SQL y **el admin no puede eliminarse a sí mismo (409)** |
| `04 - Roles: CRUD` | Crear, buscar, obtener, actualizar, nombre duplicado (409), validaciones y 404 |
| `05 - Permisos: CRUD` | Igual que roles |
| `06 - Asignaciones` | Usuario↔rol (**un solo rol**: asignar otro reemplaza el anterior) y rol↔permisos (idempotente), en las dos direcciones |
| `07 - Autorización` | Roles base creados por la migración, **un solo admin**, demo/backend/frontend son `agricultor`, y qué puede hacer cada tipo de usuario (`admin`, `agricultor`, sin rol). Incluye dos regresiones: **un rol eliminado deja de conceder permisos** y **quien tiene `usuarios.eliminar` no puede eliminar al único admin (409)** |
| `99 - Limpieza` | Elimina lo creado y comprueba que el correo del usuario eliminado vuelve a estar disponible |

**Se ejecutan en orden:** cada request guarda variables (`usuario_id`, `rol_id`, `token`...) que usa el siguiente. Los datos llevan un `run_id` (la hora de la corrida), así que se puede repetir muchas veces sin chocar.

## Autenticación y permisos

- Bearer JWT. La colección define `Authorization: Bearer {{token}}` y todos los requests lo heredan, salvo los de login y los de error 401 (sin token) y los de la carpeta 07 (`{{token_demo}}`, `{{token_usuario}}`).
- `/roles`, `/permisos` y `/asignaciones` exigen el rol **`admin`**. `/usuarios` exige un permiso por operación: `usuarios.crear`, `usuarios.consultar`, `usuarios.actualizar`, `usuarios.eliminar`.
- Sin token: **401**. Con token pero sin rol o permiso: **403**.

## Variables

| Variable | Valor por defecto | Para qué |
|---|---|---|
| `base_url` | `http://localhost:8000` | Dirección de la API |
| `admin_correo` / `admin_password` | `admin@sema.example` / `Sema2026!` | Usuario con rol `admin` (seeder) |
| `demo_correo` / `demo_password` | `demo@sema.example` / `Sema2026!` | Usuario con rol `agricultor` (seeder) |

Las demás (`token`, `usuario_id`, `rol_id`, `run_id`...) las llenan los scripts. Si cambias las credenciales del seeder, cámbialas aquí.

## Verificaciones en todas las respuestas

Un script a nivel de colección revisa cada respuesta JSON: nunca aparece `password_hash` (ni `deleted_at` en las exitosas) y todo error trae el formato `{"error": {"code", "message"}}`.

## Ejecutar desde la terminal (opcional)

Con Node.js instalado, sin abrir Postman:
```bash
npx newman run SEMA-Backend.postman_collection.json -e SEMA-Local.postman_environment.json
```
Desde esta carpeta. Termina con código distinto de 0 si algo falla.

## Si algo falla

| Síntoma | Causa probable |
|---|---|
| `401` en `Login admin` | La BD no tiene los datos de ejemplo: correr `migrate:fresh --seed` |
| `403` en casi todo | El token es de un usuario sin rol `admin`. Volver a ejecutar `Login admin` |
| `401` en todo salvo el login | El token venció (60 min por defecto): ejecutar `Login admin` otra vez |
| Falla `Solo hay un admin` o `demo, backend y frontend son agricultores` | La BD no tiene los usuarios sembrados (`migrate:fresh --seed`), o ya había otro admin |
| Todo falla después de `el admin a sí mismo → 409` | Esa regla dejó de cumplirse y el admin quedó eliminado: re-sembrar con `migrate:fresh --seed` y corregir el código |
| `Could not get any response` | La API no está levantada o `base_url` es incorrecta |
