"""Tworzenie i zapełnianie bazy kina.

Użycie (z katalogu backend/):
    uv run python -m app.db.init_db                       # pusta baza + dane stałe (sale, miejsca, gatunki)
    uv run python -m app.db.init_db --demo                # + przykładowe filmy i seanse
    uv run python -m app.db.init_db --admin-username admin --admin-email admin@kino.pl
    uv run python -m app.db.init_db --reset --demo        # skasuj plik bazy i zacznij od zera

Ścieżka bazy: --db albo zmienna CINEMA_DB_PATH (domyślnie backend/cinema.db).
Hasło administratora: zmienna CINEMA_ADMIN_PASSWORD albo pytanie w terminalu (nie przez argument).
Skrypt można uruchamiać wielokrotnie: istniejącej, zainicjalizowanej bazy nie rusza (bez --reset).
"""

from __future__ import annotations

import argparse
import getpass
import os
import sqlite3
import sys
from pathlib import Path

from app.core.clock import Clock, system_clock
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.connection import connect
from app.db.seed import seed_demo

SQL_DIR = Path(__file__).parent
SCHEMA_VERSION = 1  # musi zgadzać się z PRAGMA user_version na końcu schema.sql
MIN_PASSWORD_LEN = 8


def _remove_db_files(path: Path) -> None:
    for suffix in ("", "-wal", "-shm", "-journal"):
        Path(str(path) + suffix).unlink(missing_ok=True)


def is_initialized(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return bool(conn.execute("PRAGMA user_version").fetchone()[0] >= SCHEMA_VERSION)
    finally:
        conn.close()


def init_database(
    path: str | os.PathLike[str],
    clock: Clock = system_clock,
    *,
    reset: bool = False,
    demo: bool = False,
) -> bool:
    """Tworzy plik bazy, schemat i dane stałe. Zwraca True, jeśli baza została utworzona,
    False, jeśli już istniała (wtedy nic nie zmienia)."""
    path = Path(path)
    if reset:
        _remove_db_files(path)
    if is_initialized(path):
        return False
    if path.exists() and path.stat().st_size > 0:
        raise RuntimeError(
            f"{path} istnieje, ale nie jest zainicjalizowaną bazą kina. "
            "Użyj --reset, żeby ją skasować i utworzyć od nowa."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = connect(path, "owner", clock)
        try:
            conn.executescript((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))
            conn.executescript((SQL_DIR / "seed.sql").read_text(encoding="utf-8"))
            if demo:
                seed_demo(conn, clock)
        finally:
            conn.close()
    except BaseException:
        _remove_db_files(path)  # nie zostawiamy na wpół zainicjalizowanego pliku
        raise
    return True


def create_admin(
    path: str | os.PathLike[str],
    username: str,
    email: str,
    password: str,
    clock: Clock = system_clock,
) -> int:
    """Dodaje konto administratora (hasło trafia do bazy tylko jako hash bcrypt). Zwraca id konta.
    Rzuca sqlite3.IntegrityError, jeśli login lub e-mail są już zajęte, a ValueError, jeśli
    hasło jest za krótkie albo za długie."""
    if len(password) < MIN_PASSWORD_LEN:
        raise ValueError(f"Hasło musi mieć co najmniej {MIN_PASSWORD_LEN} znaków.")
    conn = connect(path, "owner", clock)
    try:
        cur = conn.execute(
            "INSERT INTO admin_accounts (username, email, password_hash, created_at) VALUES (?,?,?,?)",
            (username, email, hash_password(password), int(clock())),
        )
        if cur.lastrowid is None:  # po udanym INSERT nie powinno się zdarzyć
            raise RuntimeError("INSERT nie zwrócił id konta.")
        return cur.lastrowid
    finally:
        conn.close()


def _read_password() -> str:
    password = os.environ.get("CINEMA_ADMIN_PASSWORD")
    if password:
        return password
    password = getpass.getpass("Hasło administratora: ")
    if password != getpass.getpass("Powtórz hasło: "):
        raise SystemExit("Hasła się różnią.")
    return password


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inicjalizacja bazy danych kina.")
    parser.add_argument("--db", type=Path, default=None, help="ścieżka pliku bazy")
    parser.add_argument(
        "--reset", action="store_true", help="skasuj istniejącą bazę i utwórz od nowa"
    )
    parser.add_argument("--demo", action="store_true", help="dodaj przykładowe filmy i seanse")
    parser.add_argument("--admin-username")
    parser.add_argument("--admin-email")
    args = parser.parse_args(argv)
    if bool(args.admin_username) != bool(args.admin_email):
        parser.error("--admin-username i --admin-email podaje się razem")

    path = args.db or get_settings().db_path
    created = init_database(path, reset=args.reset, demo=args.demo)
    print(f"Baza {path}: " + ("utworzona." if created else "już istnieje, bez zmian."))
    if not created and args.demo:
        print("  (--demo działa tylko przy tworzeniu bazy; użyj --reset)")

    if args.admin_username:
        try:
            create_admin(path, args.admin_username, args.admin_email, _read_password())
        except (sqlite3.IntegrityError, ValueError) as exc:
            print(f"Nie utworzono administratora: {exc}", file=sys.stderr)
            return 1
        print(f"Administrator '{args.admin_username}' utworzony.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
