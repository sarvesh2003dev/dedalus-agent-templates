# Contributing to Dedalus Agent Templates

## Adding a New Agent Template

1. Create a new directory: `your-agent/`
2. Required files:
   - `agent.py` — Main agent logic
   - `requirements.txt` — Python dependencies
   - `mcp_servers.json` — MCP server configuration
   - `README.md` — Agent-specific documentation
3. Follow the persistence pattern:
   - Use `/home/machine/` for all persistent storage
   - Save state before sleeping
   - Load state on wake
4. Test with `./test-persistence.sh --agent your-agent`
5. Update the main README.md

## Code Style

- Black formatter (line length 100)
- Type hints where possible
- Docstrings for all public functions
