# 虚拟货币行情分析系统 - 项目结构与技术选型

## 📁 推荐项目结构

### 方案一：纯前端方案（推荐 MVP）

```
crypto-analysis-system/
├── public/                     # 静态资源
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/          # 组件
│   │   ├── charts/         # 图表组件
│   │   │   ├── KLineChart.vue  # K线图
│   │   │   └── DepthChart.vue # 深度图
│   │   ├── market/         # 市场相关
│   │   │   ├── MarketList.vue    # 市场列表
│   │   │   └── PriceCard.vue   # 价格卡片
│   │   ├── watchlist/      # 自选相关
│   │   │   └── WatchList.vue   # 自选列表
│   │   └── alert/          # 预警相关
│   │       └── AlertManager.vue # 预警管理
│   ├── services/            # API 服务
│   │   ├── binance.ts      # 币安 API
│   │   ├── okx.ts          # OKX API
│   │   └── websocket.ts    # WebSocket 服务
│   ├── stores/              # 状态管理
│   │   ├── market.ts        # 市场数据
│   │   ├── watchlist.ts     # 自选数据
│   │   └── alert.ts        # 预警数据
│   ├── utils/               # 工具函数
│   │   ├── format.ts       # 格式化
│   │   ├── calculation.ts  # 计算函数
│   │   └── storage.ts     # 本地存储
│   ├── views/               # 页面视图
│   │   ├── Home.vue         # 首页
│   │   ├── Market.vue       # 市场页
│   │   ├── Detail.vue       # 币种详情
│   │   ├── Watchlist.vue    # 自选页
│   │   ├── Alert.vue        # 预警页
│   │   └── Settings.vue     # 设置页
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

### 方案二：前后端分离（完整版本

```
crypto-analysis-system/
├── frontend/                  # 前端（同方案一）
│   └── ...
├── backend/                   # 后端
│   ├── api/                # API 路由
│   │   ├── market.py
│   │   ├── watchlist.py
│   │   └── alert.py
│   ├── services/            # 业务逻辑
│   │   ├── data_collector.py  # 数据采集
│   │   └── alert_service.py # 预警服务
│   ├── models/              # 数据模型
│   │   ├── market.py
│   │   └── alert.py
│   ├── db/                 # 数据库
│   │   └── init.sql
│   └── main.py
│   └── requirements.txt
└── docker-compose.yml
└── README.md
```

---

## 🛠️ 技术选型详细说明

### 前端技术栈

#### 1. 框架选择

**推荐：Vue 3 + TypeScript**

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "typescript": "^5.3.0"
  }
}
```

**理由：**
- Vue 3 组合式 API 更灵活
- TypeScript 提供类型安全
- Pinia 状态管理简单易用
- 生态丰富，学习曲线平缓

**备选：React + TypeScript

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "redux-toolkit": "^2.0.0",
    "typescript": "^5.3.0"
  }
}
```

---

#### 2. UI 组件库

**推荐：Element Plus（Vue）**

```json
{
  "dependencies": {
    "element-plus": "^2.4.0",
    "@element-plus/icons-vue": "^2.3.0"
  }
}
```

**备选：Ant Design Vue**

```json
{
  "dependencies": {
    "ant-design-vue": "^4.0.0"
  }
}
```

**React 备选：Ant Design / Material-UI

---

#### 3. 图表库（最重要！

**推荐方案：Lightweight Charts（TradingView 开源版）**

```json
{
  "dependencies": {
    "lightweight-charts": "^4.1.0"
  }
}
```

**优点：**
- TradingView 团队开发，质量高
- 性能优秀，专门为金融图表设计
- 轻量级，加载快
- 支持 K线、成交量、技术指标
- 完全免费开源

**示例代码：
```typescript
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';

const chart = createChart(document.getElementById('chart')!);
const candlestickSeries = chart.addCandlestickSeries();
```

---

**备选方案：ECharts

```json
{
  "dependencies": {
    "echarts": "^5.4.0"
  }
}
```

**优点：**
- 功能非常强大
- 图表类型丰富
- 中文文档完善

---

#### 4. HTTP 客户端

```json
{
  "dependencies": {
    "axios": "^1.6.0"
  }
}
```

---

#### 5. 构建工具

**推荐：Vite

```json
{
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^5.0.0"
  }
}
```

**理由：开发体验极佳，启动快，热更新快

---

### 后端技术栈（如需要）

#### 1. Python + FastAPI（推荐）

```txt
fastapi==0.104.0
uvicorn[standard]==0.24.0
websockets==12.0
aiohttp==3.9.0
sqlalchemy==2.0.0
aiosqlite==0.19.0
redis==5.0.0
celery==5.3.0
```

**理由：**
- FastAPI 高性能异步框架
- 自动生成 API 文档
- Type Hints 支持
- WebSocket 原生支持

---

#### 2. Node.js + Express（备选）

```json
{
  "dependencies": {
    "express": "^4.18.0",
    "ws": "^8.14.0",
    "axios": "^1.6.0",
    "sqlite3": "^5.1.0"
  }
}
```

---

### 数据库选择

#### 本地存储（纯前端方案）：
- **IndexedDB** - 浏览器本地数据库
- **localStorage** - 简单配置存储

#### 服务端存储（前后端方案）：
- **SQLite** - 轻量级，适合单机部署简单
- **PostgreSQL** - 功能强大，适合生产环境

---

## 📦 推荐的 package.json（MVP 版本

```json
{
  "name": "crypto-analysis-system",
  "version": "1.0.0",
  "type": "private",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "element-plus": "^2.4.0",
    "@element-plus/icons-vue": "^2.3.0",
    "lightweight-charts": "^4.1.0",
    "axios": "^1.6.0",
    "dayjs": "^1.11.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vue-tsc": "^1.8.0"
  }
}
```

---

## 🎯 MVP 版本技术栈总结

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 框架 | Vue 3 + TypeScript | 现代化、类型安全 |
| UI | Element Plus | 组件丰富、中文友好 |
| 图表 | Lightweight Charts | TradingView 出品 |
| 状态管理 | Pinia | Vue 3 官方推荐 |
| 构建工具 | Vite | 开发体验极佳 |
| HTTP | Axios | 功能完善 |
| 数据来源 | Binance API | 最完善的交易所 API |

---

## 🚀 快速开始（MVP 版本）

### 1. 初始化项目

```bash
# 创建项目
npm create vite@latest crypto-analysis -- --template vue-ts
cd crypto-analysis

# 安装依赖
npm install
npm install vue-router pinia element-plus @element-plus/icons-vue lightweight-charts axios dayjs

# 启动开发服务器
npm run dev
```

### 2. 基础配置

详见 `SETUP_GUIDE.md`（待创建）

---

*文档版本: v1.0*
*创建日期: 2026-03-04*
