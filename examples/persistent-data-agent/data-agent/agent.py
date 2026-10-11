"""CSV and SQLite persistence worker. Uses only the Python standard library."""

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sqlite3
import sys
from pathlib import Path


def identifier(value):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", value):
        raise ValueError("Names must start with a letter and contain only letters, digits or _. ")
    if value.lower().startswith("sqlite_"):
        raise ValueError("Names beginning with sqlite_ are reserved.")
    return '"' + value + '"'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def infer_column(values):
    nonempty = [value for value in values if value != ""]
    if nonempty and all(re.fullmatch(r"-?(0|[1-9][0-9]*)", v) for v in nonempty):
        integers = [int(v) for v in nonempty]
        if all(-(2**63) <= v < 2**63 for v in integers):
            return "INTEGER", lambda v: int(v) if v else None
    try:
        if nonempty and all(math.isfinite(float(v)) for v in nonempty):
            return "REAL", lambda v: float(v) if v else None
    except ValueError:
        pass
    return "TEXT", lambda v: v if v else None


def load_csv(state_dir, csv_path, name, proof_token):
    table = identifier(name)
    raw = csv_path.read_bytes()
    if len(raw) > 10_000_000:
        raise ValueError("This starter limits CSV files to 10 MB.")
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
    if len(rows) < 2:
        raise ValueError("CSV must contain a header and at least one data row.")
    headers, records = rows[0], rows[1:]
    if len(headers) > 100 or len(records) > 100_000:
        raise ValueError("This starter supports at most 100 columns and 100,000 rows.")
    if len({h.lower() for h in headers}) != len(headers):
        raise ValueError("CSV headers must be unique, ignoring case.")
    for header in headers:
        identifier(header)
        if header.lower() in {"rowid", "oid", "_rowid_"}:
            raise ValueError("CSV headers may not shadow SQLite's row ID.")
    if any(len(row) != len(headers) for row in records):
        raise ValueError("A CSV row has a different number of fields than the header.")
    types = [infer_column([r[i] for r in records]) for i in range(len(headers))]
    converted = [tuple(types[i][1](v) for i, v in enumerate(row)) for row in records]
    state_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(state_dir / "datasets.sqlite3")
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("CREATE TABLE IF NOT EXISTS _datasets "
                               "(name TEXT PRIMARY KEY, source_sha256 TEXT NOT NULL, "
                               "proof_token TEXT NOT NULL, row_count INTEGER NOT NULL)")
            if connection.execute("SELECT 1 FROM _datasets WHERE name = ? COLLATE NOCASE",
                                  (name,)).fetchone():
                raise ValueError("Dataset already exists; choose a new name or state directory.")
            definitions = ", ".join(f"{identifier(h)} {t[0]}" for h, t in zip(headers, types))
            connection.execute(f"CREATE TABLE {table} ({definitions})")
            placeholders = ",".join("?" for _ in headers)
            connection.executemany(f"INSERT INTO {table} VALUES ({placeholders})", converted)
            connection.execute("INSERT INTO _datasets VALUES (?, ?, ?, ?)",
                               (name, digest(raw), proof_token, len(records)))
    finally:
        connection.close()
    return snapshot(state_dir, name)


def readonly_connection(state_dir):
    path = (state_dir / "datasets.sqlite3").resolve()
    if not path.is_file():
        raise ValueError("No saved database exists in this state directory.")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only = ON")
    return connection


def snapshot(state_dir, name):
    table = identifier(name)
    connection = readonly_connection(state_dir)
    try:
        if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ValueError("SQLite integrity check failed.")
        metadata = connection.execute("SELECT source_sha256, proof_token, row_count "
                                      "FROM _datasets WHERE name = ?", (name,)).fetchone()
        if metadata is None:
            raise ValueError("Dataset not found.")
        cursor = connection.execute(f"SELECT * FROM {table} ORDER BY rowid")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        if len(rows) != metadata[2]:
            raise ValueError("Saved row count does not match the database.")
    finally:
        connection.close()
    canonical = json.dumps({"columns": columns, "rows": rows}, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {
        "dataset": name,
        "row_count": len(rows),
        "columns": columns,
        "proof_token": metadata[1],
        "source_sha256": metadata[0],
        "rows_sha256": digest(canonical),
        "database_sha256": digest((state_dir / "datasets.sqlite3").read_bytes()),
    }


def query(state_dir, sql):
    connection = readonly_connection(state_dir)
    # Limit work and permit only read queries. There is no network-facing SQL API.
    permitted = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                 sqlite3.SQLITE_RECURSIVE}
    connection.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK
                              if action in permitted else sqlite3.SQLITE_DENY)
    ticks = 0

    def budget():
        nonlocal ticks
        ticks += 1
        return ticks > 1000

    connection.set_progress_handler(budget, 1000)
    try:
        cursor = connection.execute(sql)
        if cursor.description is None:
            raise ValueError("Query must return rows.")
        rows = cursor.fetchmany(1001)
        if len(rows) > 1000:
            raise ValueError("Query exceeds 1,000 rows; add a LIMIT or use an aggregate.")
        return {"columns": [c[0] for c in cursor.description], "rows": rows}
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    commands = parser.add_subparsers(dest="action", required=True)
    load = commands.add_parser("load")
    load.add_argument("--csv", type=Path, required=True)
    load.add_argument("--name", default="sales")
    load.add_argument("--proof-token", required=True)
    inspect = commands.add_parser("snapshot")
    inspect.add_argument("--name", default="sales")
    read = commands.add_parser("query")
    read.add_argument("--sql", required=True)
    args = parser.parse_args()
    try:
        if args.action == "load":
            result = load_csv(args.state_dir, args.csv, args.name, args.proof_token)
        elif args.action == "snapshot":
            result = snapshot(args.state_dir, args.name)
        else:
            result = query(args.state_dir, args.sql)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (OSError, ValueError, sqlite3.Error, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
