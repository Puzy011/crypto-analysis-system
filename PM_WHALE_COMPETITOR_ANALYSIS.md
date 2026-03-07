# 庄家预测功能产品对比与优化（PM 视角）

## 1. 对比范围

- 竞品：`aice100`（2026-03-07 抓取 `https://www.aice100.com/static/app.js?v=1.42` 与 `dashboard.js`）
- 我方：`/api/whale-analysis/*` + `frontend/src/views/WhaleAnalysis.vue`

## 2. 竞品是怎么分析的（从前端反推）

从竞品脚本可确认其核心输出结构：

- 模式：`trade_type = realtime / intraday / longterm`
- 主结论：`whale_direction`、`whale_action`、`trade_advice`、`risk_control`
- 信号说明：`signal_explanation[]` + `summary`
- 聪明钱：`smart_money`（多空仓位、交易员、巨鲸数量、盈亏）
- 极端事件：`extreme_30day[]`
- 状态：`analysis_mode`、`plan_type`

另外，竞品仪表盘直接展示 `funding_rate`，并在 Loading 文案中强调“资金费率与持仓偏移”，说明其策略中包含合约侧偏离因子。

## 3. 我们之前的差距

- 数据源深度不足：主要基于 K 线近似，缺少真实逐笔与盘口信息。
- 合约维度不足：虽有多空画像，但缺少 `funding_rate / open interest / long-short ratio` 的直接接入。
- 可信度不可见：前端无法知道本次分析到底使用了哪些数据源，用户难判断结果可靠性。

## 4. 本轮已落地优化

### 4.1 数据源精度升级（后端）

- 新增 Binance 实时数据接入：
  - `aggTrades`（聚合成交，逐笔近似）
  - `depth`（订单簿深度）
  - `futures openInterest`
  - `globalLongShortAccountRatio`
  - `fundingRate`
  - `openInterestHist`

- 在 `whale-analysis/full` 中并行拉取上述数据并融合到分析链路。

### 4.2 分析算法升级

- 大单检测：
  - 修正 Binance `is_buyer_maker` 方向解释（此前常见误判点）
  - 优先使用真实成交样本识别大单，K 线仅作为兜底

- 订单流分析：
  - 新增盘口不平衡 `book_imbalance`
  - 新增融合不平衡 `combined_imbalance = 0.75 * trade + 0.25 * orderbook`
  - 方向判定由 `combined_imbalance` 驱动，降低单一源噪声

- 主结论/预警：
  - 将 `funding_rate / long_short_ratio / OI变化` 纳入多空评分
  - 新增“多头拥挤/空头拥挤/OI异动”预警

### 4.3 产品可解释性升级

- 新增 `data_quality`（质量评分 + 来源覆盖）
- 前端新增“数据可信度”与“合约偏离指标”面板，用户可直观看到：
  - 样本量（成交笔数、盘口档位）
  - 数据源覆盖（K线/成交/盘口/合约）
  - 资金费率、多空比、OI变化

## 5. 数据源准确性对比（当前）

- 竞品：可确认使用多维数据（至少包含资金费率、仓位偏移、智能结论），但后端实现不可见，透明度有限。
- 我方：已明确接入 Binance 原始接口并输出 `data_quality`，可追溯性更强。

结论：

- 在“可解释性与可验证性”上，我方已具备明显优势（来源覆盖直接暴露给用户）。
- 在“跨交易所与链上资金流”方面仍有提升空间（见下一步）。

## 6. 下一步优先级建议

P0：

- 接入多交易所（OKX/Bybit）同类合约指标，减少单交易所偏差。
- 增加数据异常保护（接口空返回、时间戳异常、极值平滑）。

P1：

- 增加链上巨鲸转账与交易所净流入（真实“庄家行为”维度）。
- 回测“预警命中率”，把策略效果量化成可视指标（近7天、30天）。

P2：

- 形成“模式-策略模板”：
  - realtime：偏盘口/成交驱动
  - intraday：偏订单流+阶段识别
  - longterm：偏合约结构+宏观事件
