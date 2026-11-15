-- Catálogo base de acceso: lo mínimo para que el sistema sea administrable desde cero.
--   admin       administra todos los catálogos y usuarios (de momento, un solo usuario)
--   agricultor  usuario de gestión agrícola (consulta)
-- Es idempotente: no duplica lo que ya exista (por ejemplo en BDs sembradas con db:seed).

INSERT INTO roles (nombre, descripcion, created_at, updated_at)
SELECT 'admin', 'Administrador del sistema',
       strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now'), strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now')
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'admin' AND deleted_at IS NULL);

INSERT INTO roles (nombre, descripcion, created_at, updated_at)
SELECT 'agricultor', 'Usuario de gestión agrícola',
       strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now'), strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now')
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE nombre = 'agricultor' AND deleted_at IS NULL);

INSERT INTO permisos (nombre, descripcion, created_at, updated_at)
SELECT base.nombre, base.descripcion,
       strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now'), strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now')
FROM (
    SELECT 'usuarios.crear' AS nombre, 'Registrar usuarios' AS descripcion
    UNION ALL SELECT 'usuarios.consultar', 'Consultar usuarios'
    UNION ALL SELECT 'usuarios.actualizar', 'Actualizar usuarios'
    UNION ALL SELECT 'usuarios.eliminar', 'Desactivar usuarios'
    UNION ALL SELECT 'historicos.consultar', 'Consultar históricos'
) AS base
WHERE NOT EXISTS (
    SELECT 1 FROM permisos WHERE nombre = base.nombre AND deleted_at IS NULL
);

-- admin: todos los permisos. agricultor: consultar usuarios e históricos.
INSERT OR IGNORE INTO rol_permisos (rol_id, permiso_id)
SELECT r.id, p.id
FROM roles r JOIN permisos p
WHERE r.nombre = 'admin' AND r.deleted_at IS NULL AND p.deleted_at IS NULL
  AND p.nombre IN ('usuarios.crear', 'usuarios.consultar', 'usuarios.actualizar',
                   'usuarios.eliminar', 'historicos.consultar');

INSERT OR IGNORE INTO rol_permisos (rol_id, permiso_id)
SELECT r.id, p.id
FROM roles r JOIN permisos p
WHERE r.nombre = 'agricultor' AND r.deleted_at IS NULL AND p.deleted_at IS NULL
  AND p.nombre IN ('usuarios.consultar', 'historicos.consultar');
