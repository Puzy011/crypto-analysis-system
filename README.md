<# 虚拟货币行情分析系统 - MVP 版本

## 🚀 项目简介

这是一个以 **AI 预测未来走势** 和 **庄家操作分析** 为核心的虚拟货币行情分析系统。

当前为 **MVP 版本**，包含：
- ✅ Binance 实时行情获取
- ✅ K线图展示（Lightweight Charts）
- ✅ 多币种行情列表
- 🔄 AI 预测（开发中）
- 🔄 庄家分析（开发中）

---

## 📁 项目结构

```
crypto-analysis-system/
├── backend/                    # 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   └── market.py
│   │   ├── core/           # 核心配置
│   │   │   └── config.py
│   │   ├── services/       # 业务逻辑
│   │   │   └── binance_service.py
│   │   └── main.py         # FastAPI 入口
│   └── requirements.txt     # Python 依赖
│
├── frontend/                   # 前端
│   ├── src/
│   │   ├── views/          # 页面
│   │   │   ├── Home.vue
│   │   │   └── Market.vue
│   │   ├── router/         # 路由
│   │   │   └── index.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
│
├── scripts/                    # 脚本
├── REQUIREMENTS_V2.md        # 需求文档（重点）
├── TECH_ARCHITECTURE.md      # 技术架构
├── GITHUB_REFERENCES.md      # GitHub 参考项目
└── README.md                # 本文件
```

---

## 📋 环境要求

### 后端环境
- Python 3.8 或更高版本
- pip（Python 包管理器）

### 前端环境
- Node.js 16.x 或更高版本
- npm 或 yarn

---

## 🛠️ 快速开始

### 方式一：使用启动脚本（推荐 - Linux/Mac）

```bash
# 运行准备脚本
bash scripts/start.sh
```

脚本会自动检查并安装后端依赖，然后提示你分别启动前后端服务。

---

### 方式二：手动启动

#### 1. 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# （可选）配置环境变量
# 创建 .env 文件并配置 Binance API（如需要）
# BINANCE_API_KEY=your_api_key
# BINANCE_API_SECRET=your_api_secret

# 启动后端服务
python -m app.main
```

后端服务将在 http://localhost:8000 启动

API 文档：http://localhost:8000/docs

---

#### 2. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
# 或使用 yarn
# yarn install

# 启动开发服务器
npm run dev
# 或使用 yarn
# yarn dev
```

前端服务将在 http://localhost:3000 启动

---

## 🔧 环境配置说明

### 后端配置

后端配置文件位于 `backend/app/core/config.py`，支持以下配置项：

| 配置项 | 说明 | 默认值 | 是否必需 |
|--------|------|--------|----------|
| `BINANCE_API_KEY` | Binance API 密钥 | "" | 否（使用公开接口可不配置） |
| `BINANCE_API_SECRET` | Binance API 密钥 | "" | 否（使用公开接口可不配置） |
| `DEBUG` | 调试模式 | True | 否 |

配置方式：
1. 在 `backend/` 目录下创建 `.env` 文件
2. 添加配置项（参考上表）

示例 `.env` 文件：
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
DEBUG=True
```

### 前端配置

前端默认连接到 `http://localhost:8000` 的后端服务。如需修改，可在前端代码中调整 API 基础 URL。

---

## 🌐 访问地址

启动成功后，可以访问以下地址：

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs （Swagger UI）
- **健康检查**: http://localhost:8000/health

---

## 📦 依赖说明

### 后端主要依赖

- **FastAPI**: 现代化的 Web 框架
- **Uvicorn**: ASGI 服务器
- **python-binance**: Binance API 客户端
- **pandas/numpy**: 数据处理
- **ta**: 技术指标计算
- **scikit-learn/xgboost/lightgbm**: 机器学习模型
- **prophet**: 时间序列预测
- **nltk/textblob**: 自然语言处理

### 前端主要依赖

- **Vue 3**: 渐进式 JavaScript 框架
- **Vue Router**: 路由管理
- **Pinia**: 状态管理
- **Element Plus**: UI 组件库
- **Lightweight Charts**: K线图表库
- **Axios**: HTTP 客户端
- **Vite**: 构建工具

---

## 📊 功能说明

### 核心功能

#### 1. 市场行情
- 多币种实时行情列表（BTC、ETH、BNB、SOL、XRP 等）
- K线图展示（支持多种时间周期：1m, 5m, 15m, 1h, 4h, 1d）
- 实时价格更新
- 24小时涨跌幅统计

#### 2. AI 预测
- 多模型预测（XGBoost、LightGBM、Prophet、Random Forest）
- 集成预测（Ensemble）
- 多时间框架分析
- 预测回测验证
- 实时预测更新

#### 3. 庄家/巨鲸分析
- 大单监控
- 资金流向分析
- 订单流分析（OrderFlow 风格）
- 庄家操作识别（吸筹、洗盘、拉升、出货）

#### 4. 舆情分析
- 新闻情感分析
- 社交媒体监控
- FinBERT 风格情感评分
- 实时舆情监控
- 主题建模分析

#### 5. 技术分析
- 完整技术指标（MA、MACD、RSI、布林带等）
- 多时间框架分析
- 技术形态识别

#### 6. 回测系统
- 预测准确率验证
- 策略回测
- 性能指标统计

---

## 🎯 开发路线图

### ✅ 已完成功能
- [x] Binance 实时行情获取
- [x] K线图展示（Lightweight Charts）
- [x] 多币种行情列表
- [x] 基础技术指标计算
- [x] 多模型 AI 预测
- [x] 庄家/巨鲸分析
- [x] 舆情分析系统
- [x] 预测回测验证
- [x] 实时监控功能

### 🔄 进行中
- [ ] 深度学习模型优化（LSTM/Transformer）
- [ ] 更多数据源集成
- [ ] 移动端适配

### 📅 计划中
- [ ] 用户系统和权限管理
- [ ] 自定义策略编辑器
- [ ] 告警推送系统
- [ ] 历史数据回放
- [ ] 多交易所支持

---

## � 常见问题

### 后端启动失败

**问题**: `ModuleNotFoundError: No module named 'xxx'`
**解决**: 确保已激活虚拟环境并安装所有依赖
```bash
source venv/bin/activate  # 激活虚拟环境
pip install -r requirements.txt  # 重新安装依赖
```

**问题**: 端口 8000 已被占用
**解决**: 修改 `backend/app/main.py` 中的端口号，或关闭占用端口的程序

### 前端启动失败

**问题**: `npm install` 失败
**解决**: 尝试清除缓存并重新安装
```bash
rm -rf node_modules package-lock.json
npm install
```

**问题**: 前端无法连接后端
**解决**: 确保后端服务已启动，检查 CORS 配置

### API 调用失败

**问题**: Binance API 限流
**解决**: 减少请求频率，或配置 API Key 提高限额

---

## 📚 参考文档

- [需求文档 V2.0](./REQUIREMENTS_V2.md) - 完整需求设计
- [技术架构](./TECH_ARCHITECTURE.md) - 技术方案详解
- [GitHub 参考项目](./GITHUB_REFERENCES.md) - 25+ 开源项目推荐

---

## ⚠️ 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。加密货币市场风险极高，投资需谨慎。

---

*项目版本: 2.0.0*
*最后更新: 2026-03-08*
