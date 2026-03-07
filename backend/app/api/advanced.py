from fastapi import APIRouter, HTTPException
from app.services.enhanced_sentiment_service import EnhancedSentimentService
from app.services.backtest_service import BacktestService
from app.services.simulation_service import get_simulation_service
from app.services.multi_timeframe_service import MultiTimeframeService
from app.services.enhanced_prediction_service import EnhancedPredictionService

router = APIRouter()

# 服务实例
enhanced_sentiment_service = EnhancedSentimentService()
backtest_service = BacktestService()
simulation_service = get_simulation_service()
multi_timeframe_service = MultiTimeframeService()
enhanced_prediction_service = EnhancedPredictionService()


# ==================== 增强版舆情分析 ====================

@router.get("/sentiment/full/{keyword}")
async def get_full_sentiment(keyword: str = "crypto"):
    """获取全方面舆情分析"""
    try:
        analysis = enhanced_sentiment_service.analyze_full_sentiment(keyword)
        return {
            "success": True,
            "data": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 策略回测 ====================

@router.post("/backtest/run")
async def run_backtest(
    symbol: str = "BTCUSDT",
    initial_balance: float = 10000.0,
    commission: float = 0.001,
    slippage: float = 0.0005
):
    """运行策略回测"""
    try:
        result = backtest_service.run_backtest(
            symbol=symbol,
            initial_balance=initial_balance,
            commission=commission,
            slippage=slippage
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 模拟交易 ====================

@router.post("/simulation/account")
async def create_simulation_account(initial_balance: float = 10000.0, name: str = "模拟账户"):
    """创建模拟账户"""
    try:
        account_id = simulation_service.create_account(initial_balance, name)
        return {
            "success": True,
            "data": {"account_id": account_id}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulation/account/{account_id}")
async def get_simulation_account(account_id: str):
    """获取模拟账户信息"""
    try:
        account = simulation_service.get_account(account_id)
        if account:
            return {
                "success": True,
                "data": account
            }
        else:
            raise HTTPException(status_code=404, detail="账户不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulation/order")
async def place_simulation_order(
    account_id: str,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float = None
):
    """下单"""
    try:
        result = simulation_service.place_order(
            account_id=account_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "下单失败"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulation/trades/{account_id}")
async def get_simulation_trades(account_id: str, limit: int = 100):
    """获取交易历史"""
    try:
        trades = simulation_service.get_trades(account_id, limit)
        return {
            "success": True,
            "data": trades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulation/performance/{account_id}")
async def get_simulation_performance(account_id: str):
    """获取账户表现"""
    try:
        performance = simulation_service.get_performance(account_id)
        if performance:
            return {
                "success": True,
                "data": performance
            }
        else:
            raise HTTPException(status_code=404, detail="账户不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 多时间周期分析 ====================

@router.get("/multi-timeframe/{symbol}")
async def get_multi_timeframe_analysis(
    symbol: str,
    timeframes: str = "1m,5m,15m,1h,4h,1d"
):
    """多时间周期综合分析"""
    try:
        tf_list = timeframes.split(",")
        analysis = multi_timeframe_service.analyze_multi_timeframe(symbol, tf_list)
        return {
            "success": True,
            "data": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 增强版趋势预测 ====================

@router.get("/prediction/enhanced/{symbol}")
async def get_enhanced_prediction(symbol: str, timeframe: str = "1h"):
    """增强版趋势预测"""
    try:
        prediction = enhanced_prediction_service.predict_enhanced_trend(symbol, timeframe)
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查 ====================

@router.get("/ping")
async def ping():
    """测试接口"""
    return {
        "success": True,
        "message": "pong",
        "service": "advanced"
    }
