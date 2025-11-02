"""FastAPI backend for Quant Analytics Dashboard."""
import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import io
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import (
    AnalyticsResponse, AlertRuleRequest, AlertRuleResponse, 
    ConnectionStatusResponse, SampledWindowResponse
)
from backend.data_handler import BinanceWebSocketClient, TickBuffer, TickDatabase
from backend.analytics import AnalyticsEngine
from backend import utils

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Binance Live Quant Analytics",
    description="Real-time trading analytics with Binance WebSocket",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
ws_client: Optional[BinanceWebSocketClient] = None
tick_buffer = TickBuffer()
db = TickDatabase()
analytics_engine = AnalyticsEngine(window_size=60, max_history=500)
alert_rules: Dict[str, Dict] = {}
alert_history: List[Dict] = []

# Configuration
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
SAMPLING_INTERVAL = 5.0  # 5 seconds
MAX_ALERT_HISTORY = 1000


# ==============================================================================
# BACKGROUND TASKS
# ==============================================================================

async def websocket_task() -> None:
    """Run WebSocket connection in background."""
    global ws_client
    
    ws_client = BinanceWebSocketClient(symbols=[s.lower() for s in SYMBOLS])
    ws_client.on_tick = on_tick_received
    await ws_client.connect()


async def on_tick_received(tick) -> None:
    """Handle incoming tick from WebSocket."""
    tick_buffer.add(tick)
    db.insert_tick(tick)


async def sampling_task() -> None:
    """Sample buffers every 5 seconds and compute analytics."""
    while True:
        try:
            await asyncio.sleep(SAMPLING_INTERVAL)
            
            if not tick_buffer.should_flush():
                continue
            
            windows = tick_buffer.flush()
            
            for symbol, window in windows.items():
                # Save window to DB
                db.insert_window(window)
                
                # Compute analytics
                metrics = analytics_engine.process_window(window)
                db.insert_metrics(metrics)
                
                # Check alert rules
                check_alerts(metrics)
                
                logger.debug(f"✅ {symbol}: price={window.mean_price:.2f}, vol={window.total_volume:.2f}")
        
        except Exception as e:
            logger.error(f"Sampling task error: {e}")


async def cleanup_task() -> None:
    """Cleanup old data periodically."""
    while True:
        try:
            await asyncio.sleep(3600)  # Every hour
            db.cleanup_old_data(keep_days=7)
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")


def check_alerts(metrics) -> None:
    """Check if any alert rules are triggered."""
    for rule_id, rule in alert_rules.items():
        if not rule["enabled"]:
            continue
        
        symbol = rule["symbol"]
        metric_name = rule["metric"]
        condition = rule["condition"]
        threshold = rule["threshold"]
        
        # Get metric value
        actual_value = None
        if metric_name == "z_score":
            actual_value = metrics.z_score
        elif metric_name == "volatility":
            actual_value = metrics.volatility
        elif metric_name == "price":
            actual_value = metrics.mean_price
        elif metric_name == "rsi":
            actual_value = metrics.rsi
        
        if actual_value is None:
            continue
        
        # Check condition
        triggered = utils.check_alert_condition(actual_value, condition, threshold)
        
        if triggered:
            rule["triggered_count"] += 1
            
            alert_event = {
                "rule_id": rule_id,
                "timestamp": time.time() * 1000,
                "symbol": symbol,
                "metric": metric_name,
                "actual_value": actual_value,
                "threshold": threshold,
            }
            alert_history.append(alert_event)
            
            # Keep history size bounded
            if len(alert_history) > MAX_ALERT_HISTORY:
                alert_history.pop(0)
            
            logger.warning(f"🚨 Alert triggered: {rule_id} - {metric_name} {condition} {threshold} (actual: {actual_value:.4f})")


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup."""
    logger.info("🚀 Starting backend services...")
    
    # Load alerts from database
    load_alerts_from_db()
    
    # Start background tasks
    asyncio.create_task(websocket_task())
    asyncio.create_task(sampling_task())
    asyncio.create_task(cleanup_task())


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/status", response_model=ConnectionStatusResponse, tags=["Status"])
async def get_status():
    """Get connection and system status."""
    if ws_client is None:
        return ConnectionStatusResponse(
            status="disconnected",
            uptime_seconds=0,
            ticks_received=0,
            last_tick_timestamp=None
        )
    
    return ConnectionStatusResponse(
        status="connected" if ws_client.is_connected else "connecting",
        uptime_seconds=ws_client.get_uptime(),
        ticks_received=ws_client.ticks_received,
        last_tick_timestamp=ws_client.last_tick_timestamp
    )


@app.get("/ticks/latest", response_model=List[SampledWindowResponse], tags=["Data"])
async def get_latest_ticks(symbol: str = "BTCUSDT", limit: int = 50):
    """Get latest sampled tick windows."""
    windows = db.get_recent_windows(symbol, limit)
    
    return [
        SampledWindowResponse(
            timestamp=w.timestamp,
            symbol=w.symbol,
            mean_price=w.mean_price,
            std_price=w.std_price,
            min_price=w.min_price,
            max_price=w.max_price,
            total_volume=w.total_volume,
            tick_count=w.tick_count,
            vwap=w.vwap,
        )
        for w in windows
    ]


@app.get("/analytics", response_model=Dict[str, AnalyticsResponse], tags=["Analytics"])
async def get_analytics():
    """Get latest analytics for all symbols."""
    metrics_dict = analytics_engine.get_all_metrics()
    
    response = {}
    for symbol, metrics in metrics_dict.items():
        response[symbol] = AnalyticsResponse(
            timestamp=metrics.timestamp,
            symbol=metrics.symbol,
            mean_price=metrics.mean_price,
            std_price=metrics.std_price,
            volatility=metrics.volatility,
            z_score=metrics.z_score,
            sma_20=metrics.sma_20,
            ema_20=metrics.ema_20,
            rsi=metrics.rsi,
            correlation_btc_eth=metrics.correlation_btc_eth,
            garch_forecast=metrics.garch_forecast,
            adf_pvalue=metrics.adf_pvalue,
            trend=metrics.trend,
        )
    
    return response


@app.get("/analytics/{symbol}", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_symbol_analytics(symbol: str):
    """Get latest analytics for specific symbol."""
    metrics = analytics_engine.get_metrics(symbol.upper())
    
    if not metrics:
        raise HTTPException(status_code=404, detail=f"No metrics for {symbol}")
    
    return AnalyticsResponse(
        timestamp=metrics.timestamp,
        symbol=metrics.symbol,
        mean_price=metrics.mean_price,
        std_price=metrics.std_price,
        volatility=metrics.volatility,
        z_score=metrics.z_score,
        sma_20=metrics.sma_20,
        ema_20=metrics.ema_20,
        rsi=metrics.rsi,
        correlation_btc_eth=metrics.correlation_btc_eth,
        garch_forecast=metrics.garch_forecast,
        adf_pvalue=metrics.adf_pvalue,
        trend=metrics.trend,
    )


@app.get("/price-history/{symbol}", tags=["Analytics"])
async def get_price_history(symbol: str, limit: int = 100):
    """Get price history for symbol."""
    history = analytics_engine.get_price_history(symbol.upper(), limit)
    
    return {
        "symbol": symbol.upper(),
        "count": len(history),
        "prices": history
    }


@app.get("/correlations", tags=["Analytics"])
async def get_correlations():
    """Get correlation matrix between symbols."""
    corr_matrix = analytics_engine.get_correlation_matrix()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "correlations": corr_matrix
    }


@app.get("/clustering", tags=["Analytics"])
async def get_clustering():
    """Cluster symbols by correlation."""
    clusters = analytics_engine.cluster_by_correlation(min_correlation=0.7)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "clusters": clusters
    }


@app.get("/backtest/{symbol}", tags=["Analytics"])
async def backtest_symbol(symbol: str):
    """Run mean-reversion backtest."""
    result = analytics_engine.backtest_mean_reversion(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "timestamp": datetime.utcnow().isoformat(),
        **result
    }


# ==============================================================================
# ALERT ENDPOINTS
# ==============================================================================

@app.post("/alerts/rules", response_model=AlertRuleResponse, tags=["Alerts"])
async def create_alert_rule(request: AlertRuleRequest):
    """Create a new alert rule."""
    rule_id = str(uuid.uuid4())
    
    rule = {
        "rule_id": rule_id,
        "symbol": request.symbol,
        "metric": request.metric,
        "condition": request.condition,
        "threshold": request.threshold,
        "enabled": request.enabled,
        "triggered_count": 0,
    }
    
    alert_rules[rule_id] = rule
    save_alerts_to_db()
    
    logger.info(f"✅ Alert rule created: {rule_id}")
    
    return AlertRuleResponse(**rule)


@app.get("/alerts/rules", response_model=List[AlertRuleResponse], tags=["Alerts"])
async def list_alert_rules():
    """List all alert rules."""
    return [AlertRuleResponse(**rule) for rule in alert_rules.values()]


@app.put("/alerts/rules/{rule_id}", response_model=AlertRuleResponse, tags=["Alerts"])
async def update_alert_rule(rule_id: str, request: AlertRuleRequest):
    """Update an alert rule."""
    if rule_id not in alert_rules:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    alert_rules[rule_id].update({
        "symbol": request.symbol,
        "metric": request.metric,
        "condition": request.condition,
        "threshold": request.threshold,
        "enabled": request.enabled,
    })
    
    save_alerts_to_db()
    
    return AlertRuleResponse(**alert_rules[rule_id])


@app.delete("/alerts/rules/{rule_id}", tags=["Alerts"])
async def delete_alert_rule(rule_id: str):
    """Delete an alert rule."""
    if rule_id not in alert_rules:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    del alert_rules[rule_id]
    save_alerts_to_db()
    
    return {"message": "Alert rule deleted"}


@app.get("/alerts/history", tags=["Alerts"])
async def get_alert_history(limit: int = 100):
    """Get alert trigger history."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(alert_history),
        "alerts": alert_history[-limit:]
    }


# ==============================================================================
# EXPORT ENDPOINTS
# ==============================================================================

@app.get("/export/csv", tags=["Export"])
async def export_csv(symbol: str = "BTCUSDT", hours: int = 1):
    """Export analytics as CSV."""
    csv_data = db.export_to_csv(symbol.upper(), hours)
    
    filename = f"{symbol}_analytics_{datetime.utcnow().isoformat()}.csv"
    
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def save_alerts_to_db() -> None:
    """Save alerts to database."""
    try:
        import sqlite3
        conn = sqlite3.connect("data/ticks.db")
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM alerts")
        
        for rule_id, rule in alert_rules.items():
            cursor.execute("""
                INSERT INTO alerts 
                (rule_id, symbol, metric, condition, threshold, enabled, triggered_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule["rule_id"],
                rule["symbol"],
                rule["metric"],
                rule["condition"],
                rule["threshold"],
                rule["enabled"],
                rule["triggered_count"],
                time.time() * 1000
            ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to save alerts: {e}")


def load_alerts_from_db() -> None:
    """Load alerts from database."""
    try:
        import sqlite3
        conn = sqlite3.connect("data/ticks.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM alerts")
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            rule_id, symbol, metric, condition, threshold, enabled, triggered_count, _ = row[1:]
            alert_rules[rule_id] = {
                "rule_id": rule_id,
                "symbol": symbol,
                "metric": metric,
                "condition": condition,
                "threshold": threshold,
                "enabled": bool(enabled),
                "triggered_count": triggered_count,
            }
        
        logger.info(f"Loaded {len(alert_rules)} alert rules from database")
    except Exception as e:
        logger.error(f"Failed to load alerts: {e}")


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Binance Live Quant Analytics - Backend")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
