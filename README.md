# Crypto Analysis System

加密货币分析系统（前后端分离）：
- 市场行情与 K 线
- AI 预测与回测
- 巨鲸/庄家行为分析
- 综合舆情分析（多平台定时采集 + 时间趋势分析）

项目路径：`D:\Dev\crypto-analysis-system`

## 1. 环境要求

- Windows 10/11（当前文档按 PowerShell 编写）
- Python `3.10` 或 `3.11`（推荐 `3.11`）
- Node.js `>= 18`（推荐 LTS）
- npm `>= 9`
- Git

说明：
- 后端依赖包含 `prophet`、`xgboost`、`lightgbm`，建议使用 Python 3.10/3.11 以减少安装兼容问题。
- 不配置 Binance API Key 也可运行大部分功能（使用公开接口或降级数据）。

## 2. 后端运行（FastAPI）

### 2.1 创建并激活虚拟环境

```powershell
cd D:\Dev\crypto-analysis-system\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2.2 环境变量（可选但建议）

在 `backend` 目录创建 `.env` 文件：

```env
APP_NAME=Crypto Analysis System
APP_VERSION=2.0.0
DEBUG=true
BINANCE_API_KEY=
BINANCE_API_SECRET=
DATABASE_URL=
```

### 2.3 启动后端

```powershell
cd D:\Dev\crypto-analysis-system\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后地址：
- API 根：`http://localhost:8000/`
- 健康检查：`http://localhost:8000/api/health`
- Swagger：`http://localhost:8000/docs`

说明：
- 应用启动时会自动启动舆情调度器（多平台定时采集）。
- 运行时快照默认写入：`backend/data/sentiment_scheduler/multi_platform_snapshots.jsonl`

## 3. 前端运行（Vue 3 + Vite）

```powershell
cd D:\Dev\crypto-analysis-system\frontend
npm install
npm run dev
```

启动后地址：
- 前端：`http://localhost:3000`

说明：
- 前端已在 `vite.config.ts` 配置代理：`/api -> http://localhost:8000`
- 先启动后端，再启动前端，可直接联调。

## 4. 构建与发布检查

### 4.1 后端语法编译检查

```powershell
cd D:\Dev\crypto-analysis-system
python -m compileall backend/app
```

### 4.2 前端生产构建

```powershell
cd D:\Dev\crypto-analysis-system\frontend
npm run build
```

### 4.3 前端预览构建产物

```powershell
cd D:\Dev\crypto-analysis-system\frontend
npm run preview
```

## 5. 常见问题

### 5.1 `git pull` 报 443 连接失败

如果你本机有本地代理（例如 `127.0.0.1:7890`），可给当前仓库配置：

```powershell
cd D:\Dev\crypto-analysis-system
git config --local http.proxy http://127.0.0.1:7890
git config --local https.proxy http://127.0.0.1:7890
git pull --tags origin main
```

取消代理：

```powershell
git config --local --unset http.proxy
git config --local --unset https.proxy
```

### 5.2 PowerShell 不允许执行激活脚本

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 5.3 `ModuleNotFoundError: app`

请在 `backend` 目录下启动 `uvicorn app.main:app ...`，不要在其他目录直接运行。

### 5.4 NLP 语料缺失（少数环境）

如遇 `textblob/nltk` 语料报错：

```powershell
cd D:\Dev\crypto-analysis-system\backend
.\.venv\Scripts\Activate.ps1
python -m textblob.download_corpora
```

## 6. 免责声明

本项目仅用于学习与研究，不构成任何投资建议。加密货币市场风险高，请独立判断并自行承担风险。
