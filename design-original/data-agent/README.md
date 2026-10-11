# 📊 Data Analysis Agent

Pandas + SQL + visualization pipeline on Dedalus Machines.

## What It Does

1. Loads CSV/JSON/Parquet datasets
2. Runs SQL queries via SQLite
3. Generates matplotlib/seaborn visualizations
4. **Persists datasets, query results, and charts** across sessions

## Persistence Demo

```bash
# Upload a large CSV (only once)
python3 agent.py --load data/sales.csv --name sales

# Run analysis
python3 agent.py --query "SELECT * FROM sales WHERE revenue > 10000"

# Stop machine (dataset stays!)
dedalus machines stop dm-data-01

# Wake next week — dataset is still there
dedalus machines start dm-data-01
python3 agent.py --query "SELECT SUM(revenue) FROM sales"
```

Datasets cached at `/home/machine/datasets/`. No re-upload needed.
