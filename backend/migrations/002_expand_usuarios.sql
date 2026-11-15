-- La primera migración creó `email`; el contrato público aprobado usa `correo`.
ALTER TABLE usuarios RENAME COLUMN email TO correo;
DROP INDEX ux_usuarios_email_activo;
CREATE UNIQUE INDEX ux_usuarios_correo_activo ON usuarios (correo) WHERE deleted_at IS NULL;

ALTER TABLE usuarios ADD COLUMN genero TEXT;
ALTER TABLE usuarios ADD COLUMN telefono TEXT;
ALTER TABLE usuarios ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1
    CHECK (is_active IN (0, 1));
