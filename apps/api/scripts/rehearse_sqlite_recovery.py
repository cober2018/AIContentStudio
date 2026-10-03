"""Rehearse an isolated SQLite backup/restore without touching the source DB."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def _integrity(path: Path) -> str:
    with sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()
    return str(result[0]) if result else "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="source SQLite database; it is opened read-only")
    parser.add_argument("destination", type=Path, help="new isolated restored database")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    destination = args.destination.expanduser().resolve()
    if not source.is_file() or destination.exists() or source == destination:
        raise SystemExit("source must exist and destination must be a new path")
    destination.parent.mkdir(parents=True, exist_ok=True)

    with (sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True) as source_connection,
          sqlite3.connect(destination) as destination_connection):
        source_connection.backup(destination_connection)
        destination_connection.commit()

    source_integrity = _integrity(source)
    restored_integrity = _integrity(destination)
    print(json.dumps({
        "source": str(source),
        "destination": str(destination),
        "source_integrity": source_integrity,
        "restored_integrity": restored_integrity,
        "source_bytes": source.stat().st_size,
        "restored_bytes": destination.stat().st_size,
    }, ensure_ascii=False, sort_keys=True))
    return 0 if source_integrity == restored_integrity == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
