# 💻 Code Execution Agent

Safe sandboxed code execution with dependency caching on Dedalus Machines.

## What It Does

1. Accepts Python/JavaScript code via API or file
2. Runs it in a sandboxed environment
3. **Caches installed packages** on the persistent volume
4. Survives sleep/wake — dependencies don't need reinstall

## Persistence Demo

```bash
# First run: installs numpy (takes ~30s)
python3 agent.py --file script.py

# Stop machine
dedalus machines stop dm-code-01

# Wake and run again: numpy is already installed!
dedalus machines start dm-code-01
python3 agent.py --file script.py
```

The virtualenv at `/home/machine/venv/` persists across sessions.
