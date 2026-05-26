#!/usr/bin/env python3
"""Electricity Dashboard — One-command launcher (cross-platform)"""
import os, sys, subprocess, time, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def which(cmd):
    """Find command in PATH, with Windows fallback (npm → npm.cmd)."""
    path = shutil.which(cmd)
    if not path and sys.platform == "win32" and not cmd.endswith(".cmd"):
        path = shutil.which(cmd + ".cmd")
    return path


def main():
    print("=" * 50)
    print("  Electricity Dashboard — COMP5339 Assignment 2")
    print("=" * 50)

    is_windows = sys.platform == "win32"
    frontend = ROOT / "frontend"

    # 1. Ensure .env exists
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("\n[1/5] Creating .env ...")
        src = ROOT / ".env.example"
        if src.exists():
            shutil.copy(src, env_file)
        else:
            env_file.write_text("MQTT_HOST=localhost\nMQTT_PORT=1883\nDATABASE_URL=sqlite:///./data/electricity.db\n")

    # 2. Python dependencies
    print("\n[2/5] Installing Python dependencies ...")
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

    # 3. React dependencies
    print("\n[3/5] Installing React dependencies ...")
    npm = which("npm")
    if npm:
        subprocess.run([npm, "install", "--silent"], cwd=str(frontend))
    else:
        print("   npm not found. Install Node.js from https://nodejs.org")
        print("   React frontend will be skipped — API still works at :8000")

    # 4. MQTT Broker
    print("\n[4/5] Starting MQTT broker ...")
    mosquitto = which("mosquitto")
    if mosquitto:
        if is_windows:
            subprocess.run(["taskkill", "/F", "/IM", "mosquitto.exe"],
                           capture_output=True)
        else:
            subprocess.run(["pkill", "mosquitto"], capture_output=True)
        subprocess.Popen([mosquitto, "-p", "1883"])
        print("   mosquitto started on :1883")
    else:
        print("   mosquitto not found — dashboard uses pre-loaded data")

    # 5. Backend
    print("\n[5/5] Starting services ...")
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(2)

    # 6. Frontend (if npm available)
    if npm:
        subprocess.Popen(
            [npm, "run", "dev"], cwd=str(frontend),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(2)

    print("\n" + "=" * 50)
    print("  Dashboard ready!")
    if npm:
        print("  React frontend:  http://localhost:5173")
    else:
        print("  React frontend:  NOT STARTED (install Node.js first)")
    print("  Backend API:     http://localhost:8000")
    print("=" * 50)


if __name__ == "__main__":
    main()
