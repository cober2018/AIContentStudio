"""Copy and verify every referenced local byte before a future storage cutover.

This rehearsal is read-only against the SQLite source and never changes the
database. The destination must be new; a later operator-controlled cutover
would need to apply the emitted legacy-key mappings transactionally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path


def _rows(connection: sqlite3.Connection, table: str) -> list[tuple[str | None, str | None, str]]:
    columns = "file_path, content_hash" if table != "asset_media" else "file_path, NULL"
    query = f"SELECT {columns}, '{table}' FROM {table} WHERE file_path IS NOT NULL"
    try:
        return list(connection.execute(query))
    except sqlite3.OperationalError:
        return []


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="source SQLite database; opened read-only")
    parser.add_argument("source_root", type=Path, help="current local material/media root")
    parser.add_argument("destination_root", type=Path, help="new isolated cutover rehearsal root")
    args = parser.parse_args()
    database = args.database.expanduser().resolve()
    source_root = args.source_root.expanduser().resolve()
    destination_root = args.destination_root.expanduser().resolve()
    if not database.is_file() or not source_root.is_dir() or destination_root.exists() or database == destination_root:
        raise SystemExit("database/source_root must exist and destination_root must be new")

    references: dict[str, dict] = {}
    with sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True) as connection:
        for table in ("material_revision", "draft_media", "asset_media"):
            for raw_key, expected_hash, owner in _rows(connection, table):
                if not raw_key:
                    continue
                path = Path(raw_key).expanduser()
                source = path if path.is_absolute() else source_root / path
                if path.is_absolute():
                    logical_key = f"legacy/{expected_hash or 'unresolved'}{path.suffix.lower()}"
                else:
                    logical_key = path.as_posix()
                entry = references.setdefault(logical_key, {"rows": [], "owners": []})
                entry["rows"].append((source, expected_hash))
                entry["owners"].append(owner)

    failures: list[dict] = []
    copied = 0
    verified_rows = 0
    for logical_key, entry in references.items():
        validated = []
        for source, expected_hash in entry["rows"]:
            if not source.is_file():
                failures.append({"key": logical_key, "code": "missing_source_bytes", "owners": entry["owners"]})
                continue
            actual_hash = _digest(source)
            if expected_hash and actual_hash != expected_hash:
                failures.append({"key": logical_key, "code": "source_hash_mismatch", "owners": entry["owners"]})
                continue
            validated.append((source, actual_hash))
            verified_rows += 1
        # Copy deduplication must not hide a revision with different expected bytes.
        if len(validated) != len(entry["rows"]):
            continue
        if len({digest for _, digest in validated}) != 1:
            failures.append({"key": logical_key, "code": "source_key_collision", "owners": entry["owners"]})
            continue
        source, actual_hash = validated[0]
        if logical_key.startswith("legacy/unresolved"):
            logical_key = f"legacy/{actual_hash}{source.suffix.lower()}"
        target = destination_root / logical_key
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if _digest(target) != actual_hash:
            failures.append({"key": logical_key, "code": "destination_hash_mismatch", "owners": entry["owners"]})
            continue
        copied += 1

    result = {
        "database": str(database),
        "source_root": str(source_root),
        "destination_root": str(destination_root),
        "referenced_keys": len(references),
        "referenced_rows": sum(len(entry["rows"]) for entry in references.values()),
        "verified_rows": verified_rows,
        "copied_and_verified": copied,
        "failure_count": len(failures),
        "failures": failures,
        "ready_for_operator_cutover": bool(references) and not failures,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
