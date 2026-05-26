#!/usr/bin/env python3
"""Electricity Dashboard — One-command launcher

Only requirement: Python 3.10+ (no Node.js needed — frontend is pre-built)
"""

import os, sys, subprocess, time, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON_MIN = (3, 10)


def main():
    print("=" * 50)
    print("  Electricity Dashboard — COMP5339 Assignment 2")
    print("=" * 50)

    is_windows = sys.platform == "win32"

    # ── Check Python version ──
    v = sys.version_info[:2]
    ok = v >= PYTHON_MIN
    print(f"\n▶ Python  [{f'OK (v{v[0]}.{v[1]})' if ok else f'NEED {PYTHON_MIN[0]}.{PYTHON_MIN[1]}+'}]\n")
    if not ok:
        print("  Download: https://python.org/downloads/")
        sys.exit(1)

    # ── 1. .env ──
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("▶ Creating .env ...")
        src = ROOT / ".env.example"
        if src.exists():
            shutil.copy(src, env_file)

    # ── 2. Python dependencies ──
    print("▶ Installing Python dependencies ...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=True, text=True
    )
    if result.returncode != 0 and "externally-managed" in result.stderr:
        print("   Retrying (Homebrew Python) ...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
             "--break-system-packages"],
        )

    # ── 3. MQTT Broker ──
    print("▶ Starting MQTT broker ...")
    mosquitto = shutil.which("mosquitto")
    if mosquitto:
        if is_windows:
            subprocess.run(["taskkill", "/F", "/IM", "mosquitto.exe"], capture_output=True)
        else:
            subprocess.run(["pkill", "mosquitto"], capture_output=True)
        subprocess.Popen([mosquitto, "-p", "1883"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   mosquitto :1883")
    else:
        print("   mosquitto not found — using pre-loaded data")

    # ── 4. Start backend (serves API + pre-built frontend) ──
    print("▶ Starting backend (API + dashboard) ...")
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(2)

    print("\n" + "=" * 50)
    print("  Dashboard:  http://localhost:8000")
    print("  API docs:   http://localhost:8000/docs")
    print("=" * 50)


if __name__ == "__main__":
    main()
