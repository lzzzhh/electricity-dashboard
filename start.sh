#!/bin/bash
# ==============================================
# Electricity Dashboard — 一键启动
# 
# 前置条件:
#   Python 3.10+  +  Node.js 18+  +  Mosquitto
#
# 用法:  bash start.sh
# ==============================================
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# ---- 0. 自动配置 .env ----
if [ ! -f .env ]; then
    echo "📝 创建 .env ..."
    cp .env.example .env
fi

# ---- 1. 自动安装 Python 依赖 ----
echo "📦 安装 Python 依赖..."
pip install -r requirements.txt -q

# ---- 2. 自动安装 React 依赖 ----
echo "📦 安装 React 依赖..."
cd frontend && npm install --silent && cd "$ROOT"

# ---- 3. MQTT Broker ----
echo "📡 启动 MQTT broker..."
if command -v mosquitto &>/dev/null; then
    pkill mosquitto 2>/dev/null || true
    mosquitto -p 1883 -d
    echo "   mosquitto started on :1883"
else
    echo "   ⚠️  mosquitto 未安装，跳过"
fi

# ---- 4. Backend ----
echo "🔧 启动 FastAPI 后端..."
pkill -f "uvicorn backend.main" 2>/dev/null || true
nohup python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 2

# ---- 5. Frontend ----
echo "🎨 启动 React 前端..."
cd frontend
pkill -f "vite" 2>/dev/null || true
nohup npm run dev > /tmp/frontend.log 2>&1 &
cd "$ROOT"
sleep 2

echo ""
echo "======================================"
echo "  ✅ 电力看板已启动"
echo "  React 前端:  http://localhost:5173"
echo "  API 后端:    http://localhost:8000"
echo "======================================"
