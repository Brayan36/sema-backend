CREATE TABLE rol_permisos (
    rol_id     INTEGER NOT NULL,
    permiso_id INTEGER NOT NULL,
    PRIMARY KEY (rol_id, permiso_id),
    FOREIGN KEY (rol_id) REFERENCES roles (id),
    FOREIGN KEY (permiso_id) REFERENCES permisos (id)
);

CREATE INDEX ix_rol_permisos_permiso_id ON rol_permisos (permiso_id);
