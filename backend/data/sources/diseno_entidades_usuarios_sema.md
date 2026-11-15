# SEMA — Diseño de entidades para la gestión de usuarios

> **Estado:** propuesta para revisión. No es una estructura SQL aprobada. Validar campos, relaciones y reglas con Brayan antes de implementar migraciones.

## 1. `usuarios` — Gestión de usuarios

**Propósito:** almacenar la información de las personas que tienen una cuenta en SEMA, identificarlas y conservar los datos necesarios para gestionar su cuenta y autenticación.

**Funcionalidades**
- Registrar usuarios e identificarlos mediante un ID.
- Almacenar datos personales y correo electrónico.
- Almacenar la contraseña únicamente como hash seguro.
- Consultar y actualizar la información del usuario.
- Gestionar el estado de la cuenta, si se confirma ese campo.
- Mantener fechas de creación y actualización.

**Campos propuestos**

| Campo | Función |
|---|---|
| `id` | Identificador único. |
| `nombre` | Nombre de la persona. |
| `correo` | Correo para identificar e iniciar sesión. |
| `password_hash` | Contraseña almacenada mediante hash seguro. |
| `genero` | Información de género, si el proyecto realmente la necesita. |
| `telefono` | Número de contacto. |
| `created_at` | Fecha de creación. |
| `updated_at` | Fecha de última actualización. |
| `is_active` | Estado de la cuenta, si se confirma. |
| `deleted_at` | Auditoría para borrado lógico; es independiente de `is_active`. |

**Ejemplo:** una persona se registra en SEMA y su información se almacena en `usuarios`. La asignación de roles y la determinación de permisos se gestionan mediante las demás entidades.

---

## 2. `roles` — Clasificación de usuarios

**Propósito:** definir los perfiles o roles que pueden existir dentro de SEMA. Un rol agrupa responsabilidades y capacidades.

En el MVP se han mencionado dos roles principales:
- `admin`: administrador del sistema.
- `agricultor`: usuario que utiliza las funcionalidades destinadas a la gestión agrícola.

**Funcionalidades**
- Registrar los roles disponibles.
- Identificar cada rol mediante un ID.
- Almacenar nombre y descripción.
- Permitir asignar un mismo rol a diferentes usuarios.
- Servir como agrupador de permisos.

**Campos propuestos**

| Campo | Función |
|---|---|
| `id` | Identificador único del rol. |
| `nombre` | Nombre del rol. |
| `descripcion` | Explicación de su responsabilidad. |

**Ejemplo:** si existen muchos agricultores y varios administradores, se definen los roles una sola vez y se asignan a los usuarios correspondientes.

---

## 3. `permisos` — Acciones autorizadas

**Propósito:** definir las acciones específicas que pueden ejecutarse dentro de SEMA. Cada permiso representa una capacidad concreta que puede concederse a uno o varios roles.

**Funcionalidades**
- Registrar las acciones disponibles.
- Identificar cada permiso mediante un ID.
- Describir qué operación permite realizar.
- Asociar permisos a diferentes roles.
- Facilitar cambios en las autorizaciones sin modificar individualmente cada usuario.

**Campos propuestos**

| Campo | Función |
|---|---|
| `id` | Identificador único del permiso. |
| `nombre` | Nombre de la acción autorizada. |
| `descripcion` | Explicación de lo que permite realizar. |

**Ejemplos ilustrativos de permisos**

| Permiso | Funcionalidad |
|---|---|
| `usuarios.crear` | Registrar usuarios. |
| `usuarios.consultar` | Consultar usuarios. |
| `usuarios.actualizar` | Modificar información de usuarios. |
| `usuarios.eliminar` | Desactivar o eliminar usuarios, según la regla definida. |
| `historicos.consultar` | Consultar registros históricos. |

Estos nombres son ejemplos; el catálogo real de permisos está pendiente de definición.

---

## 4. `usuario_roles` — Asignación de roles

**Propósito:** relacionar `usuarios` con `roles`. Para el MVP, un usuario puede tener **un solo rol** y un mismo rol puede asignarse a muchos usuarios.

**Funcionalidades**
- Asignar roles a usuarios.
- Consultar los roles de un usuario.
- Identificar qué usuarios pertenecen a un rol.
- Modificar las asignaciones.

**Campos propuestos**

| Campo | Función |
|---|---|
| `usuario_id` | Clave foránea hacia `usuarios` y clave primaria: asegura un único rol por usuario. |
| `rol_id` | Clave foránea hacia `roles`. |

`usuario_id` es la clave primaria; `rol_id` es una clave foránea obligatoria.

**Ejemplo ilustrativo**

| usuario_id | rol_id |
|---:|---:|
| 1 | 1 |
| 2 | 2 |

El usuario 1 tiene el rol 1; el usuario 2 tiene el rol 2.

---

## 5. `rol_permisos` — Asignación de permisos

**Propósito:** relacionar `roles` con `permisos` y determinar qué acciones están autorizadas para cada rol. En la propuesta es una relación de muchos a muchos: un rol puede tener varios permisos y un permiso puede asociarse a varios roles.

**Funcionalidades**
- Asignar permisos a roles.
- Consultar los permisos de un rol.
- Identificar qué roles pueden ejecutar una acción.
- Modificar las capacidades de un rol sin modificar individualmente cada usuario.

**Campos propuestos**

| Campo | Función |
|---|---|
| `rol_id` | Clave foránea hacia `roles`. |
| `permiso_id` | Clave foránea hacia `permisos`. |

En el diseño propuesto, ambos campos forman una clave primaria compuesta.

**Ejemplo ilustrativo**

| rol_id | permiso_id |
|---:|---:|
| 1 | 1 |
| 1 | 2 |
| 1 | 3 |
| 1 | 4 |
| 2 | 4 |

La asignación real de permisos a cada rol está pendiente de definición.

---

## Cómo trabajan las cinco entidades juntas

Cuando un usuario inicia sesión:

1. **`usuarios`:** el sistema identifica al usuario y verifica sus credenciales.
2. **`usuario_roles`:** consulta qué roles tiene asignados.
3. **`roles`:** identifica los roles asignados.
4. **`rol_permisos`:** consulta los permisos asociados a esos roles.
5. **`permisos`:** identifica las acciones autorizadas.

Por ejemplo, si un agricultor intenta consultar un histórico, el backend debe comprobar que tenga el permiso correspondiente antes de permitir la operación.

**Regla de seguridad:** la autorización debe verificarse en el backend. No se debe confiar únicamente en controles implementados en el frontend.

## Resumen de responsabilidades

| Entidad | Responsabilidad |
|---|---|
| `usuarios` | Identidad y datos de las cuentas. |
| `roles` | Perfiles de acceso. |
| `permisos` | Acciones autorizadas. |
| `usuario_roles` | Relaciona usuarios con roles. |
| `rol_permisos` | Relaciona roles con permisos. |

## Decisiones pendientes de validar con Brayan

Antes de convertir el diseño en migraciones SQL, confirmar:

1. **Multiplicidad de roles:** confirmada para el MVP: cada usuario tendrá un único rol.
2. **Catálogo de permisos:** ¿qué acciones concretas necesita SEMA y cuáles corresponden a cada rol?
3. **Gestión de cuentas:** ¿los usuarios se desactivarán mediante borrado lógico y quién podrá crear, modificar o desactivar cuentas?

## Nota final

Este documento describe una propuesta conceptual para discutir y validar. Los campos, tipos de datos, restricciones, relaciones definitivas y reglas de autorización deben acordarse con Brayan y contrastarse con la arquitectura vigente antes de implementar la base de datos.
