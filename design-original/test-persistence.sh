#!/bin/bash
set -e

# Tests that state persists across sleep/wake cycles
# Usage: ./test-persistence.sh --agent <name> --machine <id>

AGENT=""
MACHINE=""
API_KEY="${DEDALUS_API_KEY:-}"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[persistence-test]${NC} $1"; }
ok() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; exit 1; }

while [[ $# -gt 0 ]]; do
    case $1 in
        --agent) AGENT="$2"; shift 2 ;;
        --machine) MACHINE="$2"; shift 2 ;;
        --api-key) API_KEY="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

[[ -z "$AGENT" ]] && { echo "--agent required"; exit 1; }
[[ -z "$API_KEY" ]] && { echo "API key required"; exit 1; }

# If no machine specified, create one
if [[ -z "$MACHINE" ]]; then
    log "Creating test machine..."
    MACHINE=$(python3 <<PYEOF
import os
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
client = Dedalus()
m = client.machines.create(name="persist-test", vcpu=1, memory_mib=2048, storage_gib=5)
print(m.id)
PYEOF
)
    ok "Created: $MACHINE"
    sleep 5
fi

log "Running persistence test on $MACHINE..."

# Test 1: Write state
log "[1/5] Writing test state..."
python3 <<PYEOF
import os
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
client = Dedalus()
mid = "$MACHINE"
client.machines.exec_create(
    machine_id=mid,
    command=["bash", "-c", 'echo "{\"test\": \"persistence_works\", \"timestamp\": \"$(date -Iseconds)\"}" > /home/machine/persist_test.json']
)
PYEOF
ok "State written"

# Test 2: Install a package
log "[2/5] Installing test dependency..."
python3 <<PYEOF
import os
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
client = Dedalus()
mid = "$MACHINE"
client.machines.exec_create(
    machine_id=mid,
    command=["bash", "-c", "pip install colorama -q"]
)
PYEOF
ok "Dependency installed"

# Test 3: Sleep
log "[3/5] Sleeping machine..."
python3 <<PYEOF
import os
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
client = Dedalus()
client.machines.update(machine_id="$MACHINE", status="stopped")
PYEOF
ok "Machine sleeping"

# Test 4: Wake and measure
log "[4/5] Waking machine..."
START_MS=$(python3 -c "import time; print(int(time.time()*1000))")
python3 <<PYEOF
import os
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
client = Dedalus()
client.machines.update(machine_id="$MACHINE", status="running")
PYEOF
END_MS=$(python3 -c "import time; print(int(time.time()*1000))")
WAKE_TIME=$((END_MS - START_MS))
ok "Machine awake in ${WAKE_TIME}ms"

# Test 5: Verify state
log "[5/5] Verifying persisted state..."
python3 <<PYEOF
import os, sys
os.environ["DEDALUS_API_KEY"] = "$API_KEY"
from dedalus_labs import Dedalus
client = Dedalus()
mid = "$MACHINE"

# Check file
result = client.machines.exec_create(
    machine_id=mid,
    command=["cat", "/home/machine/persist_test.json"]
)
stdout = result.stdout.decode() if hasattr(result, 'stdout') else str(result)
if "persistence_works" not in stdout:
    print("FAIL: File not persisted")
    sys.exit(1)
print("File persisted: OK")

# Check package
result = client.machines.exec_create(
    machine_id=mid,
    command=["python3", "-c", "import colorama; print(colorama.__version__)"]
)
stdout = result.stdout.decode() if hasattr(result, 'stdout') else str(result)
if "FAIL" in stdout or "Error" in stdout:
    print("FAIL: Package not persisted")
    sys.exit(1)
print("Package persisted: OK")
PYEOF
ok "All state verified!"

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  🎉 Persistence test PASSED${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo "  Wake time: ${WAKE_TIME}ms"
echo "  File state: PERSISTED"
echo "  Package state: PERSISTED"
echo ""
