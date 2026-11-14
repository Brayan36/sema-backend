"""Comandos de mantenimiento de la base de datos (similar a `php artisan` de Laravel).

Uso, desde la carpeta backend/ (en Linux/macOS: python3; en Windows: py):
    py manage.py migrate                 aplica las migraciones pendientes
    py manage.py migrate:status          muestra qué migraciones están aplicadas
    py manage.py migrate:fresh [--seed]  borra la BD, migra desde cero y opcionalmente siembra
    py manage.py db:seed [--class X]     ejecuta todos los seeders, o solo el indicado
"""

import argparse
import sys

from app.core.config import settings
from app.core.database import connect, migration_status, run_migrations
from app.seeders import SEEDERS

DEV_ONLY_COMMANDS = ("migrate:fresh", "db:seed")


def migrate() -> None:
    connection = connect()
    try:
        applied = run_migrations(connection)
    finally:
        connection.close()
    if not applied:
        print("No hay migraciones pendientes.")
    for name in applied:
        print(f"  Migrada: {name}")


def status() -> None:
    connection = connect()
    try:
        rows = migration_status(connection)
    finally:
        connection.close()
    if not rows:
        print("No hay archivos en migrations/.")
    for name, applied_at in rows:
        print(f"  {'[x]' if applied_at else '[ ]'} {name}  {applied_at or 'pendiente'}")


def fresh(seed: bool) -> None:
    db_files = [
        settings.db_path.with_name(settings.db_path.name + suffix) for suffix in ("-wal", "-shm")
    ]
    try:
        for file in [settings.db_path, *db_files]:
            file.unlink(missing_ok=True)
    except PermissionError:
        sys.exit(
            "No se pudo borrar la BD: ciérrala en el servidor o en el visor SQL e intenta de nuevo."
        )
    print(f"BD eliminada: {settings.db_path.name}")
    migrate()
    if seed:
        db_seed(None)


def db_seed(seeder_name: str | None) -> None:
    seeders = SEEDERS
    if seeder_name:
        seeders = [s for s in SEEDERS if s.__name__ == seeder_name]
        if not seeders:
            available = ", ".join(s.__name__ for s in SEEDERS)
            sys.exit(f"Seeder '{seeder_name}' no existe. Disponibles: {available}")

    connection = connect()
    try:
        run_migrations(connection)
        for seeder_class in seeders:
            created = seeder_class(connection).run()
            connection.commit()
            print(f"  {seeder_class.__name__}: {created} registros creados")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="manage.py", description="Comandos de la base de datos")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("migrate", help="Aplica las migraciones pendientes")
    commands.add_parser("migrate:status", help="Muestra el estado de cada migración")
    fresh_parser = commands.add_parser("migrate:fresh", help="Borra la BD y migra desde cero")
    fresh_parser.add_argument("--seed", action="store_true", help="Ejecuta los seeders al final")
    seed_parser = commands.add_parser("db:seed", help="Llena la BD con datos de ejemplo")
    seed_parser.add_argument("--class", dest="seeder_class", help="Nombre de un seeder concreto")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if args.command in DEV_ONLY_COMMANDS and settings.environment == "production":
        sys.exit(f"'{args.command}' no está permitido con ENVIRONMENT=production.")

    if args.command == "migrate":
        migrate()
    elif args.command == "migrate:status":
        status()
    elif args.command == "migrate:fresh":
        fresh(seed=args.seed)
    elif args.command == "db:seed":
        db_seed(args.seeder_class)


if __name__ == "__main__":
    main()
