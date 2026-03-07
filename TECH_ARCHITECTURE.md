# 虚拟货币行情分析系统 - 技术架构设计

## 🏗️ 系统整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Vue 3)                            │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌─────────┐      │
│  │ 行情展示  │  │ AI 预测  │  │ 庄家分析 │  │ 预警系统 │      │
│  └──────────┘  └──────────┘  └─────────┘  └─────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      API 网关 (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  行情 API    │  │  AI 预测 API  │  │  庄家分析 API │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      业务逻辑层                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ 数据采集服务 │  │ 特征工程服务 │  │ 模型推理服务 │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ 庄家识别服务 │  │ 预警服务     │  │ 回测服务     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                        数据层                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ 时序数据库    │  │ 关系数据库    │  │  模型仓库     │       │
│  │ (InfluxDB)   │  │ (PostgreSQL)  │  │  (ML models) │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │  缓存        │  │  消息队列     │                           │
│  │  (Redis)     │  │  (Redis/Celery)│                          │
│  └──────────────┘  └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      外部数据源                                    │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌─────────┐      │
│  │ Binance  │  │   OKX    │  │ 新闻API  │  │ 其他... │      │
│  └──────────┘  └──────────┘  └─────────┘  └─────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 技术栈详细说明

### 前端技术栈

| 技术 | 选型 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Vue 3 | ^3.4 | 组合式 API，TypeScript 支持 |
| 路由 | Vue Router | ^4.2 | 官方路由 |
| 状态管理 | Pinia | ^2.1 | 轻量级状态管理 |
| UI 组件 | Element Plus | ^2.4 | 企业级组件库 |
| 图表库 | ECharts | ^5.4 | 数据可视化 |
| K线图 | Lightweight Charts | ^4.1 | TradingView 出品 |
| HTTP 客户端 | Axios | ^1.6 | HTTP 请求 |
| WebSocket | 原生 WebSocket | - | 实时数据推送 |
| 构建工具 | Vite | ^5.0 | 快速开发构建 |

---

### 后端技术栈

| 技术 | 选型 | 版本 | 说明 |
|------|------|------|------|
| 语言 | Python | 3.10+ | AI/ML 生态最好 |
| Web 框架 | FastAPI | ^0.104 | 高性能异步框架 |
| ASGI 服务器 | Uvicorn | ^0.24 | ASGI 服务器 |
| 任务队列 | Celery | ^5.3 | 异步任务处理 |
| 任务调度 | APScheduler | ^3.10 | 定时任务 |

---

### AI/机器学习技术栈

| 技术 | 选型 | 版本 | 说明 |
|------|------|------|------|
| 深度学习 | PyTorch | ^2.1 | 灵活的深度学习框架 |
| 传统 ML | Scikit-learn | ^1.3 | 机器学习算法库 |
| 梯度提升 | XGBoost / LightGBM | ^2.0 / ^4.0 | GBDT 算法 |
| 时序模型 | tsfresh / statsmodels | ^0.20 / ^0.14 | 时间序列分析 |
| 技术指标 | TA-Lib | ^0.4 | 技术指标计算 |
| 数据处理 | Pandas / NumPy | ^2.0 / ^1.24 | 数据处理 |
| 模型序列化 | Joblib / Pickle | ^1.3 | 模型保存加载 |
| 超参数优化 | Optuna | ^3.4 | 自动超参数调优 |

---

### 数据库技术栈

| 技术 | 选型 | 版本 | 说明 |
|------|------|------|------|
| 时序数据库 | InfluxDB | ^2.7 | 专门存储时序数据 |
| 关系型数据库 | PostgreSQL | ^15 | 通用关系型数据库 |
| ORM | SQLAlchemy | ^2.0 | Python ORM |
| 缓存 | Redis | ^7.0 | 缓存和消息队列 |

---

## 📁 项目目录结构

```
crypto-analysis-system/
├── frontend/                           # 前端
│   ├── public/
│   ├── src/
│   │   ├── components/                # 组件
│   │   │   ├── charts/               # 图表组件
│   │   │   │   ├── KLineChart.vue
│   │   │   │   ├── PredictionChart.vue
│   │   │   │   └── WhaleChart.vue
│   │   │   ├── market/
│   │   │   ├── prediction/           # AI 预测组件
│   │   │   │   ├── PricePrediction.vue
│   │   │   │   ├── TrendAnalysis.vue
│   │   │   │   └── FeatureImportance.vue
│   │   │   ├── whale/                # 庄家分析组件
│   │   │   │   ├── WhaleDetection.vue
│   │   │   │   ├── PhaseIndicator.vue
│   │   │   │   └── OrderFlow.vue
│   │   │   └── alert/
│   │   ├── services/                 # API 服务
│   │   │   ├── api.ts
│   │   │   ├── prediction.ts
│   │   │   └── whale.ts
│   │   ├── stores/                   # 状态管理
│   │   │   ├── market.ts
│   │   │   ├── prediction.ts
│   │   │   └── whale.ts
│   │   ├── views/                    # 页面
│   │   │   ├── Home.vue
│   │   │   ├── Prediction.vue        # 预测页面
│   │   │   ├── WhaleAnalysis.vue     # 庄家分析页面
│   │   │   └── ...
│   │   └── main.ts
│   └── package.json
│
├── backend/                            # 后端
│   ├── app/
│   │   ├── api/                       # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── market.py
│   │   │   ├── prediction.py         # 预测 API
│   │   │   └── whale.py             # 庄家分析 API
│   │   ├── core/                      # 核心配置
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── services/                  # 业务逻辑
│   │   │   ├── data_collector.py      # 数据采集
│   │   │   ├── feature_engineer.py    # 特征工程
│   │   │   ├── prediction_service.py # 预测服务
│   │   │   ├── whale_service.py      # 庄家分析服务
│   │   │   ├── alert_service.py      # 预警服务
│   │   │   └── backtest_service.py   # 回测服务
│   │   ├── models/                    # 数据模型
│   │   │   ├── market.py
│   │   │   ├── prediction.py
│   │   │   └── whale.py
│   │   ├── ml/                        # 机器学习模块
│   │   │   ├── features/              # 特征定义
│   │   │   │   ├── price_features.py
│   │   │   │   ├── technical_features.py
│   │   │   │   ├── volume_features.py
│   │   │   │   └── sentiment_features.py
│   │   │   ├── models/                # 模型定义
│   │   │   │   ├── lstm_model.py
│   │   │   │   ├── transformer_model.py
│   │   │   │   ├── xgboost_model.py
│   │   │   │   └── ensemble_model.py
│   │   │   ├── trainers/              # 模型训练
│   │   │   │   ├── trainer_base.py
│   │   │   │   └── model_trainer.py
│   │   │   └── model_store.py        # 模型管理
│   │   ├── whale/                     # 庄家分析模块
│   │   │   ├── detectors/             # 识别器
│   │   │   │   ├── accumulation_detector.py
│   │   │   │   ├── washout_detector.py
│   │   │   │   ├── pump_detector.py
│   │   │   │   └── distribution_detector.py
│   │   │   ├── indicators/            # 指标
│   │   │   │   ├── order_flow.py
│   │   │   │   ├── chip_distribution.py
│   │   │   │   └── money_flow.py
│   │   │   └── tracker.py             # 追踪器
│   │   └── main.py
│   ├── tests/
│   ├── scripts/                       # 脚本
│   │   ├── train_model.py            # 训练模型
│   │   ├── backtest.py              # 回测
│   │   └── init_db.py               # 初始化数据库
│   ├── models/                        # 训练好的模型文件
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```

---

## 🧠 AI 预测模块设计

### 特征工程流程

```
原始数据 (OHLCV)
    ↓
[价格特征]
- 收益率、对数收益率
- 波动率、ATR
- 价格动量
    ↓
[技术指标特征]
- MA、EMA、MACD、BOLL
- RSI、KDJ、WR、CCI
- OBV、Volume Profile
    ↓
[交易量特征]
- 成交量变化率
- 量价相关性
- 大单占比
    ↓
[资金流向特征]
- 主力资金流入/流出
- 不同级别资金流向
    ↓
[市场情绪特征]
- 恐慌贪婪指数
- 多空比
    ↓
特征选择与降维
    ↓
模型输入特征
```

### 模型架构

#### 1. LSTM 模型
```python
class LSTMPredictor(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
```

#### 2. Transformer 模型
```python
class TransformerPredictor(nn.Module):
    def __init__(self, input_dim, d_model, nhead, num_layers, output_dim):
        super().__init__()
        self.embedding = nn.Linear(input_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        self.fc = nn.Linear(d_model, output_dim)
```

#### 3. 集成模型
```
LSTM 预测 ──┐
             ├──→ 加权融合 → 最终预测
XGBoost 预测 ─┘
```

---

## 🕵️ 庄家分析模块设计

### 庄家阶段识别流程

```
实时行情数据
    ↓
[大单分析]
- 大单成交量
- 大单买卖方向
- 大单挂单/撤单
    ↓
[资金流向分析]
- 主力资金流向
- 资金背离检测
    ↓
[筹码分布分析]
- 筹码集中度
- 平均持仓成本
    ↓
[模式匹配]
- 吸筹模式
- 洗盘模式
- 拉升模式
- 出货模式
    ↓
[阶段判断]
- 当前所处阶段
- 置信度评分
- 下一步预测
```

### 各阶段识别特征

| 阶段 | 价格特征 | 成交量特征 | 资金流向 | 筹码分布 |
|------|---------|-----------|---------|---------|
| 吸筹 | 低位横盘 | 温和放量 | 持续流入 | 集中度提升 |
| 洗盘 | 快速下跌后收回 | 异常放量 | 先出后入 | 集中度稳定 |
| 拉升 | 快速上涨 | 显著放量 | 大幅流入 | 集中度高位 |
| 出货 | 高位震荡 | 放量滞涨 | 持续流出 | 集中度下降 |

---

## 📊 数据流设计

### 实时数据流

```
交易所 WebSocket
    ↓
数据采集服务
    ↓
数据清洗与格式化
    ↓
实时特征计算
    ↓
┌─────────────┬─────────────┐
↓             ↓             ↓
[实时行情]   [AI 预测]    [庄家分析]
   ↓             ↓             ↓
Redis 缓存   模型推理      模式匹配
   ↓             ↓             ↓
前端展示    预测结果      识别结果
              ↓             ↓
           预警检查       预警检查
              ↓             ↓
           预警触发       预警触发
```

### 批量数据流（定时任务）

```
定时任务启动
    ↓
从交易所 API 获取历史数据
    ↓
存入 InfluxDB
    ↓
批量特征计算
    ↓
模型重新训练（每天/每周）
    ↓
模型性能评估
    ↓
更新模型仓库
```

---

## 🚀 部署方案

### 开发环境
```bash
# 前端
cd frontend
npm install
npm run dev

# 后端
cd backend
pip install -r requirements.txt
python -m app.main
```

### Docker 部署
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - influxdb
      - redis
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
  
  influxdb:
    image: influxdb:2.7
  
  redis:
    image: redis:7.0
```

---

*文档版本: v1.0*
*创建日期: 2026-03-04*
