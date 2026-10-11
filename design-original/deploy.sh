#!/bin/bash
set -e

# Dedalus Agent Templates — One-Click Deploy
# Usage: ./deploy.sh --template <name> --name <machine-name> [--api-key <key>]

TEMPLATE=""
NAME=""
API_KEY="${DEDALUS_API_KEY:-}"
VCPU="2"
MEMORY="4096"
STORAGE="10"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "Usage: ./deploy.sh --template <agent-type> --name <machine-name> [options]"
    echo ""
    echo "Agents:"
    echo "  research-agent     Deep Research Agent"
    echo "  browser-agent      Browser Automation Agent"
    echo "  code-agent         Code Execution Agent"
    echo "  data-agent         Data Analysis Agent"
    echo "  slack-agent        Slack Bot Agent"
    echo ""
    echo "Options:"
    echo "  --api-key KEY      Dedalus API key (or set DEDALUS_API_KEY env var)"
    echo "  --vcpu N           vCPU count (default: 2)"
    echo "  --memory N         Memory in MiB (default: 4096)"
    echo "  --storage N        Storage in GiB (default: 10)"
    echo "  --help             Show this help"
    exit 1
}

log() { echo -e "${BLUE}[dedalus-deploy]${NC} $1"; }
ok() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --template) TEMPLATE="$2"; shift 2 ;;
        --name) NAME="$2"; shift 2 ;;
        --api-key) API_KEY="$2"; shift 2 ;;
        --vcpu) VCPU="$2"; shift 2 ;;
        --memory) MEMORY="$2"; shift 2 ;;
        --storage) STORAGE="$2"; shift 2 ;;
        --help) usage ;;
        *) error "Unknown option: $1"; ;;
    esac
done

# Validate
[[ -z "$TEMPLATE" ]] && error "--template is required"
[[ -z "$NAME" ]] && error "--name is required"
[[ -z "$API_KEY" ]] && error "API key required. Use --api-key or set DEDALUS_API_KEY"
[[ -d "$TEMPLATE" ]] || error "Unknown template: $TEMPLATE"

log "Deploying $TEMPLATE as '$NAME'..."
log "Resources: ${VCPU} vCPU, ${MEMORY} MiB RAM, ${STORAGE} GiB storage"

# Check dependencies
command -v python3 >/dev/null 2>&1 || error "python3 is required"

# Install dedalus SDK if needed
python3 -c "import dedalus_labs" 2>/dev/null || {
    log "Installing dedalus-labs SDK..."
    pip install dedalus_labs -q
}

# Create machine via Python script
log "Creating Dedalus Machine..."
MACHINE_ID=$(python3 <<PYEOF
import os
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
client = Dedalus()
machine = client.machines.create(
    name="$NAME",
    vcpu=$VCPU,
    memory_mib=$MEMORY,
    storage_gib=$STORAGE
)
print(machine.id)
PYEOF
)

ok "Machine created: $MACHINE_ID"

# Wait for running
log "Waiting for machine to start..."
python3 <<PYEOF
import os, time
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
client = Dedalus()
mid = "$MACHINE_ID"
for i in range(60):
    m = client.machines.retrieve(mid)
    if m.phase == "running":
        print(f"Machine running after {i*2}s")
        break
    time.sleep(2)
else:
    print("Timeout waiting for machine")
    exit(1)
PYEOF

# Upload agent files
log "Uploading agent files..."
python3 <<PYEOF
import os
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
import tarfile, io

client = Dedalus()
mid = "$MACHINE_ID"

# Create tarball of agent files
agent_dir = "$TEMPLATE"
tar_buffer = io.BytesIO()
with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
    tar.add(agent_dir, arcname="agent")
tar_bytes = tar_buffer.getvalue()

# Upload and extract
client.machines.exec_create(
    machine_id=mid,
    command=["bash", "-c", "mkdir -p /home/machine/agent && cd /home/machine/agent && tar xzf -"],
    stdin=tar_bytes
)
PYEOF

ok "Agent files uploaded to /home/machine/agent"

# Install dependencies
log "Installing dependencies..."
python3 <<PYEOF
import os
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
client = Dedalus()
mid = "$MACHINE_ID"

# Check for requirements.txt or package.json
result = client.machines.exec_create(
    machine_id=mid,
    command=["bash", "-c", "cd /home/machine/agent && if [ -f requirements.txt ]; then pip install -r requirements.txt; elif [ -f package.json ]; then npm install; fi"]
)
print(result.stdout.decode() if hasattr(result, 'stdout') else "Dependencies installed")
PYEOF

ok "Dependencies installed"

# Start agent
log "Starting agent..."
python3 <<PYEOF
import os
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
client = Dedalus()
mid = "$MACHINE_ID"

# Start agent in background
client.machines.exec_create(
    machine_id=mid,
    command=["bash", "-c", "cd /home/machine/agent && nohup python3 agent.py > /home/machine/agent.log 2>&1 &"]
)
PYEOF

ok "Agent started!"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🚀 Agent deployed successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "  Machine ID:  $MACHINE_ID"
echo "  Name:        $NAME"
echo "  Status:      Running"
echo "  Agent Dir:   /home/machine/agent"
echo "  Logs:        /home/machine/agent.log"
echo ""
echo "  Commands:"
echo "    dedalus machines exec $MACHINE_ID -- bash"
echo "    dedalus machines stop $MACHINE_ID"
echo "    dedalus machines start $MACHINE_ID"
echo ""
echo -e "  ${YELLOW}Try the persistence test:${NC}"
echo "    ./test-persistence.sh --agent $TEMPLATE --machine $MACHINE_ID"
echo ""
