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

## 🛠️ 快速开始

### 1. 后端启动

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 .\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动后端
python -m app.main
```

后端服务将在 http://localhost:8000 启动

API 文档：http://localhost:8000/docs

---

### 2. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:3000 启动

---

## 📊 MVP 功能说明

### 首页
- 系统介绍
- 后端健康检查
- 快速导航到市场行情

### 市场行情页
- 多币种实时行情列表（BTC、ETH、BNB、SOL、XRP）
- K线图展示（支持多种时间周期）
- 点击币种切换查看

---

## 🎯 后续开发计划

### 第二阶段
- [ ] 技术指标计算（MA、MACD、RSI 等）
- [ ] 基础价格预测（ML 模型）
- [ ] 大单分析
- [ ] 价格预警

### 第三阶段
- [ ] LSTM/Transformer 深度学习预测
- [ ] 完整庄家操作识别（吸-洗-拉-出）
- [ ] 资金流向分析
- [ ] 新闻舆情分析

---

## 📚 参考文档

- [需求文档 V2.0](./REQUIREMENTS_V2.md) - 完整需求设计
- [技术架构](./TECH_ARCHITECTURE.md) - 技术方案详解
- [GitHub 参考项目](./GITHUB_REFERENCES.md) - 25+ 开源项目推荐

---

## ⚠️ 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。加密货币市场风险极高，投资需谨慎。

---

*项目版本: MVP 1.0*
*创建日期: 2026-03-04*
