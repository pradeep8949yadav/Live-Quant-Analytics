"""Binance WebSocket data ingestion and SQLite persistence."""
import asyncio
import json
import logging
import sqlite3
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
import aiohttp
import numpy as np

from backend.models import Tick, SampledWindow
from backend import utils

logger = logging.getLogger(__name__)

DB_PATH = "data/ticks.db"
BINANCE_WS_URL = "wss://fstream.binance.com/ws"


class BinanceWebSocketClient:
    """Connect to Binance Futures WebSocket and ingest tick data."""
    
    def __init__(self, symbols: List[str] = None):
        """
        Args:
            symbols: List of symbols (e.g., ['btcusdt', 'ethusdt'])
        """
        self.symbols = symbols or ["btcusdt", "ethusdt"]
        self.ws = None
        self.session = None
        self.is_connected = False
        self.connect_time = None
        self.ticks_received = 0
        self.last_tick_timestamp = None
        self.on_tick: Optional[Callable] = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
    
    async def connect(self) -> None:
        """Establish WebSocket connection with reconnection logic."""
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.session = aiohttp.ClientSession()
                
                # Build combined stream URL
                streams = "/".join([f"{sym}@aggTrade" for sym in self.symbols])
                url = f"{BINANCE_WS_URL}/{streams}"
                
                logger.info(f"Connecting to {url}")
                self.ws = await self.session.ws_connect(url)
                
                self.is_connected = True
                self.reconnect_attempts = 0
                self.connect_time = time.time()
                logger.info("✅ Binance WebSocket connected!")
                
                await self._listen()
                
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.is_connected = False
                self.reconnect_attempts += 1
                
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    logger.error("Max reconnection attempts reached!")
                    break
                
                wait_time = utils.exponential_backoff(self.reconnect_attempts)
                logger.info(f"Reconnecting in {wait_time:.1f}s (attempt {self.reconnect_attempts})")
                await asyncio.sleep(wait_time)
            
            finally:
                if self.session:
                    await self.session.close()
    
    async def _listen(self) -> None:
        """Listen to incoming WebSocket messages."""
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {msg}")
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.warning("WebSocket closed")
                    break
        except Exception as e:
            logger.error(f"Listen error: {e}")
    
    async def _handle_message(self, data: str) -> None:
        """Parse and handle incoming trade message."""
        try:
            msg = json.loads(data)
            
            # Binance aggTrade format
            if "s" in msg and "p" in msg and "q" in msg:
                symbol = msg["s"].upper()
                price = float(msg["p"])
                quantity = float(msg["q"])
                timestamp = msg.get("T", int(time.time() * 1000))
                
                tick = Tick(
                    timestamp=timestamp,
                    symbol=symbol,
                    price=price,
                    quantity=quantity,
                )
                
                self.ticks_received += 1
                self.last_tick_timestamp = timestamp
                
                if self.on_tick:
                    await self.on_tick(tick)
        
        except Exception as e:
            logger.debug(f"Message parse error: {e}")
    
    def get_uptime(self) -> float:
        """Get connection uptime in seconds."""
        if self.connect_time is None:
            return 0.0
        return time.time() - self.connect_time
    
    async def close(self) -> None:
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
        self.is_connected = False


class TickBuffer:
    """Buffer for 5-second tick aggregation."""
    
    def __init__(self):
        self.buffer: Dict[str, List[Tick]] = {}
        self.last_flush = time.time()
    
    def add(self, tick: Tick) -> None:
        """Add tick to buffer."""
        if tick.symbol not in self.buffer:
            self.buffer[tick.symbol] = []
        self.buffer[tick.symbol].append(tick)
    
    def should_flush(self, interval_ms: int = 5000) -> bool:
        """Check if buffer should be flushed."""
        elapsed = (time.time() - self.last_flush) * 1000
        return elapsed >= interval_ms
    
    def flush(self) -> Dict[str, SampledWindow]:
        """Aggregate and return sampled windows."""
        windows = {}
        current_time = time.time() * 1000
        
        for symbol, ticks in self.buffer.items():
            if not ticks:
                continue
            
            prices = [t.price for t in ticks]
            quantities = [t.quantity for t in ticks]
            
            mean_price = utils.calculate_mean(prices)
            std_price = utils.calculate_std(prices, mean_price)
            min_price = min(prices)
            max_price = max(prices)
            total_volume = sum(quantities)
            vwap = utils.calculate_vwap(prices, quantities)
            
            window = SampledWindow(
                timestamp=current_time,
                symbol=symbol,
                mean_price=mean_price,
                std_price=std_price,
                min_price=min_price,
                max_price=max_price,
                total_volume=total_volume,
                tick_count=len(ticks),
                vwap=vwap,
            )
            
            windows[symbol] = window
        
        self.buffer = {}
        self.last_flush = time.time()
        return windows


class TickDatabase:
    """SQLite database for tick persistence."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Raw ticks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                iso_timestamp TEXT NOT NULL
            )
        """)
        
        # Sampled windows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sampled_windows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                mean_price REAL NOT NULL,
                std_price REAL NOT NULL,
                min_price REAL NOT NULL,
                max_price REAL NOT NULL,
                total_volume REAL NOT NULL,
                tick_count INTEGER NOT NULL,
                vwap REAL NOT NULL
            )
        """)
        
        # Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                mean_price REAL NOT NULL,
                std_price REAL NOT NULL,
                volatility REAL NOT NULL,
                z_score REAL NOT NULL,
                sma_20 REAL NOT NULL,
                ema_20 REAL NOT NULL,
                rsi REAL NOT NULL,
                correlation_btc_eth REAL,
                garch_forecast REAL,
                adf_pvalue REAL,
                trend TEXT NOT NULL
            )
        """)
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                metric TEXT NOT NULL,
                condition TEXT NOT NULL,
                threshold REAL NOT NULL,
                enabled INTEGER NOT NULL,
                triggered_count INTEGER NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        
        # Alert triggers log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                symbol TEXT NOT NULL,
                metric TEXT NOT NULL,
                actual_value REAL NOT NULL,
                threshold REAL NOT NULL
            )
        """)
        
        # Create indices for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticks_timestamp ON ticks(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticks_symbol ON ticks(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_windows_timestamp ON sampled_windows(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Database initialized: {self.db_path}")
    
    def insert_tick(self, tick: Tick) -> None:
        """Insert raw tick."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ticks (timestamp, symbol, price, quantity, iso_timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (tick.timestamp, tick.symbol, tick.price, tick.quantity, tick.iso_timestamp))
        
        conn.commit()
        conn.close()
    
    def insert_window(self, window: SampledWindow) -> None:
        """Insert sampled window."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sampled_windows 
            (timestamp, symbol, mean_price, std_price, min_price, max_price, total_volume, tick_count, vwap)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (window.timestamp, window.symbol, window.mean_price, window.std_price,
              window.min_price, window.max_price, window.total_volume, window.tick_count, window.vwap))
        
        conn.commit()
        conn.close()
    
    def insert_metrics(self, metrics) -> None:
        """Insert analytics metrics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO metrics
            (timestamp, symbol, mean_price, std_price, volatility, z_score, sma_20, ema_20, rsi,
             correlation_btc_eth, garch_forecast, adf_pvalue, trend)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (metrics.timestamp, metrics.symbol, metrics.mean_price, metrics.std_price,
              metrics.volatility, metrics.z_score, metrics.sma_20, metrics.ema_20, metrics.rsi,
              metrics.correlation_btc_eth, metrics.garch_forecast, metrics.adf_pvalue, metrics.trend))
        
        conn.commit()
        conn.close()
    
    def get_recent_windows(self, symbol: str, limit: int = 100) -> List[SampledWindow]:
        """Get recent sampled windows."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, symbol, mean_price, std_price, min_price, max_price, total_volume, tick_count, vwap
            FROM sampled_windows
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (symbol, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [SampledWindow(*row) for row in rows[::-1]]
    
    def export_to_csv(self, symbol: str, hours: int = 1) -> str:
        """Export metrics to CSV."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = time.time() * 1000 - (hours * 3600 * 1000)
        
        cursor.execute("""
            SELECT timestamp, symbol, mean_price, std_price, volatility, z_score, sma_20, ema_20, rsi,
                   correlation_btc_eth, garch_forecast, adf_pvalue, trend
            FROM metrics
            WHERE symbol = ? AND timestamp > ?
            ORDER BY timestamp ASC
        """, (symbol, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
        csv_data = "timestamp,symbol,mean_price,std_price,volatility,z_score,sma_20,ema_20,rsi,correlation_btc_eth,garch_forecast,adf_pvalue,trend\n"
        for row in rows:
            csv_data += ",".join(str(x) if x is not None else "" for x in row) + "\n"
        
        return csv_data
    
    def cleanup_old_data(self, keep_days: int = 7) -> None:
        """Remove old data from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = time.time() * 1000 - (keep_days * 24 * 3600 * 1000)
        
        for table in ["ticks", "sampled_windows", "metrics", "alert_triggers"]:
            cursor.execute(f"DELETE FROM {table} WHERE timestamp < ?", (cutoff,))
        
        conn.commit()
        conn.close()
        logger.info(f"Cleaned up data older than {keep_days} days")
