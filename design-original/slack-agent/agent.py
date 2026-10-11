#!/usr/bin/env python3
"""
💬 Slack Bot Agent for Dedalus Machines

Demonstrates Dedalus persistence by:
1. Maintaining conversation history across sessions
2. Scheduling tasks that survive sleep/wake
3. Remembering user preferences and context
4. Waking in 50ms when a Slack event arrives

The "aha moment": Your bot remembers yesterday's conversation
even though the machine was sleeping all night.
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

PERSIST_DIR = Path("/home/machine")
CONVERSATIONS_FILE = PERSIST_DIR / "conversations.json"
TASKS_FILE = PERSIST_DIR / ".scheduled_tasks.json"
BOT_STATE_FILE = PERSIST_DIR / ".bot_state.json"


def load_conversations():
    """Load conversation history from persistent volume."""
    if CONVERSATIONS_FILE.exists():
        with open(CONVERSATIONS_FILE) as f:
            return json.load(f)
    return {"channels": {}, "dms": {}, "total_messages": 0}


def save_conversations(conversations):
    """Save conversations — THE AHA MOMENT."""
    conversations["last_updated"] = datetime.now().isoformat()
    with open(CONVERSATIONS_FILE, "w") as f:
        json.dump(conversations, f, indent=2)
    print(f"💾 Conversations persisted to {CONVERSATIONS_FILE}")


def load_tasks():
    """Load scheduled tasks."""
    if TASKS_FILE.exists():
        with open(TASKS_FILE) as f:
            return json.load(f)
    return {"tasks": [], "completed": []}


def save_tasks(tasks):
    """Save tasks to persistent storage."""
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def load_bot_state():
    """Load bot state (online status, config)."""
    if BOT_STATE_FILE.exists():
        with open(BOT_STATE_FILE) as f:
            return json.load(f)
    return {"status": "offline", "started_at": None, "total_interactions": 0}


def save_bot_state(state):
    """Save bot state."""
    with open(BOT_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def simulate_message(user, text, channel="general"):
    """Simulate receiving a Slack message."""
    conversations = load_conversations()

    # Record message
    msg = {
        "user": user,
        "text": text,
        "timestamp": datetime.now().isoformat(),
        "channel": channel
    }

    if channel not in conversations["channels"]:
        conversations["channels"][channel] = []
    conversations["channels"][channel].append(msg)
    conversations["total_messages"] += 1

    # Generate response
    response = generate_response(text, user, conversations)

    # Record response
    response_msg = {
        "user": "bot",
        "text": response,
        "timestamp": datetime.now().isoformat(),
        "channel": channel
    }
    conversations["channels"][channel].append(response_msg)

    save_conversations(conversations)

    # Update bot state
    state = load_bot_state()
    state["total_interactions"] += 1
    save_bot_state(state)

    return response


def generate_response(text, user, conversations):
    """Generate a response based on message and history."""
    text_lower = text.lower()

    # Check for memory/recall queries
    if "remember" in text_lower or "discuss" in text_lower or "yesterday" in text_lower:
        history = conversations["channels"].get("general", [])
        if len(history) > 2:
            last_topic = history[-3]["text"] if len(history) >= 3 else history[0]["text"]
            return f"""🧠 Yes! I remember our conversation. 

Last time we discussed: *"{last_topic}"*

This conversation is persisted on my Dedalus Machine at `{CONVERSATIONS_FILE}`.
Even if I sleep for days, I'll remember this when I wake up in 50ms! 🪽"""

    if "remind" in text_lower:
        return f"""⏰ Got it! I'll remind you. 

Your scheduled tasks are persisted at `{TASKS_FILE}`.
Even if this machine sleeps, your reminders survive."""

    if "hello" in text_lower or "hi" in text_lower:
        return f"""👋 Hello {user}! I'm running on a Dedalus Machine.

💾 My memory is persisted to disk, so I remember everything across sessions.
🛌 Sleep this machine. Wake it in 50ms. I'll still know who you are!"""

    return f"""🤖 I received: "{text}"

I'm a stateful agent running on Dedalus Machines. My conversation history is persisted at:
`{CONVERSATIONS_FILE}`

Try asking me if I remember our conversation!"""


def schedule_task(user, task, when):
    """Schedule a task that persists across sessions."""
    tasks = load_tasks()
    tasks["tasks"].append({
        "user": user,
        "task": task,
        "scheduled_for": when,
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    })
    save_tasks(tasks)
    return f"⏰ Task scheduled for {when}. It will persist even if I sleep!"


def show_status():
    """Show bot status and persistence info."""
    state = load_bot_state()
    conversations = load_conversations()
    tasks = load_tasks()

    print("\n" + "="*60)
    print(f"💬 Slack Bot Agent — Dedalus Machines")
    print("="*60)
    print(f"\n🤖 Bot Status:")
    print(f"   Status: {state['status']}")
    print(f"   Started: {state.get('started_at', 'Never')}")
    print(f"   Total interactions: {state['total_interactions']}")
    print(f"\n💾 Persistent Storage:")
    print(f"   Conversations: {CONVERSATIONS_FILE} ({conversations['total_messages']} messages)")
    print(f"   Tasks: {TASKS_FILE} ({len(tasks['tasks'])} pending)")
    print(f"   State: {BOT_STATE_FILE}")
    print(f"\n🛌 Persistence Demo:")
    print(f"   1. Stop this machine: dedalus machines stop <id>")
    print(f"   2. Wait any amount of time")
    print(f"   3. Start it: dedalus machines start <id>")
    print(f"   4. All data is still here! Wake time: <50ms")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Slack Bot Agent")
    parser.add_argument("--start", action="store_true", help="Start the bot")
    parser.add_argument("--message", help="Simulate a message")
    parser.add_argument("--user", default="user", help="Username")
    parser.add_argument("--channel", default="general", help="Channel")
    parser.add_argument("--schedule", help="Schedule a task")
    parser.add_argument("--when", default="tomorrow", help="When to schedule")
    parser.add_argument("--status", action="store_true", help="Show bot status")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.start:
        state = load_bot_state()
        state["status"] = "online"
        state["started_at"] = datetime.now().isoformat()
        save_bot_state(state)
        print("🚀 Bot started! Conversation history will persist across sessions.")
        print(f"   Storage: {CONVERSATIONS_FILE}")
    elif args.message:
        response = simulate_message(args.user, args.message, args.channel)
        print(f"\n💬 {args.user}: {args.message}")
        print(f"🤖 Bot: {response}")
    elif args.schedule:
        result = schedule_task(args.user, args.schedule, args.when)
        print(result)
    else:
        show_status()


if __name__ == "__main__":
    main()
