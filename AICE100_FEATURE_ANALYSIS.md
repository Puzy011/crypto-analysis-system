# AICE100 庄家分析功能拆解与本项目映射

## 1. 页面功能拆解（基于 2026-03-07 抓取）

核心交互来自 `https://www.aice100.com/static/app.js?v=1.42`，其研究面板使用以下关键字段：

- 交易模式：`realtime` / `intraday` / `longterm`
- 主结论区：`whale_direction`、`whale_action`、`trade_advice`、`risk_control`
- 信号解释区：`signal_explanation[]`、`summary`
- 聪明钱面板：`smart_money`（含多空仓位、交易员、巨鲸数量、建仓均价、盈亏）
- 极端事件：`extreme_30day[]`
- 状态标识：`analysis_mode`、`plan_type`、`trade_type`

## 2. 我们已实现的对应能力

后端 `whale-analysis/full/{symbol}` 已新增/对齐：

- `whale_direction`、`whale_action`、`trade_advice`、`risk_control`
- `signal_explanation`、`summary`
- `smart_money`（包含 `total_positions_m`、`long_short_ratio_percent`、`long/short_whales_*` 等）
- `extreme_30day`（过去 30 天极端波动提取）
- `trade_type="realtime"`、`analysis_mode="ai"`、`smart_money_full=true`

并保留原有兼容字段：

- `overall`、`large_orders`、`order_flow`、`manipulation_phase`、`alerts`

## 3. 核心算法升级

- 大单检测：从默认 mock 改为基于真实 K 线 `quoteVolume/takerBuyQuote` 的动态阈值识别。
- 订单流：新增 `aggressive_buy_ratio`、`cvd_change`，提高买卖主导判断稳定性。
- 阶段识别：按吸筹/洗盘/拉升/出货重写条件，加入趋势、波动、量能确认。
- 智能总结：综合大单方向 + 订单流 + 阶段输出主力动作与风险建议。

## 4. 前端改造

`WhaleAnalysis.vue` 已新增：

- 主力结论卡片（方向/动作/风险/建议）
- 聪明钱分布卡片（总仓位、多空比、巨鲸数量）
- 信号解读与近期极端事件列表

## 5. 当前仍可继续增强

- 若后续接入逐笔成交/订单簿 WS，可把“大单检测和聪明钱画像”从 K 线近似升级到盘口级精度。
- 可新增 `intraday/longterm` 两套阈值参数，和 AICE100 的模式切换完全一致。

## 6. 与竞品差距（当前）与本轮优化

当前差距：

- 模式策略：此前仅固定 `realtime`，无法按 `intraday/longterm` 切换阈值和采样周期。
- 前端交互：此前页面无交易模式切换，且刷新周期固定，不符合不同持仓周期的观察节奏。
- 协议可读性：此前 API 不暴露模式配置，前端难以显示“当前模式说明”。

本轮已落地：

- 后端新增三模式配置中心（`realtime/intraday/longterm`），统一驱动：
  - K 线采样周期与样本数（`15m/1h/4h`）
  - 大单检测阈值（分位数/中位倍率/回看窗口）
  - 订单流强弱阈值（不平衡与主动买入比）
  - 阶段识别参数（吸筹/洗盘/拉升/出货）
- API 全链路支持 `trade_type` 参数，并新增 `/api/whale-analysis/trade-modes`。
- 前端 `WhaleAnalysis` 新增交易对 + 模式切换，自动刷新周期按模式动态调整。

## 7. 本次继续优化（预测 + 舆情）

### 7.1 高级预测

- 新增模式接口：`/api/advanced-prediction/trade-modes`
- 训练/预测/特征接口均支持 `trade_type`：
  - `realtime`(15m)、`intraday`(1h)、`longterm`(4h)
- 按 K 线粒度自动换算目标步长（例如 15m 下 24h=96 根 K 线）
- 模型命名空间改为 `symbol__trade_type`，避免不同模式训练结果互相覆盖
- 预测结果返回 `trade_type_label`、`interval`、`target_bars`，前端可直接解释“当前预测是基于哪种周期”

### 7.2 综合舆情

- 在 `full-analysis` 返回新增 `trend_forecast`
- 新增接口：`/api/comprehensive-sentiment/trend-forecast/{symbol}`
- 趋势预测采用 “线性趋势 + 24h 动量” 融合，输出：
  - `direction/direction_label`
  - `forecast_score`、`expected_fear_greed_index`
  - `confidence`、`drivers`
- 新增内存历史记录，用于连续调用时提升趋势判断稳定性
