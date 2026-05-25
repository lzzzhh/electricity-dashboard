#!/bin/bash
# ==============================================
# Electricity Dashboard — 一键启动脚本
# 
# 前置条件:
#   1. Python 3.10+  +  pip install -r requirements.txt
#   2. Node.js 18+   +  cd frontend && npm install
#   3. Mosquitto      +  brew install mosquitto (macOS) 或 apt install mosquitto (Linux)
#   4. cp .env.example .env
#
# 用法:  bash start.sh
# ==============================================
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# ---- 0. 检查 .env ----
if [ ! -f .env ]; then
    echo "❌ 缺少 .env 文件，请先: cp .env.example .env"
    exit 1
fi

# ---- 1. MQTT Broker ----
echo "📡 启动 MQTT broker..."
if command -v mosquitto &>/dev/null; then
    pkill mosquitto 2>/dev/null || true
    mosquitto -p 1883 -d
    echo "   mosquitto started on :1883"
else
    echo "   ⚠️  mosquitto 未安装，跳过（需手动启动 broker）"
fi

# ---- 2. Backend ----
echo "🔧 启动 FastAPI 后端..."
pkill -f "uvicorn backend.main" 2>/dev/null || true
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 2

# ---- 3. Frontend ----
echo "🎨 启动 React 前端..."
cd frontend
pkill -f "vite" 2>/dev/null || true
nohup npm run dev > /tmp/frontend.log 2>&1 &
cd "$ROOT"
sleep 2

# ---- 4. Publisher (optional) ----
if [ -f run_publisher.py ]; then
    echo "📤 启动 MQTT publisher（连续模式）..."
    pkill -f "run_publisher" 2>/dev/null || true
    nohup python3 -u run_publisher.py --rounds 0 > /tmp/publisher.log 2>&1 &
else
    echo "📤 MQTT publisher skipped (run_publisher.py not found — use notebook Task 6 instead)"
fi

sleep 1
echo ""
echo "======================================"
echo "  ✅ 电力看板已启动"
echo "  React 前端:  http://localhost:5173"
echo "  API 后端:    http://localhost:8000"
echo "  Streamlit:   http://localhost:8501"
echo "======================================"
