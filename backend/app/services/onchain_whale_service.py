"""
链上巨鲸指标服务

基于公开 Ethereum JSON-RPC（无 API Key）计算：
- 交易所监控地址净流（Exchange Net Flow）
- 活跃地址近似（最近区块唯一地址）
- Gas 异常（base fee / priority fee）
- 监控地址余额集中度（Concentration）
"""

import asyncio
import statistics
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp


class OnchainWhaleService:
    """链上巨鲸指标服务"""

    def __init__(self) -> None:
        self.rpc_endpoints = [
            "https://eth.llamarpc.com",
            "https://ethereum-rpc.publicnode.com",
        ]

        # 已知交易所热钱包（公开标签常见地址）
        self.exchange_wallets: Dict[str, str] = {
            "binance_hot_1": "0x28c6c06298d514db089934071355e5743bf21d60",
            "binance_hot_2": "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
            "binance_hot_3": "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
            "coinbase_hot_1": "0x503828976d22510aad0201ac7ec88293211d23da",
            "coinbase_hot_2": "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740",
            "kraken_hot_1": "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0",
            "okx_hot_1": "0xa7efae728d2936e78bda97dc267687568dd593f3",
        }
        self.exchange_wallet_set = {addr.lower() for addr in self.exchange_wallets.values()}

        self.trade_type_block_window = {
            "realtime": 8,
            "intraday": 16,
            "longterm": 28,
        }
        self.trade_type_large_transfer_eth = {
            "realtime": 20.0,
            "intraday": 35.0,
            "longterm": 60.0,
        }

        self.supported_assets = {"ETH"}

        self.cache: Dict[str, Dict[str, Any]] = {}
        self.activity_history = defaultdict(lambda: deque(maxlen=80))

    async def get_onchain_metrics(
        self,
        symbol: str = "BTCUSDT",
        trade_type: str = "realtime",
    ) -> Dict[str, Any]:
        """获取链上真实指标"""
        mode = (trade_type or "realtime").lower()
        if mode not in self.trade_type_block_window:
            mode = "realtime"

        base_asset = self._extract_base_asset(symbol)
        if base_asset not in self.supported_assets:
            return self._empty_metrics(symbol, mode, reason="not_supported_asset", applicable=False)

        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            latest_hex = await self._rpc_call(session, "eth_blockNumber", [])
            if latest_hex is None:
                return self._empty_metrics(symbol, mode, reason="rpc_unavailable")
            latest_block = int(latest_hex, 16)

            cache_key = f"{mode}:{latest_block // 3}"
            cached = self.cache.get(cache_key)
            if cached:
                return cached

            block_count = int(self.trade_type_block_window[mode])
            start_block = max(0, latest_block - block_count + 1)
            blocks = await self._fetch_blocks(session, start_block, latest_block)
            if not blocks:
                return self._empty_metrics(symbol, mode, reason="no_blocks")

            exchange_flow = self._analyze_exchange_netflow(
                blocks=blocks,
                large_transfer_threshold_eth=self.trade_type_large_transfer_eth[mode],
            )
            activity = self._analyze_activity(blocks=blocks, trade_type=mode)
            gas = await self._analyze_gas(session)
            concentration = await self._analyze_balance_concentration(session)

            result = {
                "symbol": symbol.upper(),
                "trade_type": mode,
                "available": True,
                "source": "ethereum_jsonrpc_public",
                "rpc_endpoints": self.rpc_endpoints,
                "sample": {
                    "start_block": start_block,
                    "end_block": latest_block,
                    "block_count": len(blocks),
                },
                "exchange_netflow": exchange_flow,
                "activity": activity,
                "gas": gas,
                "holder_concentration": concentration,
                "updated_at": datetime.now().isoformat(),
            }
            self.cache[cache_key] = result
            return result

    async def _rpc_call(
        self,
        session: aiohttp.ClientSession,
        method: str,
        params: List[Any],
    ) -> Optional[Any]:
        for endpoint in self.rpc_endpoints:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": 1,
            }
            try:
                async with session.post(endpoint, json=payload) as response:
                    if response.status != 200:
                        continue
                    body = await response.json()
                    if body.get("result") is not None:
                        return body.get("result")
            except Exception:
                continue
        return None

    async def _fetch_blocks(
        self,
        session: aiohttp.ClientSession,
        start_block: int,
        end_block: int,
    ) -> List[Dict[str, Any]]:
        sem = asyncio.Semaphore(6)

        async def _one(block_number: int) -> Optional[Dict[str, Any]]:
            async with sem:
                block_hex = hex(block_number)
                result = await self._rpc_call(
                    session,
                    "eth_getBlockByNumber",
                    [block_hex, True],
                )
                if isinstance(result, dict):
                    return result
                return None

        tasks = [_one(n) for n in range(start_block, end_block + 1)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        blocks = [item for item in results if isinstance(item, dict)]
        blocks.sort(key=lambda x: int(str(x.get("number", "0x0")), 16))
        return blocks

    def _analyze_exchange_netflow(
        self,
        blocks: List[Dict[str, Any]],
        large_transfer_threshold_eth: float,
    ) -> Dict[str, Any]:
        inflow_eth = 0.0
        outflow_eth = 0.0
        inflow_count = 0
        outflow_count = 0
        large_transfer_count = 0
        transfers: List[Dict[str, Any]] = []

        for block in blocks:
            block_number = int(str(block.get("number", "0x0")), 16)
            ts = int(str(block.get("timestamp", "0x0")), 16)
            for tx in block.get("transactions", []) or []:
                from_addr = str(tx.get("from", "")).lower()
                to_addr = str(tx.get("to", "")).lower() if tx.get("to") else ""
                if from_addr not in self.exchange_wallet_set and to_addr not in self.exchange_wallet_set:
                    continue

                try:
                    value_eth = int(str(tx.get("value", "0x0")), 16) / 1e18
                except Exception:
                    value_eth = 0.0
                if value_eth <= 0:
                    continue

                if to_addr in self.exchange_wallet_set:
                    inflow_eth += value_eth
                    inflow_count += 1
                    direction = "inflow_to_exchange"
                else:
                    outflow_eth += value_eth
                    outflow_count += 1
                    direction = "outflow_from_exchange"

                if value_eth >= large_transfer_threshold_eth:
                    large_transfer_count += 1
                    transfers.append(
                        {
                            "hash": tx.get("hash"),
                            "block_number": block_number,
                            "timestamp": ts * 1000,
                            "from": from_addr,
                            "to": to_addr,
                            "value_eth": value_eth,
                            "direction": direction,
                        }
                    )

        transfers.sort(key=lambda x: x.get("value_eth", 0), reverse=True)
        net_flow_eth = float(inflow_eth - outflow_eth)
        if net_flow_eth > 0:
            direction = "inflow"
            direction_label = "净流入交易所（偏利空）"
        elif net_flow_eth < 0:
            direction = "outflow"
            direction_label = "净流出交易所（偏利多）"
        else:
            direction = "neutral"
            direction_label = "净流平衡"

        return {
            "inflow_eth": float(inflow_eth),
            "outflow_eth": float(outflow_eth),
            "net_flow_eth": net_flow_eth,
            "inflow_count": int(inflow_count),
            "outflow_count": int(outflow_count),
            "large_transfer_threshold_eth": float(large_transfer_threshold_eth),
            "large_transfer_count": int(large_transfer_count),
            "direction": direction,
            "direction_label": direction_label,
            "top_transfers": transfers[:10],
        }

    def _analyze_activity(
        self,
        blocks: List[Dict[str, Any]],
        trade_type: str,
    ) -> Dict[str, Any]:
        unique_addresses = set()
        tx_count = 0
        for block in blocks:
            for tx in block.get("transactions", []) or []:
                from_addr = str(tx.get("from", "")).lower()
                to_addr = str(tx.get("to", "")).lower() if tx.get("to") else ""
                if from_addr:
                    unique_addresses.add(from_addr)
                if to_addr:
                    unique_addresses.add(to_addr)
                tx_count += 1

        active_addresses = len(unique_addresses)
        hist = self.activity_history[trade_type]
        prev_avg = float(statistics.mean(hist)) if hist else 0.0
        change_pct = float((active_addresses - prev_avg) / (prev_avg + 1e-8)) if prev_avg > 0 else 0.0
        hist.append(active_addresses)

        return {
            "active_addresses": int(active_addresses),
            "sample_tx_count": int(tx_count),
            "active_addresses_change_pct": change_pct,
            "history_avg": prev_avg,
        }

    async def _analyze_gas(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        fee_history = await self._rpc_call(
            session,
            "eth_feeHistory",
            [24, "latest", [10, 50, 90]],
        )
        if not isinstance(fee_history, dict):
            return {
                "available": False,
                "base_fee_gwei": 0.0,
                "priority_fee_gwei": 0.0,
                "anomaly_zscore": 0.0,
                "anomaly_level": "unknown",
            }

        base_fees_hex = fee_history.get("baseFeePerGas", []) or []
        reward = fee_history.get("reward", []) or []
        if len(base_fees_hex) < 5:
            return {
                "available": False,
                "base_fee_gwei": 0.0,
                "priority_fee_gwei": 0.0,
                "anomaly_zscore": 0.0,
                "anomaly_level": "unknown",
            }

        base_fees = [int(x, 16) for x in base_fees_hex if isinstance(x, str)]
        latest_base = float(base_fees[-1])
        hist = base_fees[:-1]
        mean_base = float(statistics.mean(hist)) if hist else latest_base
        std_base = float(statistics.pstdev(hist)) if len(hist) > 2 else 0.0
        z = float((latest_base - mean_base) / (std_base + 1e-8)) if std_base > 0 else 0.0

        priority_samples = []
        for row in reward:
            if isinstance(row, list) and len(row) >= 2:
                try:
                    priority_samples.append(int(row[1], 16))
                except Exception:
                    continue
        priority_fee = float(statistics.median(priority_samples)) if priority_samples else 0.0

        if z > 1.8:
            level = "spike"
        elif z > 0.8:
            level = "elevated"
        elif z < -1.2:
            level = "low"
        else:
            level = "normal"

        return {
            "available": True,
            "base_fee_gwei": float(latest_base / 1e9),
            "base_fee_mean_gwei": float(mean_base / 1e9),
            "priority_fee_gwei": float(priority_fee / 1e9),
            "anomaly_zscore": z,
            "anomaly_level": level,
        }

    async def _analyze_balance_concentration(
        self,
        session: aiohttp.ClientSession,
    ) -> Dict[str, Any]:
        sem = asyncio.Semaphore(6)

        async def _get_balance(label: str, address: str) -> Optional[Dict[str, Any]]:
            async with sem:
                result = await self._rpc_call(
                    session,
                    "eth_getBalance",
                    [address, "latest"],
                )
                if result is None:
                    return None
                try:
                    balance_eth = int(str(result), 16) / 1e18
                except Exception:
                    balance_eth = 0.0
                return {"label": label, "address": address, "balance_eth": float(balance_eth)}

        tasks = [_get_balance(label, addr) for label, addr in self.exchange_wallets.items()]
        rows = await asyncio.gather(*tasks, return_exceptions=True)
        balances = [r for r in rows if isinstance(r, dict)]
        if not balances:
            return {
                "available": False,
                "tracked_addresses": 0,
                "total_balance_eth": 0.0,
                "top3_ratio": 0.0,
                "max_single_ratio": 0.0,
                "top_balances": [],
            }

        balances.sort(key=lambda x: x.get("balance_eth", 0.0), reverse=True)
        total_balance = float(sum(item["balance_eth"] for item in balances))
        top3 = float(sum(item["balance_eth"] for item in balances[:3]))
        top1 = float(balances[0]["balance_eth"]) if balances else 0.0

        return {
            "available": True,
            "tracked_addresses": len(balances),
            "total_balance_eth": total_balance,
            "top3_ratio": float(top3 / (total_balance + 1e-8)),
            "max_single_ratio": float(top1 / (total_balance + 1e-8)),
            "top_balances": balances[:6],
        }

    def _empty_metrics(self, symbol: str, trade_type: str, reason: str, applicable: bool = True) -> Dict[str, Any]:
        return {
            "symbol": symbol.upper(),
            "trade_type": trade_type,
            "available": False,
            "applicable": bool(applicable),
            "reason": reason,
            "exchange_netflow": {
                "inflow_eth": 0.0,
                "outflow_eth": 0.0,
                "net_flow_eth": 0.0,
                "direction": "neutral",
                "direction_label": "无数据",
                "large_transfer_threshold_eth": 0.0,
                "large_transfer_count": 0,
                "top_transfers": [],
            },
            "activity": {
                "active_addresses": 0,
                "sample_tx_count": 0,
                "active_addresses_change_pct": 0.0,
                "history_avg": 0.0,
            },
            "gas": {
                "available": False,
                "base_fee_gwei": 0.0,
                "priority_fee_gwei": 0.0,
                "anomaly_zscore": 0.0,
                "anomaly_level": "unknown",
            },
            "holder_concentration": {
                "available": False,
                "tracked_addresses": 0,
                "total_balance_eth": 0.0,
                "top3_ratio": 0.0,
                "max_single_ratio": 0.0,
                "top_balances": [],
            },
            "updated_at": datetime.now().isoformat(),
        }

    def _extract_base_asset(self, symbol: str) -> str:
        normalized = str(symbol or "").upper().replace("-", "").replace("_", "")
        for suffix in ("USDT", "USDC", "BUSD", "FDUSD", "TUSD", "BTC", "ETH"):
            if normalized.endswith(suffix) and len(normalized) > len(suffix):
                return normalized[: -len(suffix)]
        return normalized


_onchain_whale_service: Optional[OnchainWhaleService] = None


def get_onchain_whale_service() -> OnchainWhaleService:
    global _onchain_whale_service
    if _onchain_whale_service is None:
        _onchain_whale_service = OnchainWhaleService()
    return _onchain_whale_service
