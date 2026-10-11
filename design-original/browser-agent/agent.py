#!/usr/bin/env python3
"""
🌐 Browser Automation Agent for Dedalus Machines

Demonstrates Dedalus persistence by:
1. Opening a browser session
2. Logging into websites (cookies persist)
3. Saving browser state to persistent volume
4. Surviving sleep/wake — wake up still logged in!

This is the "aha moment" for browser automation use cases.
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Persistent storage
PERSIST_DIR = Path("/home/machine")
BROWSER_DATA_DIR = PERSIST_DIR / "browser_data"
SESSION_FILE = PERSIST_DIR / ".browser_session.json"
TASKS_FILE = PERSIST_DIR / ".browser_tasks.json"

BROWSER_DATA_DIR.mkdir(exist_ok=True)


def load_session():
    """Load browser session state from persistent volume."""
    if SESSION_FILE.exists():
        with open(SESSION_FILE) as f:
            return json.load(f)
    return {"cookies": [], "local_storage": {}, "last_url": None, "logged_in": False}


def save_session(session):
    """Save browser session — THE AHA MOMENT."""
    session["last_updated"] = datetime.now().isoformat()
    with open(SESSION_FILE, "w") as f:
        json.dump(session, f, indent=2)
    print(f"💾 Browser session persisted to {SESSION_FILE}")


def load_tasks():
    """Load scheduled tasks."""
    if TASKS_FILE.exists():
        with open(TASKS_FILE) as f:
            return json.load(f)
    return {"tasks": [], "completed": []}


def save_tasks(tasks):
    """Save tasks to persistent volume."""
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def simulate_login(url, username=None, password=None):
    """
    Simulates browser login (in production, uses Playwright/MCP).
    The key insight: after login, we save cookies to persistent storage.
    """
    print(f"🌐 Navigating to {url}")
    print(f"🔑 Logging in...")

    session = load_session()
    session["last_url"] = url
    session["logged_in"] = True
    session["cookies"] = [
        {"name": "session_id", "value": "abc123", "domain": ".example.com"},
        {"name": "auth_token", "value": "xyz789", "domain": ".example.com"}
    ]
    session["local_storage"] = {"user_prefs": "dark_mode", "last_visit": datetime.now().isoformat()}

    save_session(session)
    print(f"✅ Logged in! Session saved to persistent volume.")
    print(f"   🛌 Sleep the machine now. Wake in 50ms — still logged in.")
    return session


def simulate_scrape(url):
    """Scrape data using persisted session."""
    session = load_session()

    if not session["logged_in"]:
        print("⚠️  No active session. Run --task login first.")
        return

    print(f"🌐 Scraping {url}")
    print(f"📂 Using persisted cookies: {len(session['cookies'])} cookies loaded")

    # Simulated scrape
    data = {
        "url": url,
        "scraped_at": datetime.now().isoformat(),
        "data": {"title": "Dashboard", "items": ["item1", "item2", "item3"]},
        "session_used": True
    }

    output_file = PERSIST_DIR / f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Scraped data saved to {output_file}")
    return data


def run_browser_task(task, url, username=None, password=None):
    """Main browser automation loop."""
    print("\n" + "="*60)
    print(f"🌐 Browser Automation Agent — Dedalus Machines")
    print(f"🎯 Task: {task}")
    print(f"💾 Persistent storage: {PERSIST_DIR}")
    print("="*60 + "\n")

    session = load_session()
    print(f"📂 Browser state loaded:")
    print(f"   Logged in: {session['logged_in']}")
    print(f"   Cookies: {len(session['cookies'])}")
    print(f"   Last URL: {session['last_url']}")
    print(f"   Last updated: {session.get('last_updated', 'Never')}")
    print()

    if task == "login":
        simulate_login(url, username, password)
    elif task == "scrape":
        simulate_scrape(url)
    elif task == "status":
        print(f"Session status: {'✅ Active' if session['logged_in'] else '❌ No session'}")
    else:
        print(f"Unknown task: {task}")


def main():
    parser = argparse.ArgumentParser(description="Browser Automation Agent")
    parser.add_argument("--task", required=True, choices=["login", "scrape", "status"])
    parser.add_argument("--url", default="https://example.com")
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    args = parser.parse_args()

    run_browser_task(args.task, args.url, args.username, args.password)


if __name__ == "__main__":
    main()
