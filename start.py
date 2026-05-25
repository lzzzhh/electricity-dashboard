#!/usr/bin/env python3
"""Electricity Dashboard — One-command launcher (cross-platform)"""
import os, sys, subprocess, time, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run(cmd, cwd=None, shell=False):
    print(f"  → {cmd}")
    return subprocess.run(cmd, cwd=str(cwd or ROOT), shell=shell)

def main():
    print("=" * 50)
    print("  Electricity Dashboard — COMP5339 Assignment 2")
    print("=" * 50)

    # 1. Ensure .env exists
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("\n[1/4] Creating .env ...")
        shutil.copy(ROOT / ".env.example", env_file)

    # 2. Platform detection
    is_windows = sys.platform == "win32"

    # 3. Python dependencies
    print("\n[2/5] Installing Python dependencies ...")
    # Try normal pip first, fall back to --break-system-packages for Homebrew Python
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
        capture_output=True, text=True
    )
    if result.returncode != 0 and "externally-managed" in result.stderr:
        print("   Retrying with --break-system-packages (Homebrew Python) ...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q", "--break-system-packages"],
            capture_output=True, text=True
        )

    # 4. React dependencies
    print("\n[3/5] Installing React dependencies ...")
    frontend = ROOT / "frontend"
    if is_windows:
        run(["npm.cmd", "install", "--silent"], cwd=frontend, shell=True)
    else:
        run(["npm", "install", "--silent"], cwd=frontend)

    # 5. MQTT Broker (skip on Windows if mosquitto not in PATH)
    print("\n[4/5] Starting MQTT broker ...")
    mosquitto = shutil.which("mosquitto")
    if mosquitto:
        # Kill existing mosquitto
        if is_windows:
            subprocess.run(["taskkill", "/F", "/IM", "mosquitto.exe"], capture_output=True)
        else:
            subprocess.run(["pkill", "mosquitto"], capture_output=True)
        subprocess.Popen([mosquitto, "-p", "1883"])
        print("   mosquitto started on :1883")
    else:
        print("   mosquitto not found — dashboard will work with pre-loaded data")

    # 6. Backend
    print("\n[5/5] Starting services ...")
    if is_windows:
        subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app",
                          "--host", "0.0.0.0", "--port", "8000"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app",
                          "--host", "0.0.0.0", "--port", "8000"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    # 7. Frontend
    frontend_cmd = ["npm.cmd" if is_windows else "npm", "run", "dev"]
    subprocess.Popen(frontend_cmd, cwd=str(frontend),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    print("\n" + "=" * 50)
    print("  Dashboard ready!")
    print("  React frontend:  http://localhost:5173")
    print("  Backend API:     http://localhost:8000")
    print("=" * 50)


if __name__ == "__main__":
    main()
