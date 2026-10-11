# 🌐 Browser Automation Agent

Playwright-powered browser agent that automates web workflows.

## What It Does

1. Connects to a headless browser via Playwright
2. Navigates websites, fills forms, clicks buttons
3. **Persists browser state** (cookies, localStorage, session) across sleep/wake
4. Runs scheduled tasks (e.g., "check dashboard every morning")

## Persistence Demo

```bash
# Log into a website
python3 agent.py --task "login" --url "https://example.com"

# Stop the machine
dedalus machines stop dm-browser-01

# Wake next day — still logged in!
dedalus machines start dm-browser-01
python3 agent.py --task "scrape" --url "https://example.com/dashboard"
```

The browser session (cookies, localStorage) is preserved because
`/home/machine/browser_data/` lives on the persistent volume.
