-- Catálogo de roles. El borrado lógico conserva su trazabilidad.
CREATE TABLE roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    descripcion TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    deleted_at  TEXT
);

CREATE UNIQUE INDEX ux_roles_nombre_activo ON roles (nombre) WHERE deleted_at IS NULL;
