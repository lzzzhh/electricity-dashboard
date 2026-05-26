#!/bin/bash
# ==============================================
# Electricity Dashboard — 一键启动
# 自动检测并安装 Python 依赖后启动项目
# ==============================================
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=================================================="
echo "  Electricity Dashboard — COMP5339 Assignment 2"
echo "=================================================="

# --- 检测 Python ---
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "❌ 未找到 Python。请先安装 Python 3.10+:"
    echo "   macOS:  brew install python"
    echo "   Linux:  sudo apt install python3"
    echo "   Win:    https://python.org/downloads/"
    exit 1
fi

V=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python: $V"

# --- 安装依赖 ---
echo "安装 Python 依赖..."
$PYTHON -m pip install -r requirements.txt -q 2>/dev/null || \
$PYTHON -m pip install -r requirements.txt --break-system-packages -q 2>/dev/null || \
$PYTHON -m pip install -r requirements.txt 2>/dev/null

# --- 创建 .env ---
if [ ! -f .env ]; then
    cp .env.example .env
fi

# --- MQTT ---
echo "启动 MQTT broker..."
if command -v mosquitto &>/dev/null; then
    pkill mosquitto 2>/dev/null || true
    mosquitto -p 1883 -d 2>/dev/null && echo "   mosquitto :1883" || echo "   mosquitto 启动失败"
else
    echo "   mosquitto 未安装（跳过）"
fi

# --- 启动 ---
echo "启动后端..."
pkill -f "uvicorn backend" 2>/dev/null || true
$PYTHON -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
sleep 2

echo ""
echo "=================================================="
echo "  Dashboard:  http://localhost:8000"
echo "  API docs:   http://localhost:8000/docs"
echo "=================================================="
