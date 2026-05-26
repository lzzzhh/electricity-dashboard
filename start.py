#!/usr/bin/env python3
"""Electricity Dashboard — One-command launcher (cross-platform)

Prerequisites (auto-checked, with install links if missing):
  - Python 3.10+
  - Node.js 18+ (for React frontend)
  - Mosquitto 2+ (optional, dashboard works without it)
"""

import os, sys, subprocess, time, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON_MIN  = (3, 10)
NODE_MIN    = (18,)


def which(cmd):
    """Find command in PATH, with Windows fallback (npm → npm.cmd)."""
    path = shutil.which(cmd)
    if not path and sys.platform == "win32" and not cmd.endswith(".cmd"):
        path = shutil.which(cmd + ".cmd")
    return path


def check_python():
    """Check Python version >= 3.10."""
    v = sys.version_info[:2]
    ok = v >= PYTHON_MIN
    tag = "OK" if ok else f"NEED {PYTHON_MIN[0]}.{PYTHON_MIN[1]}+"
    print(f"  Python {v[0]}.{v[1]}  [{tag}]")
    if not ok:
        print("  → Download: https://python.org/downloads/")
    return ok


def check_node():
    """Check Node.js and npm versions."""
    node = which("node")
    version = None
    if node:
        try:
            r = subprocess.run([node, "-v"], capture_output=True, text=True, timeout=5)
            version = r.stdout.strip().lstrip("v")
            parts = tuple(int(x) for x in version.split(".")[:2])
            ok = parts >= NODE_MIN
        except Exception:
            ok = False
            version = "unknown"
    else:
        version = "not found"
        ok = False

    tag = f"OK (v{version})" if ok else f"NEED v{NODE_MIN[0]}+ (found: {version})"
    print(f"  Node.js  [{tag}]")
    if not ok:
        print("  → Download: https://nodejs.org/en/download")
    return ok and node is not None


def check_mosquitto():
    """Check Mosquitto."""
    mosq = which("mosquitto")
    if mosq:
        print(f"  Mosquitto  [OK]")
    else:
        print(f"  Mosquitto  [NOT FOUND — dashboard uses pre-loaded data]")
    return mosq is not None


def main():
    print("=" * 50)
    print("  Electricity Dashboard — COMP5339 Assignment 2")
    print("=" * 50)

    is_windows = sys.platform == "win32"
    frontend = ROOT / "frontend"

    # ── Prerequisite checks ──
    print("\n▶ Checking prerequisites...")
    py_ok  = check_python()
    node_ok = check_node()
    mosq_ok = check_mosquitto()

    if not py_ok:
        print("\n❌ Python 3.10+ required. Install and try again.")
        sys.exit(1)

    # ── 1. .env ──
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("\n▶ Creating .env ...")
        src = ROOT / ".env.example"
        if src.exists():
            shutil.copy(src, env_file)

    # ── 2. Python dependencies ──
    print("\n▶ Installing Python dependencies ...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=True, text=True
    )
    if result.returncode != 0 and "externally-managed" in result.stderr:
        print("   Retrying (Homebrew Python, this may take a minute) ...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
             "--break-system-packages"],
        )

    # ── 3. React dependencies ──
    print("\n▶ Installing React dependencies ...")
    npm = which("npm")
    if npm:
        subprocess.run([npm, "install"], cwd=str(frontend))
    else:
        print("   Skipped — Node.js/npm not found")

    # ── 4. MQTT Broker ──
    print("\n▶ Starting MQTT broker ...")
    mosquitto = which("mosquitto")
    if mosquitto:
        if is_windows:
            subprocess.run(["taskkill", "/F", "/IM", "mosquitto.exe"],
                           capture_output=True)
        else:
            subprocess.run(["pkill", "mosquitto"], capture_output=True)
        subprocess.Popen([mosquitto, "-p", "1883"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   mosquitto started on :1883")
    else:
        print("   Skipped")

    # ── 5. Backend ──
    print("\n▶ Starting FastAPI backend ...")
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(2)

    # ── 6. Frontend ──
    if npm:
        print("▶ Starting React frontend ...")
        subprocess.Popen(
            [npm, "run", "dev"], cwd=str(frontend),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(2)

    print("\n" + "=" * 50)
    print("  Dashboard ready!")
    if npm:
        print(f"  React frontend:  http://localhost:5173")
    else:
        print(f"  React frontend:  NOT STARTED — install Node.js {NODE_MIN[0]}+")
    print(f"  Backend API:     http://localhost:8000")
    print("=" * 50)


if __name__ == "__main__":
    main()
