# 💬 Slack Bot Agent

Event-driven Slack bot with long-running memory on Dedalus Machines.

## What It Does

1. Listens to Slack events (mentions, DMs, channel messages)
2. Responds using LLM reasoning
3. **Persists conversation history** across sleep/wake
4. Schedules tasks (e.g., "remind me tomorrow")

## Persistence Demo

```bash
# Start the bot
python3 agent.py --start

# Chat with it in Slack
# @my-bot what's the weather?
# @my-bot remind me to check logs at 9am

# Stop machine overnight
dedalus machines stop dm-slack-01

# Wake in morning — bot remembers your conversation!
dedalus machines start dm-slack-01
# @my-bot what did we discuss yesterday?
```

Conversation history at `/home/machine/conversations.json` persists forever.
