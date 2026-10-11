#!/usr/bin/env python3
"""
💻 Code Execution Agent for Dedalus Machines

Demonstrates Dedalus persistence by:
1. Creating a virtualenv on the persistent volume
2. Installing packages (cached forever)
3. Running user code safely
4. Surviving sleep/wake — venv and packages persist

The "aha moment": Install numpy once. Use it forever.
"""

import os
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

PERSIST_DIR = Path("/home/machine")
VENV_DIR = PERSIST_DIR / "venv"
SANDBOX_DIR = PERSIST_DIR / "sandbox"
HISTORY_FILE = PERSIST_DIR / ".code_history.json"

VENV_DIR.mkdir(exist_ok=True)
SANDBOX_DIR.mkdir(exist_ok=True)


def ensure_venv():
    """Create virtualenv on persistent volume if it doesn't exist."""
    python_path = VENV_DIR / "bin" / "python3"
    if not python_path.exists():
        print("📦 Creating virtualenv on persistent volume...")
        subprocess.run(["python3", "-m", "venv", str(VENV_DIR)], check=True)
        print(f"✅ Virtualenv created at {VENV_DIR}")
    return str(python_path)


def install_package(package):
    """Install a package into the persistent virtualenv."""
    python = ensure_venv()
    print(f"📦 Installing {package}...")
    subprocess.run([python, "-m", "pip", "install", package, "-q"], check=True)
    print(f"✅ {package} installed (persisted in {VENV_DIR})")

    # Record in history
    history = load_history()
    history["packages"].append({
        "package": package,
        "installed_at": datetime.now().isoformat()
    })
    save_history(history)


def load_history():
    """Load execution history from persistent storage."""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {"runs": [], "packages": [], "created_at": datetime.now().isoformat()}


def save_history(history):
    """Save execution history — survives sleep/wake."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def run_code(code_str, filename="<inline>"):
    """Run Python code in the persistent virtualenv."""
    python = ensure_venv()

    print(f"\n🚀 Running code from {filename}")
    print("-" * 40)

    # Write code to sandbox
    code_file = SANDBOX_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    with open(code_file, "w") as f:
        f.write(code_str)

    # Execute
    result = subprocess.run(
        [python, str(code_file)],
        capture_output=True,
        text=True,
        cwd=str(SANDBOX_DIR)
    )

    print(result.stdout)
    if result.stderr:
        print(f"⚠️  stderr: {result.stderr}")
    print("-" * 40)

    # Record
    history = load_history()
    history["runs"].append({
        "filename": filename,
        "code_file": str(code_file),
        "ran_at": datetime.now().isoformat(),
        "success": result.returncode == 0
    })
    save_history(history)

    print(f"✅ Execution complete. History persisted to {HISTORY_FILE}")
    return result


def run_file(filepath):
    """Run a Python file."""
    with open(filepath) as f:
        code = f.read()
    return run_code(code, filepath)


def main():
    parser = argparse.ArgumentParser(description="Code Execution Agent")
    parser.add_argument("--file", help="Python file to execute")
    parser.add_argument("--code", help="Inline Python code")
    parser.add_argument("--install", help="Install a package")
    parser.add_argument("--history", action="store_true", help="Show execution history")
    args = parser.parse_args()

    print("\n" + "="*60)
    print(f"💻 Code Execution Agent — Dedalus Machines")
    print(f"💾 Persistent venv: {VENV_DIR}")
    print(f"📂 Sandbox: {SANDBOX_DIR}")
    print("="*60 + "\n")

    # Show current state
    history = load_history()
    print(f"📚 History: {len(history['runs'])} runs, {len(history['packages'])} packages installed")
    print(f"   Created: {history['created_at']}")
    print()

    if args.install:
        install_package(args.install)
    elif args.file:
        run_file(args.file)
    elif args.code:
        run_code(args.code)
    elif args.history:
        print("\n📜 Execution History:")
        for run in history["runs"]:
            status = "✅" if run["success"] else "❌"
            print(f"   {status} {run['filename']} at {run['ran_at']}")
        print(f"\n📦 Installed Packages:")
        for pkg in history["packages"]:
            print(f"   • {pkg['package']} ({pkg['installed_at']})")
    else:
        print("Use --file, --code, --install, or --history")


if __name__ == "__main__":
    main()
