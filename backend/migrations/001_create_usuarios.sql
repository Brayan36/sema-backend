-- Convención de todas las tablas: `id INTEGER PRIMARY KEY AUTOINCREMENT`.
-- En SQLite es un entero de 64 bits (equivale a BIGINT) y solo toma valores
-- positivos al autogenerarse (1, 2, 3...), así que en la práctica es "unsigned".
-- No se declara como `BIGINT UNSIGNED`: SQLite solo convierte la columna en el
-- id de la fila (rowid) si el tipo es exactamente `INTEGER PRIMARY KEY`.
CREATE TABLE usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL,
    email         TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL,
    updated_at    TEXT    NOT NULL,
    deleted_at    TEXT
);

-- Email único solo entre usuarios activos: un usuario eliminado no bloquea su email.
CREATE UNIQUE INDEX ux_usuarios_email_activo ON usuarios (email) WHERE deleted_at IS NULL;
