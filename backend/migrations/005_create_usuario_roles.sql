-- MVP: un usuario puede tener como máximo un rol. La PK sobre usuario_id
-- conserva la entidad de asociación y hace cumplir la cardinalidad en la BD.
CREATE TABLE usuario_roles (
    usuario_id INTEGER PRIMARY KEY,
    rol_id     INTEGER NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
    FOREIGN KEY (rol_id) REFERENCES roles (id)
);

CREATE INDEX ix_usuario_roles_rol_id ON usuario_roles (rol_id);
