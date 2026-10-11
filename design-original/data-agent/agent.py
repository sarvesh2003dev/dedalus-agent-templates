#!/usr/bin/env python3
"""
📊 Data Analysis Agent for Dedalus Machines

Demonstrates Dedalus persistence by:
1. Loading datasets into persistent storage
2. Running SQL queries with cached results
3. Generating charts that survive sleep/wake
4. Building up analysis state over time

The "aha moment": Upload a 1GB dataset once. Query it for weeks.
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

PERSIST_DIR = Path("/home/machine")
DATASETS_DIR = PERSIST_DIR / "datasets"
QUERIES_FILE = PERSIST_DIR / ".queries.json"
CHARTS_DIR = PERSIST_DIR / "charts"

DATASETS_DIR.mkdir(exist_ok=True)
CHARTS_DIR.mkdir(exist_ok=True)


def load_queries():
    """Load query history from persistent storage."""
    if QUERIES_FILE.exists():
        with open(QUERIES_FILE) as f:
            return json.load(f)
    return {"queries": [], "datasets": []}


def save_queries(queries):
    """Save queries — survives sleep/wake."""
    with open(QUERIES_FILE, "w") as f:
        json.dump(queries, f, indent=2)


def load_dataset(name):
    """Load a dataset from persistent storage."""
    dataset_path = DATASETS_DIR / f"{name}.json"
    if dataset_path.exists():
        with open(dataset_path) as f:
            return json.load(f)
    return None


def save_dataset(name, data):
    """Save dataset to persistent volume."""
    dataset_path = DATASETS_DIR / f"{name}.json"
    with open(dataset_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Dataset '{name}' persisted to {dataset_path}")


def simulate_query(dataset_name, sql):
    """Simulate a SQL query (in production, uses MCP SQLite server)."""
    print(f"\n🔍 Querying dataset: {dataset_name}")
    print(f"   SQL: {sql}")

    dataset = load_dataset(dataset_name)
    if not dataset:
        print(f"❌ Dataset '{dataset_name}' not found. Use --load first.")
        return None

    # Simulated query result
    result = {
        "query": sql,
        "dataset": dataset_name,
        "row_count": 42,
        "columns": ["date", "revenue", "region"],
        "sample": [
            {"date": "2026-01-01", "revenue": 15000, "region": "US"},
            {"date": "2026-01-02", "revenue": 23000, "region": "EU"},
        ],
        "executed_at": datetime.now().isoformat()
    }

    # Save result
    result_file = PERSIST_DIR / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)

    # Record query
    queries = load_queries()
    queries["queries"].append({
        "sql": sql,
        "dataset": dataset_name,
        "result_file": str(result_file),
        "executed_at": datetime.now().isoformat()
    })
    save_queries(queries)

    print(f"✅ Query complete. {result['row_count']} rows returned.")
    print(f"💾 Result saved to {result_file}")
    return result


def simulate_load(filepath, name):
    """Simulate loading a dataset (in production, reads CSV/Parquet)."""
    print(f"\n📂 Loading dataset from {filepath}...")

    # Simulated dataset
    data = {
        "name": name,
        "source": filepath,
        "rows": 10000,
        "columns": ["date", "revenue", "region", "product"],
        "loaded_at": datetime.now().isoformat()
    }

    save_dataset(name, data)

    queries = load_queries()
    queries["datasets"].append({
        "name": name,
        "source": filepath,
        "rows": data["rows"],
        "loaded_at": data["loaded_at"]
    })
    save_queries(queries)

    print(f"✅ Dataset loaded: {data['rows']} rows, {len(data['columns'])} columns")
    return data


def simulate_chart(dataset_name, chart_type="bar"):
    """Simulate chart generation."""
    print(f"\n📊 Generating {chart_type} chart for {dataset_name}...")

    chart_file = CHARTS_DIR / f"{dataset_name}_{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    # In production, this would use matplotlib/seaborn
    with open(chart_file, "wb") as f:
        f.write(b"PNG_SIMULATED_CHART_DATA")

    print(f"✅ Chart saved to {chart_file}")
    print(f"💾 Chart persists across sleep/wake cycles!")
    return str(chart_file)


def main():
    parser = argparse.ArgumentParser(description="Data Analysis Agent")
    parser.add_argument("--load", help="Load a dataset file")
    parser.add_argument("--name", help="Dataset name")
    parser.add_argument("--query", help="SQL query to run")
    parser.add_argument("--chart", help="Generate chart for dataset")
    parser.add_argument("--type", default="bar", help="Chart type")
    parser.add_argument("--history", action="store_true", help="Show query history")
    args = parser.parse_args()

    print("\n" + "="*60)
    print(f"📊 Data Analysis Agent — Dedalus Machines")
    print(f"💾 Datasets: {DATASETS_DIR}")
    print(f"📊 Charts: {CHARTS_DIR}")
    print("="*60 + "\n")

    queries = load_queries()
    print(f"📚 Loaded {len(queries['datasets'])} datasets, {len(queries['queries'])} queries")
    print()

    if args.load and args.name:
        simulate_load(args.load, args.name)
    elif args.query and args.name:
        simulate_query(args.name, args.query)
    elif args.chart:
        simulate_chart(args.chart, args.type)
    elif args.history:
        print("\n📜 Query History:")
        for q in queries["queries"]:
            print(f"   • {q['sql']} on {q['dataset']} ({q['executed_at']})")
        print(f"\n📂 Datasets:")
        for d in queries["datasets"]:
            print(f"   • {d['name']}: {d['rows']} rows from {d['source']}")
    else:
        print("Use --load, --query, --chart, or --history")


if __name__ == "__main__":
    main()
