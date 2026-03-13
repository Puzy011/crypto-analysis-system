# 庄家分析功能优化方案（2026-03-12）

## 📋 现状分析

### 当前系统优势
1. ✅ 完整的订单流分析（order flow imbalance）
2. ✅ 大单检测与追踪（large orders detection）
3. ✅ 阶段识别（accumulation/distribution/pump/washout）
4. ✅ 合约衍生指标（funding rate, OI, long/short ratio）
5. ✅ 链上数据集成（onchain metrics）

### 核心问题
1. ❌ **缺少"聪明钱"真实数据** - 无法获取交易员级别持仓、盈亏、巨鲸数量
2. ❌ **成本带分析不够精细** - 缺少 Volume Profile、POC（Point of Control）
3. ❌ **大户追踪不够智能** - 无法识别"持续性大户"vs"一次性大单"
4. ❌ **市场微观结构指标缺失** - 缺少 Order Book Imbalance、Liquidity Heatmap
5. ❌ **输出结构不够直观** - 缺少"报告式"呈现

---

## 🎯 优化方案（分 4 个层级）

### Layer 1: 增强大户追踪与聪明钱估算（核心优先级 P0）

#### 1.1 大户持续性追踪
**目标**: 识别"持续建仓的大户" vs "一次性大单"

**实现方法**:
```python
# 在 whale_analysis_service.py 中添加
def track_persistent_whales(self, symbol: str, trades: List[Dict], window_minutes: int = 60):
    """
    追踪持续性大户行为
    - 识别在时间窗口内多次出现的大单地址特征
    - 计算大户"累积建仓量"
    """
    # 1. 按价格区间分组大单
    # 2. 识别"同一价格区间内的重复大单"
    # 3. 计算累积建仓强度
    pass
```

**数据来源**:
- Binance aggTrades（已有）
- 按 price、amount、timestamp 聚类分析

**输出指标**:
- `persistent_whale_score`: 持续性大户强度（0-100）
- `accumulation_zones`: 建仓密集区间
- `whale_cost_basis`: 估算大户成本价

---

#### 1.2 聪明钱估算（无私有数据版本）
**目标**: 在无法获取真实交易员数据时，提供"可解释的估算版"

**实现方法**:
```python
def estimate_smart_money_distribution(self, symbol: str, trades: List[Dict], klines: pd.DataFrame):
    """
    基于订单流 + 大单 + 价格行为估算聪明钱分布
    """
    # 1. 识别"逆势大单"（价格下跌时大额买入 = 聪明钱）
    # 2. 计算"大单胜率"（大单后价格是否朝大单方向移动）
    # 3. 估算"聪明钱持仓占比"

    return {
        "estimated_smart_money_long_pct": 0.65,  # 估算多头聪明钱占比
        "estimated_smart_money_short_pct": 0.35,
        "smart_money_win_rate": 0.72,  # 聪明钱胜率
        "confidence": "estimated",  # 标注为估算值
    }
```

**关键逻辑**:
- **逆势大单 = 聪明钱**: 价格下跌时出现大额买单 → 可能是聪明钱抄底
- **大单胜率**: 统计大单后 5/15/30 分钟价格变化，计算胜率
- **持仓估算**: 基于大单累积量 / 24h 总成交量

---

### Layer 2: 成本带与建仓成本分析（P0）

#### 2.1 Volume Profile（成交量分布）
**目标**: 识别"成交密集区"作为支撑/阻力位

**实现方法**:
```python
def calculate_volume_profile(self, klines: pd.DataFrame, bins: int = 50):
    """
    计算 Volume Profile
    - 将价格区间分成 N 个 bins
    - 统计每个 bin 的成交量
    - 识别 POC（Point of Control，成交量最大的价格）
    """
    price_min = klines['low'].min()
    price_max = klines['high'].max()
    price_bins = np.linspace(price_min, price_max, bins)

    volume_profile = []
    for i in range(len(price_bins) - 1):
        bin_low = price_bins[i]
        bin_high = price_bins[i + 1]
        # 统计该价格区间的成交量
        mask = (klines['low'] <= bin_high) & (klines['high'] >= bin_low)
        volume = klines.loc[mask, 'volume'].sum()
        volume_profile.append({
            'price_low': bin_low,
            'price_high': bin_high,
            'volume': volume,
        })

    # 找到 POC
    poc = max(volume_profile, key=lambda x: x['volume'])

    return {
        'volume_profile': volume_profile,
        'poc_price': (poc['price_low'] + poc['price_high']) / 2,
        'value_area_high': ...,  # 70% 成交量的上界
        'value_area_low': ...,   # 70% 成交量的下界
    }
```

**输出指标**:
- `poc_price`: 成交量最大的价格（关键支撑/阻力）
- `value_area_high/low`: 70% 成交量区间（主力成本带）
- `volume_profile`: 完整的成交量分布图

---

#### 2.2 建仓成本估算
**目标**: 估算"主力平均建仓成本"

**实现方法**:
```python
def estimate_whale_cost_basis(self, trades: List[Dict], large_orders: Dict):
    """
    基于大单加权平均价格估算主力成本
    """
    large_buy_orders = [t for t in large_orders['large_orders'] if t['side'] == 'buy']

    if not large_buy_orders:
        return None

    total_amount = sum(o['amount'] for o in large_buy_orders)
    weighted_price = sum(o['price'] * o['amount'] for o in large_buy_orders) / total_amount

    return {
        'whale_cost_basis': weighted_price,
        'total_whale_volume': total_amount,
        'sample_size': len(large_buy_orders),
    }
```

---

### Layer 3: 市场微观结构指标（P1）

#### 3.1 Order Book Imbalance（订单簿不平衡）
**目标**: 实时监控买卖盘力量对比

**实现方法**:
```python
def calculate_order_book_imbalance(self, order_book: Dict, depth_levels: int = 10):
    """
    计算订单簿不平衡度
    - 取前 N 档买卖盘
    - 计算买卖盘量差
    """
    bids = order_book['bids'][:depth_levels]
    asks = order_book['asks'][:depth_levels]

    bid_volume = sum(b['amount'] for b in bids)
    ask_volume = sum(a['amount'] for a in asks)

    imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)

    return {
        'order_book_imbalance': imbalance,  # -1 到 1
        'bid_volume': bid_volume,
        'ask_volume': ask_volume,
        'interpretation': 'bullish' if imbalance > 0.2 else 'bearish' if imbalance < -0.2 else 'neutral',
    }
```

**关键指标**:
- `order_book_imbalance > 0.3`: 买盘压倒性优势
- `order_book_imbalance < -0.3`: 卖盘压倒性优势

---

#### 3.2 Liquidity Heatmap（流动性热力图）
**目标**: 识别"大额挂单墙"（可能是主力诱导）

**实现方法**:
```python
def detect_liquidity_walls(self, order_book: Dict, threshold_multiplier: float = 3.0):
    """
    检测订单簿中的"异常大单墙"
    """
    bids = order_book['bids']
    asks = order_book['asks']

    # 计算平均挂单量
    avg_bid_size = np.mean([b['amount'] for b in bids])
    avg_ask_size = np.mean([a['amount'] for a in asks])

    # 识别异常大单
    bid_walls = [b for b in bids if b['amount'] > avg_bid_size * threshold_multiplier]
    ask_walls = [a for a in asks if a['amount'] > avg_ask_size * threshold_multiplier]

    return {
        'bid_walls': bid_walls,  # 买盘大单墙
        'ask_walls': ask_walls,  # 卖盘大单墙
        'interpretation': '卖盘有大单墙，可能是主力压盘' if ask_walls else '',
    }
```

---

### Layer 4: 输出结构优化（P1）

#### 4.1 对齐 Aice100 风格的"报告式"输出

**目标**: 让输出更直观、更易理解

**优化后的输出结构**:
```json
{
  "report": {
    "whale_direction": "多头主导",
    "whale_action": "持续建仓",
    "trade_advice": "回调至 0.85 附近可轻仓做多",
    "risk_control": "止损 0.82，止盈 0.95",
    "confidence": 0.78
  },
  "smart_money_distribution": {
    "estimated_long_pct": 0.65,
    "estimated_short_pct": 0.35,
    "smart_money_win_rate": 0.72,
    "confidence": "estimated"
  },
  "cost_analysis": {
    "whale_cost_basis": 0.87,
    "poc_price": 0.86,
    "value_area_high": 0.92,
    "value_area_low": 0.83
  },
  "microstructure": {
    "order_book_imbalance": 0.35,
    "bid_walls": [...],
    "ask_walls": [...]
  },
  "signal_explanation": [
    "大单持续流入，累积建仓量达 24h 成交量的 12%",
    "订单簿买盘优势明显（imbalance = 0.35）",
    "价格接近 POC（0.86），支撑较强"
  ]
}
```

---

## 🚀 实施计划

### 第 1 周（P0 核心功能）
1. ✅ 添加 `track_persistent_whales()` - 持续性大户追踪
2. ✅ 添加 `estimate_smart_money_distribution()` - 聪明钱估算
3. ✅ 添加 `calculate_volume_profile()` - Volume Profile
4. ✅ 添加 `estimate_whale_cost_basis()` - 建仓成本估算

### 第 2 周（P1 微观结构）
5. ✅ 添加 `calculate_order_book_imbalance()` - 订单簿不平衡
6. ✅ 添加 `detect_liquidity_walls()` - 流动性墙检测
7. ✅ 优化输出结构，对齐 Aice100 风格

### 第 3 周（测试与优化）
8. ✅ 回测验证各指标有效性
9. ✅ 前端对接与可视化
10. ✅ 文档与使用说明

---

## 📊 关键指标说明

### 1. 持续性大户强度（Persistent Whale Score）
- **计算方法**: 统计时间窗口内"同价格区间的重复大单"
- **阈值**: > 60 表示有持续建仓行为
- **用途**: 区分"一次性大单"和"持续建仓"

### 2. 聪明钱胜率（Smart Money Win Rate）
- **计算方法**: 统计大单后 5/15/30 分钟价格是否朝大单方向移动
- **阈值**: > 65% 表示聪明钱
- **用途**: 验证大单是否真的"聪明"

### 3. POC 价格（Point of Control）
- **计算方法**: Volume Profile 中成交量最大的价格
- **用途**: 关键支撑/阻力位，主力成本密集区

### 4. 订单簿不平衡（Order Book Imbalance）
- **计算方法**: (买盘量 - 卖盘量) / (买盘量 + 卖盘量)
- **阈值**: > 0.3 多头优势，< -0.3 空头优势
- **用途**: 实时监控买卖盘力量

---

## 🎯 RIVERUSDT 支持

RIVERUSDT 是 Binance 合约市场的新币种，系统已支持，无需额外配置。

**使用方法**:
```bash
# API 调用
GET /api/whale-analysis/full/RIVERUSDT?market_type=futures&trade_type=realtime
```

---

## 📚 参考资料

1. **Order Flow Analysis**: Wyckoff Method, Volume Spread Analysis
2. **Volume Profile**: Market Profile, TPO Charts
3. **Smart Money Concepts**: ICT (Inner Circle Trader), SMC Trading
4. **Microstructure**: Order Book Dynamics, Liquidity Analysis

---

## ⚠️ 重要说明

1. **聪明钱数据为估算值**: 由于无法获取真实交易员数据，所有"聪明钱"指标均为基于订单流和大单行为的估算
2. **需要配合其他指标**: 庄家分析不应单独使用，需结合技术分析、基本面分析
3. **回测验证**: 所有新增指标需要回测验证有效性

---

**生成时间**: 2026-03-12
**版本**: v1.0
**作者**: Crypto Analysis System Team
