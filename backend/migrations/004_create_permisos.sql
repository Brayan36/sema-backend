-- Catálogo de permisos. JWT y la autorización los utilizarán en una fase posterior.
CREATE TABLE permisos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    descripcion TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    deleted_at  TEXT
);

CREATE UNIQUE INDEX ux_permisos_nombre_activo ON permisos (nombre) WHERE deleted_at IS NULL;
