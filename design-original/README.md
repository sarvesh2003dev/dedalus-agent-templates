# 🪽 Dedalus Agent Templates

> **5 production-ready agent templates for Dedalus Machines** — the fastest persistent VMs for AI agents.
> 
> Built by [Sarvesh](https://github.com/sarvesh2003dev) as an onboarding accelerator concept for Dedalus Labs.

---

## 🎯 What Problem This Solves

Dedalus Machines are incredible: **<50ms wake times**, full Linux VMs, filesystem + memory persistence.

But getting started takes **30-60 minutes for teams**. The quickstart shows you how to create a VM and run a command. But it doesn't show you the **"aha moment"** — the 50ms wake with state persistence. That's the killer feature, and it's buried.

This repo fixes that.

| Asset | Why It Matters |
|-------|---------------|
| **5 Pre-Built Agents** | Go from "what do I build?" to "let me tweak this" in seconds |
| **One-Click Deploy** | `./deploy.sh --name my-agent` — that's it |
| **Persistence Demos** | Every agent proves state survives sleep/wake cycles |
| **MCP Pre-Configured** | No manual server setup. It just works |

---

## 🚀 Quick Start (3 Minutes)

```bash
# 1. Clone this repo
git clone https://github.com/sarvesh2003dev/dedalus-agent-templates.git
cd dedalus-agent-templates

# 2. Set your Dedalus API key
export DEDALUS_API_KEY="ddsk_your_key_here"

# 3. Pick an agent and deploy
./deploy.sh --template research-agent --name my-researcher
```

**That's it.** Your agent is running on a persistent VM. Sleep it. Wake it in 50ms. Your data is still there.

---

## 📦 The 5 Agents

### 1. 🔬 Deep Research Agent
Autonomous research with web search, PDF parsing, and structured note-taking.
- **MCP Servers**: `mcp-web-search`, `mcp-filesystem`
- **Persistence**: Research notes survive across sessions
- **Use case**: "Research the latest LLM papers and summarize findings daily"

```bash
./deploy.sh --template research-agent --name deep-researcher
```

### 2. 🌐 Browser Automation Agent
Playwright-powered browser agent that automates workflows.
- **MCP Servers**: `mcp-browser`, `mcp-filesystem`
- **Persistence**: Browser sessions (cookies, localStorage) survive sleep
- **Use case**: "Log into my dashboard every morning and export a CSV"

```bash
./deploy.sh --template browser-agent --name browser-bot
```

### 3. 💻 Code Execution Agent
Safe sandboxed code execution with dependency caching.
- **MCP Servers**: `mcp-code-runner`
- **Persistence**: Installed packages, virtualenvs, and code files persist
- **Use case**: "Run my data pipeline every hour, cache the results"

```bash
./deploy.sh --template code-agent --name code-runner
```

### 4. 📊 Data Analysis Agent
Pandas + SQL + visualization pipeline.
- **MCP Servers**: `mcp-sqlite`, `mcp-filesystem`
- **Persistence**: Datasets, query results, and generated charts persist
- **Use case**: "Analyze my sales CSV and generate a weekly report"

```bash
./deploy.sh --template data-agent --name data-analyst
```

### 5. 💬 Slack Bot Agent
Event-driven Slack bot with long-running memory.
- **MCP Servers**: `mcp-slack`, `mcp-filesystem`
- **Persistence**: Conversation history, scheduled tasks survive restarts
- **Use case**: "Slack bot that remembers context across days"

```bash
./deploy.sh --template slack-agent --name slack-assistant
```

---

## 🧠 How Persistence Works (The "Aha Moment")

Traditional cloud VMs:
1. Start VM → pull image → install deps → **2-5 minutes**
2. Stop VM → **everything lost**
3. Start again → **2-5 minutes again**

Dedalus Machines:
1. Create VM → **~30 seconds**
2. Install deps once → cached on persistent volume
3. Sleep VM → **billing pauses, state frozen**
4. Wake VM → **<50ms**, continue exactly where you left off

This repo demonstrates that in every agent. Run the persistence test:

```bash
./test-persistence.sh --agent research-agent
```

---

## 🏗️ Architecture

```
dedalus-agent-templates/
├── deploy.sh              # One-click deploy script
├── test-persistence.sh    # Proves state persistence
├── shared/
│   ├── dedalus_client.py  # Thin wrapper around dedalus-labs SDK
│   ├── mcp_config.yaml    # Pre-configured MCP server registry
│   └── setup_machine.sh   # Bootstraps any Dedalus Machine
├── research-agent/
│   ├── agent.py           # Main agent loop
│   ├── requirements.txt   # Python deps
│   ├── mcp_servers.json   # MCP server configs
│   └── README.md          # Agent-specific docs
├── browser-agent/
│   └── ...
├── code-agent/
│   └── ...
├── data-agent/
│   └── ...
└── slack-agent/
    └── ...
```

---

## 🔧 Prerequisites

- Python 3.9+
- Node.js 20+ (for TypeScript agents)
- A Dedalus API key — [get one here](https://www.dedaluslabs.ai/)
- (Optional) LLM API key for agent reasoning

---

## 🎓 For Beginners: How This All Works

> *"I want to learn like a beginner kid"* — okay, let's break it down.

### What is an "AI Agent"?

Think of it like a smart robot that can:
- **Think** using an LLM (like GPT-4, Claude)
- **Use tools** like a browser, calculator, or file system
- **Remember** what it did before
- **Run code** safely in a sandbox

### What is "Persistence"?

Imagine you write a long essay in Google Docs, close your laptop, open it tomorrow — your essay is still there. That's persistence.

Most AI sandboxes **don't** do this. Close the tab = everything gone.

Dedalus Machines **do** persist. Your agent can sleep for hours, days, weeks — wake up in 50ms, and remember everything.

### What is MCP?

MCP = Model Context Protocol. It's like USB for AI tools.

Instead of every tool needing custom integration, MCP is a standard. Any MCP-compatible tool plugs into any MCP-compatible agent. This repo pre-configures 5 MCP servers so you don't have to.

### What is a "Dedalus Machine"?

It's a tiny, fast Linux computer in the cloud. Specifically:
- A **microVM** (smaller, faster than Docker)
- Starts in **<50ms** (vs 2-5 minutes for traditional VMs)
- Your **files, memory, and installed programs survive** when it sleeps
- You only pay when it's **actually running**
- You get **root access** — full control

---

## 🧪 Testing Persistence

Each agent includes a persistence test. Here's what happens:

```bash
$ ./test-persistence.sh --agent research-agent

[1/5] Creating machine dm-test-01...
        ✓ Running (28s)

[2/5] Writing state: research_notes.json...
        ✓ Written to /home/machine/research_notes.json

[3/5] Installing dependency: beautifulsoup4...
        ✓ Installed (cached on persistent volume)

[4/5] Sleeping machine...
        ✓ Sleeping. Billing paused.

[5/5] Waking machine and reading state...
        ✓ Awake in 47ms!
        ✓ research_notes.json: FOUND
        ✓ beautifulsoup4: IMPORTABLE
        ✓ All state persisted!
```

---

## 📊 Why This Moves the Needle for Dedalus

| Metric | Before | After |
|--------|--------|-------|
| Time to first persistent VM | 30-60 min | **3 min** |
| Time to deploy an agent | Hours of setup | **One command** |
| User conversion from waitlist | Low (complexity barrier) | **High** (instant value) |
| Investor signal | Weak onboarding metrics | **Strong activation** |

---

## 🤝 Contributing

This is a concept demo built to show what's possible. If Dedalus Labs finds this valuable:

1. **Make it official** — fork this into `dedalus-labs/agent-templates`
2. **Add more agents** — community-contributed templates
3. **One-click dashboard** — integrate "Clone This Agent" into the Dedalus UI

---

## 📝 License

MIT — use it, fork it, ship it.

---

> *"Let us build your wings so your agents can fly."* 🪽
> 
> — Built with love for Dedalus Labs by Sarvesh
