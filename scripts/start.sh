#!/bin/bash
# 虚拟货币行情分析系统 - 快速启动脚本

echo "🚀 启动虚拟货币行情分析系统..."
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "📁 项目目录: $PROJECT_ROOT"
echo ""

# 检查后端依赖
echo "📦 检查后端依赖..."
if [ ! -d "backend/venv" ]; then
    echo "   创建虚拟环境..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo "   安装 Python 依赖..."
    pip install -r requirements.txt
    cd ..
else
    echo "   虚拟环境已存在"
fi

echo ""
echo "✅ 后端准备就绪！"
echo ""
echo "📋 启动步骤："
echo ""
echo "1️⃣  启动后端（终端 1）："
echo "    cd $PROJECT_ROOT/backend"
echo "    source venv/bin/activate"
echo "    python -m app.main"
echo ""
echo "2️⃣  启动前端（终端 2）："
echo "    cd $PROJECT_ROOT/frontend"
echo "    npm install"
echo "    npm run dev"
echo ""
echo "3️⃣  访问："
echo "    前端: http://localhost:3000"
echo "    后端 API: http://localhost:8000"
echo "    API 文档: http://localhost:8000/docs"
echo ""
