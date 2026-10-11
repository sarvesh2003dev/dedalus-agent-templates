#!/usr/bin/env python3
"""
🔬 Deep Research Agent for Dedalus Machines

This agent demonstrates Dedalus persistence by:
1. Running a research query
2. Saving structured notes to the persistent volume
3. Surviving sleep/wake cycles with all data intact

Built for Dedalus Labs — shows the "aha moment" of state persistence.
"""

import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Dedalus SDK
from dedalus_labs import Dedalus

# Persistent storage path (survives sleep/wake)
PERSIST_DIR = Path("/home/machine")
NOTES_FILE = PERSIST_DIR / "research_notes.json"
STATE_FILE = PERSIST_DIR / ".research_state.json"


def load_notes():
    """Load existing research notes from persistent volume."""
    if NOTES_FILE.exists():
        with open(NOTES_FILE) as f:
            return json.load(f)
    return {"queries": [], "findings": [], "pdfs_processed": [], "last_updated": None}


def save_notes(notes):
    """Save notes to persistent volume — THIS IS THE AHA MOMENT."""
    notes["last_updated"] = datetime.now().isoformat()
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)
    print(f"💾 Notes persisted to {NOTES_FILE}")


def load_state():
    """Load agent state (current query, progress, etc.)."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    """Save agent state — survives machine sleep."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def search_web(query):
    """
    Search the web using MCP web-search server.
    In production, this calls the MCP server. Here we simulate with requests.
    """
    print(f"🔍 Searching: {query}")
    # Simulated search results (in production, call MCP server)
    return [
        {"title": f"Result about {query}", "url": "https://example.com/1", "snippet": "..."},
        {"title": f"Another result for {query}", "url": "https://example.com/2", "snippet": "..."},
    ]


def process_findings(query, results):
    """Extract structured findings from search results."""
    findings = []
    for i, result in enumerate(results):
        findings.append({
            "id": f"finding_{int(time.time())}_{i}",
            "query": query,
            "title": result["title"],
            "url": result["url"],
            "summary": result["snippet"],
            "extracted_at": datetime.now().isoformat()
        })
    return findings


def run_research(query):
    """Main research loop with persistence."""
    print("\n" + "="*60)
    print(f"🔬 Deep Research Agent — Dedalus Machines")
    print(f"📝 Query: {query}")
    print(f"💾 Persistent storage: {PERSIST_DIR}")
    print("="*60 + "\n")

    # Load previous state (the magic of persistence!)
    notes = load_notes()
    state = load_state()

    print(f"📚 Loaded {len(notes['findings'])} previous findings from persistent storage")
    if notes['last_updated']:
        print(f"   Last updated: {notes['last_updated']}")

    # Update state
    state["current_query"] = query
    state["status"] = "researching"
    save_state(state)

    # Search
    results = search_web(query)
    print(f"\n📊 Found {len(results)} results")

    # Process
    new_findings = process_findings(query, results)
    notes["queries"].append({
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "results_count": len(results)
    })
    notes["findings"].extend(new_findings)

    # Save to persistent volume
    save_notes(notes)

    # Update state
    state["status"] = "completed"
    state["last_query_completed"] = datetime.now().isoformat()
    save_state(state)

    print("\n" + "="*60)
    print(f"✅ Research complete! Total findings: {len(notes['findings'])}")
    print(f"💾 All data persisted to {NOTES_FILE}")
    print(f"🛌 You can now sleep this machine. Wake it in 50ms and continue.")
    print("="*60 + "\n")

    return notes


def main():
    parser = argparse.ArgumentParser(description="Deep Research Agent for Dedalus Machines")
    parser.add_argument("--query", default="latest LLM advances", help="Research query")
    parser.add_argument("--list", action="store_true", help="List all persisted findings")
    args = parser.parse_args()

    if args.list:
        notes = load_notes()
        print(f"\n📚 Research History ({len(notes['findings'])} findings)")
        for q in notes["queries"]:
            print(f"   • {q['query']} ({q['results_count']} results)")
        return

    run_research(args.query)


if __name__ == "__main__":
    main()
