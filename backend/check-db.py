from app.core.config import get_settings
from app.db.connection import connect

conn = connect(get_settings().db_path, "owner")


def names(kind: str) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = ? AND name NOT LIKE 'sqlite_%' ORDER BY name",
        (kind,),
    )
    return [r[0] for r in rows]


for kind, expected in [("table", 10), ("index", 8), ("trigger", 15), ("view", 7)]:
    found = names(kind)
    status = "OK" if len(found) == expected else f"UWAGA (oczekiwano {expected})"
    print(f"{kind:8} {len(found):3}  {status}")

print("user_version:   ", conn.execute("PRAGMA user_version").fetchone()[0], "(oczekiwano 1)")
print("integrity_check:", conn.execute("PRAGMA integrity_check").fetchone()[0])
print("foreign_key_check:", conn.execute("PRAGMA foreign_key_check").fetchall() or "OK")
print("journal_mode:   ", conn.execute("PRAGMA journal_mode").fetchone()[0], "(oczekiwano wal)")

# widoki wykonują się poprawnie (łapie literówki w nazwach kolumn)
for v in names("view"):
    conn.execute(f"SELECT * FROM {v} LIMIT 1").fetchall()
print("widoki: OK")
