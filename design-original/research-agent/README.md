# 🔬 Deep Research Agent

Autonomous research agent with web search, PDF parsing, and structured note-taking.

## What It Does

1. Takes a research query (e.g., "latest advances in LLM reasoning")
2. Searches the web using MCP web-search server
3. Downloads and parses PDFs
4. Extracts key findings into structured JSON
5. **Persists everything** to `/home/machine/research_notes.json`

## Persistence Demo

```bash
# Start the agent
python3 agent.py --query "LLM reasoning benchmarks 2026"

# Stop the machine (simulating end of workday)
dedalus machines stop dm-research-01

# Next morning, wake it up
dedalus machines start dm-research-01

# Your notes are still there!
cat /home/machine/research_notes.json
```

## Files

- `agent.py` — Main research loop
- `requirements.txt` — Python dependencies
- `mcp_servers.json` — MCP server configuration
