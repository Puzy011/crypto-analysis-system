"""
多平台舆情定时调度服务

功能:
- 定时采集多平台消息（RSS 新闻、Reddit、Binance 公告）
- 统一结构化并进行 FinBERT 风格情感评分
- 生成平台分解指标与时间序列趋势（1h/4h/24h）
- 将快照落盘（jsonl）并保留内存历史
"""

import asyncio
import json
import math
import os
import re
from collections import Counter, defaultdict, deque
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import aiohttp
import numpy as np

from app.services.comprehensive_sentiment_service import (
    ComprehensiveSentimentService,
    get_comprehensive_sentiment_service,
)


class SentimentSchedulerService:
    """多平台舆情定时调度服务"""

    BINANCE_CMS_URL = (
        "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
    )

    def __init__(
        self,
        interval_seconds: int = 15 * 60,
        symbols: Optional[List[str]] = None,
        max_snapshots_per_symbol: int = 2000,
        data_dir: Optional[str] = None,
    ) -> None:
        self.interval_seconds = max(120, int(interval_seconds))
        self.symbols = [s.upper() for s in (symbols or ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"])]
        self.max_snapshots_per_symbol = max(100, int(max_snapshots_per_symbol))

        self.comprehensive_service: ComprehensiveSentimentService = (
            get_comprehensive_sentiment_service()
        )

        self.snapshots: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=self.max_snapshots_per_symbol)
        )
        self.latest_snapshot: Dict[str, Dict[str, Any]] = {}
        self.task: Optional[asyncio.Task] = None
        self.running = False
        self.last_run_at: Optional[str] = None
        self.last_error: Optional[str] = None

        self._lock = asyncio.Lock()

        backend_root = Path(__file__).resolve().parents[2]
        self.data_dir = Path(data_dir) if data_dir else (backend_root / "data" / "sentiment_scheduler")
        os.makedirs(self.data_dir, exist_ok=True)
        self.snapshots_file = self.data_dir / "multi_platform_snapshots.jsonl"

        self._load_snapshots_from_disk()

    async def start(self) -> None:
        """启动后台调度"""
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._run_loop(), name="sentiment-scheduler-loop")

    async def stop(self) -> None:
        """停止后台调度"""
        self.running = False
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
            self.task = None

    async def _run_loop(self) -> None:
        """后台循环"""
        while self.running:
            started = datetime.now(timezone.utc)
            try:
                results = await asyncio.gather(
                    *(self.collect_once(symbol, force_refresh=True) for symbol in self.symbols),
                    return_exceptions=True,
                )
                self.last_run_at = datetime.now(timezone.utc).isoformat()
                errors = [r for r in results if isinstance(r, Exception)]
                if errors:
                    first = errors[0]
                    self.last_error = f"{type(first).__name__}: {first}"
                else:
                    self.last_error = None
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"

            elapsed = (datetime.now(timezone.utc) - started).total_seconds()
            wait_seconds = max(10.0, float(self.interval_seconds) - elapsed)
            try:
                await asyncio.sleep(wait_seconds)
            except asyncio.CancelledError:
                break

    async def collect_once(
        self,
        symbol: str,
        force_refresh: bool = True,
    ) -> Dict[str, Any]:
        """手动/定时执行一次采集并返回快照"""
        normalized_symbol = symbol.upper()
        items = await self._collect_multi_platform_items(normalized_symbol, force_refresh=force_refresh)
        analyzed_items = self._analyze_items(items)
        snapshot = self._build_snapshot(normalized_symbol, analyzed_items)

        async with self._lock:
            self.latest_snapshot[normalized_symbol] = snapshot
            self.snapshots[normalized_symbol].append(snapshot)
            self._append_snapshot_to_disk(snapshot)

        return snapshot

    async def get_or_collect_latest(
        self,
        symbol: str,
        freshness_seconds: int = 20 * 60,
    ) -> Dict[str, Any]:
        """获取最新快照；超出新鲜度则触发采集"""
        normalized_symbol = symbol.upper()
        latest = self.latest_snapshot.get(normalized_symbol)
        if latest:
            now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
            age_ms = now_ts - int(latest.get("timestamp", now_ts))
            if age_ms <= max(60, int(freshness_seconds)) * 1000:
                return latest
        return await self.collect_once(normalized_symbol, force_refresh=True)

    def get_timeline(
        self,
        symbol: str,
        hours: int = 24,
        limit: int = 240,
    ) -> List[Dict[str, Any]]:
        """获取时间线数据"""
        normalized_symbol = symbol.upper()
        all_points = list(self.snapshots.get(normalized_symbol, []))
        if not all_points:
            return []

        now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        cutoff = now_ts - max(1, int(hours)) * 3600 * 1000
        points = [p for p in all_points if int(p.get("timestamp", 0)) >= cutoff]
        return points[-max(1, int(limit)) :]

    def analyze_timeline(self, symbol: str) -> Dict[str, Any]:
        """时间序列分析（1h/4h/24h）"""
        normalized_symbol = symbol.upper()
        points = list(self.snapshots.get(normalized_symbol, []))
        if not points:
            return {
                "symbol": normalized_symbol,
                "status": "no_data",
                "windows": {},
                "burst": {"score": 0.0, "is_spike": False},
                "data_points": 0,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        windows = {
            "1h": self._window_metrics(points, window_hours=1),
            "4h": self._window_metrics(points, window_hours=4),
            "24h": self._window_metrics(points, window_hours=24),
        }

        attention_series = [float(p.get("total_items", 0)) for p in points][-96:]
        burst = self._burst_metrics(attention_series)

        latest = points[-1]
        previous = points[-2] if len(points) >= 2 else None
        platform_momentum: Dict[str, float] = {}
        if previous:
            prev_breakdown = previous.get("platform_breakdown", {}) or {}
            cur_breakdown = latest.get("platform_breakdown", {}) or {}
            for platform in {"news", "reddit", "announcement"}:
                cur_score = float((cur_breakdown.get(platform) or {}).get("weighted_sentiment", 0.0))
                prev_score = float((prev_breakdown.get(platform) or {}).get("weighted_sentiment", 0.0))
                platform_momentum[platform] = float(cur_score - prev_score)

        return {
            "symbol": normalized_symbol,
            "status": "active",
            "windows": windows,
            "burst": burst,
            "platform_momentum": platform_momentum,
            "data_points": len(points),
            "latest_overall_score": float(latest.get("overall_sentiment_score", 0.0)),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_scheduler_status(self) -> Dict[str, Any]:
        """返回调度器状态"""
        return {
            "running": self.running,
            "interval_seconds": self.interval_seconds,
            "symbols": self.symbols,
            "last_run_at": self.last_run_at,
            "last_error": self.last_error,
            "loaded_points": {
                symbol: len(self.snapshots.get(symbol, []))
                for symbol in self.symbols
            },
            "latest_at": {
                symbol: (self.latest_snapshot.get(symbol) or {}).get("collected_at")
                for symbol in self.symbols
            },
        }

    async def _collect_multi_platform_items(
        self,
        symbol: str,
        force_refresh: bool = True,
    ) -> List[Dict[str, Any]]:
        """并行采集多平台消息并统一结构"""
        news_task = asyncio.to_thread(
            self.comprehensive_service.fetch_market_news,
            symbol,
            40,
            96,
            force_refresh,
        )
        reddit_task = self._fetch_reddit_posts(symbol, limit=30, hours=96)
        announce_task = self._fetch_binance_announcements(symbol, limit=40, hours=168)

        news_data, reddit_data, announcement_data = await asyncio.gather(
            news_task, reddit_task, announce_task, return_exceptions=True
        )

        if isinstance(news_data, Exception):
            news_data = []
        if isinstance(reddit_data, Exception):
            reddit_data = []
        if isinstance(announcement_data, Exception):
            announcement_data = []

        normalized_news = [
            {
                "id": n.get("id") or f"news_{idx}",
                "title": str(n.get("title", "")).strip(),
                "content": str(n.get("content", "")).strip(),
                "source": str(n.get("source", "News")).strip(),
                "platform": "news",
                "url": str(n.get("url", "")).strip(),
                "timestamp": int(n.get("timestamp", 0)),
                "symbol": symbol,
            }
            for idx, n in enumerate(news_data if isinstance(news_data, list) else [])
            if n.get("title")
        ]

        all_items = normalized_news + reddit_data + announcement_data

        # 去重: 同标题 + 小时桶
        dedup: Dict[str, Dict[str, Any]] = {}
        for item in all_items:
            title = str(item.get("title", "")).strip().lower()
            ts = int(item.get("timestamp", 0))
            bucket = ts // 3600000
            key = f"{re.sub(r'\\s+', ' ', title)}::{bucket}"
            previous = dedup.get(key)
            if previous is None or int(previous.get("timestamp", 0)) < ts:
                dedup[key] = item

        result = sorted(dedup.values(), key=lambda x: int(x.get("timestamp", 0)), reverse=True)
        return result[:120]

    def _analyze_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """对采集项进行情感分析"""
        analyzed: List[Dict[str, Any]] = []
        for item in items:
            merged_text = f"{item.get('title', '')} {item.get('content', '')}".strip()
            sentiment = self.comprehensive_service.analyze_financial_sentiment(merged_text)
            enriched = dict(item)
            enriched["sentiment_analysis"] = sentiment
            enriched["published_at"] = datetime.fromtimestamp(
                max(0, int(item.get("timestamp", 0))) / 1000,
                tz=timezone.utc,
            ).isoformat()
            analyzed.append(enriched)
        return analyzed

    def _build_snapshot(self, symbol: str, analyzed_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建单个 symbol 的多平台快照"""
        now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        platform_scores: Dict[str, List[float]] = defaultdict(list)
        platform_weighted: Dict[str, List[float]] = defaultdict(list)
        platform_weights: Dict[str, List[float]] = defaultdict(list)
        label_counter: Counter = Counter()
        weighted_sum = 0.0
        total_weight = 0.0

        platform_quality_weight = {
            "news": 1.0,
            "announcement": 0.95,
            "reddit": 0.82,
        }

        for item in analyzed_items:
            analysis = item.get("sentiment_analysis", {}) or {}
            score = float(analysis.get("sentiment_score", 0.0))
            label = str(analysis.get("sentiment_label", "neutral"))
            label_counter[label] += 1

            platform = str(item.get("platform", "news"))
            ts = int(item.get("timestamp", now_ts))
            age_hours = max(0.0, (now_ts - ts) / 3600000)
            time_weight = math.exp(-age_hours / 24.0)
            quality_weight = platform_quality_weight.get(platform, 0.8)
            weight = time_weight * quality_weight

            weighted_sum += score * weight
            total_weight += weight
            platform_scores[platform].append(score)
            platform_weighted[platform].append(score * weight)
            platform_weights[platform].append(weight)

        overall_score = float(weighted_sum / total_weight) if total_weight > 1e-9 else 0.0
        overall_score = float(max(-1.0, min(1.0, overall_score)))
        fear_greed = float(max(0.0, min(100.0, 50.0 + overall_score * 50.0)))

        platform_breakdown: Dict[str, Any] = {}
        for platform in ["news", "reddit", "announcement"]:
            scores = platform_scores.get(platform, [])
            if not scores:
                platform_breakdown[platform] = {
                    "count": 0,
                    "avg_sentiment": 0.0,
                    "weighted_sentiment": 0.0,
                    "positive_ratio": 0.0,
                    "negative_ratio": 0.0,
                }
                continue
            weights = platform_weights.get(platform, [])
            weighted_values = platform_weighted.get(platform, [])
            platform_weighted_score = (
                float(sum(weighted_values) / max(sum(weights), 1e-9))
                if weights
                else 0.0
            )
            positives = len([s for s in scores if s > 0.1])
            negatives = len([s for s in scores if s < -0.1])
            platform_breakdown[platform] = {
                "count": len(scores),
                "avg_sentiment": float(np.mean(scores)),
                "weighted_sentiment": float(platform_weighted_score),
                "positive_ratio": float(positives / len(scores)),
                "negative_ratio": float(negatives / len(scores)),
            }

        top_titles = [item.get("title", "") for item in analyzed_items[:30] if item.get("title")]
        top_keywords = [
            word
            for word, _score in self.comprehensive_service.extract_keywords_tfidf(top_titles, top_n=10)
        ]

        latest_ts = (
            max([int(item.get("timestamp", 0)) for item in analyzed_items]) if analyzed_items else now_ts
        )
        latest_age_min = max(0.0, (now_ts - latest_ts) / 60000.0)
        freshness_score = float(max(0.0, min(1.0, 1.0 - latest_age_min / 240.0)))
        coverage_score = float(
            len([p for p in platform_breakdown.values() if p.get("count", 0) > 0]) / 3.0
        )
        volume_score = float(max(0.0, min(1.0, len(analyzed_items) / 60.0)))
        quality_score = float(
            max(0.0, min(1.0, coverage_score * 0.45 + freshness_score * 0.30 + volume_score * 0.25))
        )

        headlines = [
            {
                "id": item.get("id"),
                "platform": item.get("platform"),
                "source": item.get("source"),
                "title": item.get("title"),
                "timestamp": int(item.get("timestamp", 0)),
                "sentiment_score": float(
                    (item.get("sentiment_analysis") or {}).get("sentiment_score", 0.0)
                ),
                "url": item.get("url", ""),
            }
            for item in analyzed_items[:12]
        ]

        return {
            "symbol": symbol,
            "timestamp": now_ts,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "overall_sentiment_score": overall_score,
            "fear_greed_index": fear_greed,
            "total_items": len(analyzed_items),
            "sentiment_distribution": dict(label_counter),
            "platform_breakdown": platform_breakdown,
            "top_keywords": top_keywords,
            "latest_headlines": headlines,
            "data_quality": {
                "coverage_score": coverage_score,
                "freshness_score": freshness_score,
                "volume_score": volume_score,
                "quality_score": quality_score,
                "latest_age_minutes": latest_age_min,
            },
        }

    async def _fetch_reddit_posts(
        self,
        symbol: str,
        limit: int = 30,
        hours: int = 96,
    ) -> List[Dict[str, Any]]:
        """抓取 Reddit 公开 JSON"""
        asset = self._extract_base_asset(symbol)
        aliases = self._asset_aliases(asset)
        cutoff_ts = int((datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp() * 1000)
        subreddits = self._subreddits_for_asset(asset)
        per_subreddit = max(8, min(30, int(limit)))

        results: List[Dict[str, Any]] = []
        headers = {"User-Agent": "Mozilla/5.0 (compatible; sentiment-scheduler/1.0)"}

        async with aiohttp.ClientSession(headers=headers) as session:
            for subreddit in subreddits:
                url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={per_subreddit}"
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status != 200:
                            continue
                        data = await response.json()
                except Exception:
                    continue

                for child in (((data or {}).get("data") or {}).get("children") or []):
                    post = (child or {}).get("data") or {}
                    title = str(post.get("title", "")).strip()
                    if not title:
                        continue
                    content = str(post.get("selftext", "")).strip()
                    merged = f"{title} {content}".lower()
                    if not self._is_text_relevant(merged, asset, aliases):
                        continue

                    ts = int(float(post.get("created_utc", 0)) * 1000)
                    if ts <= 0 or ts < cutoff_ts:
                        continue

                    post_id = str(post.get("name") or post.get("id") or "")
                    permalink = str(post.get("permalink", "")).strip()
                    url_path = str(post.get("url_overridden_by_dest", "")).strip()
                    if not url_path:
                        url_path = str(post.get("url", "")).strip()
                    if url_path.startswith("/"):
                        final_url = f"https://www.reddit.com{url_path}"
                    else:
                        final_url = url_path
                    if permalink and not final_url:
                        final_url = f"https://www.reddit.com{permalink}"

                    results.append(
                        {
                            "id": f"reddit_{post_id or ts}",
                            "title": title,
                            "content": content,
                            "source": f"Reddit/{subreddit}",
                            "platform": "reddit",
                            "url": final_url,
                            "timestamp": ts,
                            "symbol": symbol,
                        }
                    )

        # 去重 id
        unique: Dict[str, Dict[str, Any]] = {}
        for row in results:
            unique[row["id"]] = row
        ordered = sorted(unique.values(), key=lambda x: int(x.get("timestamp", 0)), reverse=True)
        return ordered[:limit]

    async def _fetch_binance_announcements(
        self,
        symbol: str,
        limit: int = 40,
        hours: int = 168,
    ) -> List[Dict[str, Any]]:
        """抓取 Binance 公告"""
        asset = self._extract_base_asset(symbol)
        aliases = self._asset_aliases(asset)
        cutoff_ts = int((datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp() * 1000)
        params = {"type": 1, "pageNo": 1, "pageSize": max(20, min(80, int(limit)))}
        headers = {"User-Agent": "Mozilla/5.0 (compatible; sentiment-scheduler/1.0)"}
        results: List[Dict[str, Any]] = []

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(self.BINANCE_CMS_URL, params=params, timeout=10) as response:
                    if response.status != 200:
                        return []
                    payload = await response.json()
        except Exception:
            return []

        catalogs = ((((payload or {}).get("data") or {}).get("catalogs")) or [])
        for catalog in catalogs:
            catalog_name = str(catalog.get("catalogName", "Binance")).strip()
            for article in catalog.get("articles", []) or []:
                title = str(article.get("title", "")).strip()
                if not title:
                    continue
                release_ts = int(article.get("releaseDate", 0) or 0)
                if release_ts <= 0 or release_ts < cutoff_ts:
                    continue
                lowered = title.lower()
                if not self._is_text_relevant(lowered, asset, aliases):
                    # 对交易规则变更类公告做通用保留，避免过滤过严
                    if not any(
                        key in lowered
                        for key in [
                            "listing",
                            "delist",
                            "futures",
                            "margin",
                            "maintenance",
                            "upgrade",
                            "launchpool",
                            "spot",
                            "api",
                            "trading pairs",
                        ]
                    ):
                        continue

                code = str(article.get("code", "")).strip()
                url = f"https://www.binance.com/en/support/announcement/{code}" if code else ""
                article_id = str(article.get("id", ""))
                results.append(
                    {
                        "id": f"binance_{article_id or release_ts}",
                        "title": title,
                        "content": title,
                        "source": f"Binance/{catalog_name}",
                        "platform": "announcement",
                        "url": url,
                        "timestamp": release_ts,
                        "symbol": symbol,
                    }
                )

        results.sort(key=lambda x: int(x.get("timestamp", 0)), reverse=True)
        return results[:limit]

    def _window_metrics(
        self,
        points: List[Dict[str, Any]],
        window_hours: int,
    ) -> Dict[str, Any]:
        """计算某个时间窗口的趋势指标"""
        now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        cutoff = now_ts - max(1, int(window_hours)) * 3600 * 1000
        window_points = [p for p in points if int(p.get("timestamp", 0)) >= cutoff]
        if len(window_points) < 2:
            last_score = float(window_points[-1].get("overall_sentiment_score", 0.0)) if window_points else 0.0
            return {
                "slope_per_hour": 0.0,
                "momentum": 0.0,
                "volatility": 0.0,
                "avg_attention": float(np.mean([p.get("total_items", 0) for p in window_points])) if window_points else 0.0,
                "trend_label": "insufficient_data",
                "last_score": last_score,
                "points": len(window_points),
            }

        ts_arr = np.array([float(p.get("timestamp", 0.0)) for p in window_points], dtype=float)
        score_arr = np.array(
            [float(p.get("overall_sentiment_score", 0.0)) for p in window_points], dtype=float
        )
        x_hours = (ts_arr - np.min(ts_arr)) / 3600000.0
        if np.max(x_hours) <= 1e-9:
            slope = 0.0
        else:
            slope, _intercept = np.polyfit(x_hours, score_arr, 1)
        slope = float(slope)
        momentum = float(score_arr[-1] - score_arr[0])
        volatility = float(np.std(score_arr))
        avg_attention = float(np.mean([float(p.get("total_items", 0)) for p in window_points]))

        if slope > 0.03:
            trend = "up_fast"
        elif slope > 0.01:
            trend = "up"
        elif slope < -0.03:
            trend = "down_fast"
        elif slope < -0.01:
            trend = "down"
        else:
            trend = "sideways"

        return {
            "slope_per_hour": slope,
            "momentum": momentum,
            "volatility": volatility,
            "avg_attention": avg_attention,
            "trend_label": trend,
            "last_score": float(score_arr[-1]),
            "points": len(window_points),
        }

    def _burst_metrics(self, attention_series: List[float]) -> Dict[str, Any]:
        """注意力突发检测"""
        if not attention_series:
            return {"score": 0.0, "is_spike": False, "latest": 0.0, "baseline": 0.0}
        latest = float(attention_series[-1])
        baseline_series = attention_series[:-1]
        if not baseline_series:
            return {"score": 0.0, "is_spike": False, "latest": latest, "baseline": latest}
        baseline = float(np.mean(baseline_series))
        std = float(np.std(baseline_series))
        score = float((latest - baseline) / (std + 1e-6))
        return {
            "score": score,
            "is_spike": bool(score > 2.0 and latest >= baseline + 3),
            "latest": latest,
            "baseline": baseline,
        }

    def _extract_base_asset(self, symbol: str) -> str:
        sym = symbol.upper().replace("-", "").replace("_", "")
        for suffix in ("USDT", "BUSD", "USDC", "USD", "BTC", "ETH"):
            if sym.endswith(suffix) and len(sym) > len(suffix):
                return sym[: -len(suffix)]
        return sym

    def _asset_aliases(self, asset: str) -> List[str]:
        alias_map = {
            "BTC": ["btc", "bitcoin", "比特币"],
            "ETH": ["eth", "ethereum", "以太坊"],
            "BNB": ["bnb", "binance coin", "币安币"],
            "SOL": ["sol", "solana"],
            "XRP": ["xrp", "ripple"],
            "ADA": ["ada", "cardano"],
            "DOGE": ["doge", "dogecoin"],
        }
        return alias_map.get(asset, [asset.lower()])

    def _subreddits_for_asset(self, asset: str) -> List[str]:
        mapping = {
            "BTC": ["Bitcoin", "CryptoCurrency", "CryptoMarkets"],
            "ETH": ["ethereum", "CryptoCurrency", "CryptoMarkets"],
            "BNB": ["binance", "CryptoCurrency", "CryptoMarkets"],
            "SOL": ["solana", "CryptoCurrency", "CryptoMarkets"],
            "XRP": ["Ripple", "CryptoCurrency", "CryptoMarkets"],
        }
        return mapping.get(asset, ["CryptoCurrency", "CryptoMarkets"])

    def _is_text_relevant(self, lowered_text: str, asset: str, aliases: List[str]) -> bool:
        if any(alias in lowered_text for alias in aliases):
            return True
        if asset in {"BTC", "ETH"} and any(
            key in lowered_text
            for key in ("crypto", "etf", "regulation", "stablecoin", "bitcoin", "ethereum")
        ):
            return True
        return False

    def _load_snapshots_from_disk(self) -> None:
        if not self.snapshots_file.exists():
            return
        try:
            with open(self.snapshots_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue
                    symbol = str(row.get("symbol", "")).upper()
                    if not symbol:
                        continue
                    self.snapshots[symbol].append(row)
                    self.latest_snapshot[symbol] = row
        except Exception:
            return

    def _append_snapshot_to_disk(self, snapshot: Dict[str, Any]) -> None:
        try:
            with open(self.snapshots_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
        except Exception:
            return


_sentiment_scheduler_service: Optional[SentimentSchedulerService] = None


def get_sentiment_scheduler_service() -> SentimentSchedulerService:
    global _sentiment_scheduler_service
    if _sentiment_scheduler_service is None:
        _sentiment_scheduler_service = SentimentSchedulerService()
    return _sentiment_scheduler_service
