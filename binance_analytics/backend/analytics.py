"""Advanced analytics module for quant trading."""
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime
import numpy as np

from backend.models import AnalyticsMetrics, SampledWindow
from backend import utils

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Compute real-time trading analytics."""
    
    def __init__(self, window_size: int = 60, max_history: int = 500):
        """
        Args:
            window_size: Number of 5-sec windows to keep (5 min default)
            max_history: Max historical points to maintain
        """
        self.window_size = window_size
        self.max_history = max_history
        
        # Price history per symbol
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.volume_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.timestamp_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.returns_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        
        # Metrics cache
        self.latest_metrics: Dict[str, AnalyticsMetrics] = {}
    
    def process_window(self, window: SampledWindow) -> AnalyticsMetrics:
        """Process a 5-sec sampled window and compute metrics."""
        symbol = window.symbol
        
        # Add to history
        self.price_history[symbol].append(window.mean_price)
        self.volume_history[symbol].append(window.total_volume)
        self.timestamp_history[symbol].append(window.timestamp)
        
        # Calculate returns for GARCH
        if len(self.price_history[symbol]) > 1:
            ret = (window.mean_price - self.price_history[symbol][-2]) / self.price_history[symbol][-2]
            self.returns_history[symbol].append(ret)
        
        # Compute metrics
        prices = list(self.price_history[symbol])
        volumes = list(self.volume_history[symbol])
        returns = list(self.returns_history[symbol])
        
        mean_price = utils.calculate_mean(prices)
        std_price = utils.calculate_std(prices, mean_price)
        volatility = std_price / mean_price if mean_price > 0 else 0.0
        
        # Z-score based on recent window
        recent_prices = prices[-self.window_size:] if len(prices) >= self.window_size else prices
        recent_mean = utils.calculate_mean(recent_prices)
        recent_std = utils.calculate_std(recent_prices, recent_mean)
        z_score = utils.calculate_z_score(window.mean_price, recent_mean, recent_std)
        
        # Moving averages
        sma_20 = utils.calculate_sma(prices, 20)
        ema_20 = utils.calculate_ema(prices, 20)
        
        # RSI
        rsi = utils.calculate_rsi(prices, 14)
        
        # Trend detection
        trend = utils.detect_trend(sma_20, ema_20, window.mean_price)
        
        # ADF test (stationarity)
        adf_pvalue = utils.calculate_adf_test_simple(prices)
        
        # GARCH volatility forecast
        garch_forecast = utils.calculate_garch_volatility_forecast(returns, horizon=1)
        
        # Correlation (BTC-ETH)
        correlation = None
        if symbol == "BTCUSDT" and "ETHUSDT" in self.price_history:
            eth_prices = list(self.price_history["ETHUSDT"])
            if len(eth_prices) == len(prices):
                correlation = utils.calculate_correlation(prices, eth_prices)
        elif symbol == "ETHUSDT" and "BTCUSDT" in self.price_history:
            btc_prices = list(self.price_history["BTCUSDT"])
            if len(prices) == len(btc_prices):
                correlation = utils.calculate_correlation(btc_prices, prices)
        
        metrics = AnalyticsMetrics(
            timestamp=window.timestamp,
            symbol=symbol,
            mean_price=mean_price,
            std_price=std_price,
            volatility=volatility,
            z_score=z_score,
            sma_20=sma_20,
            ema_20=ema_20,
            rsi=rsi,
            correlation_btc_eth=correlation,
            garch_forecast=garch_forecast,
            adf_pvalue=adf_pvalue,
            trend=trend,
        )
        
        self.latest_metrics[symbol] = metrics
        return metrics
    
    def get_metrics(self, symbol: str) -> Optional[AnalyticsMetrics]:
        """Get latest metrics for symbol."""
        return self.latest_metrics.get(symbol)
    
    def get_all_metrics(self) -> Dict[str, AnalyticsMetrics]:
        """Get all latest metrics."""
        return self.latest_metrics.copy()
    
    def get_price_history(self, symbol: str, limit: int = 100) -> List[float]:
        """Get price history for symbol."""
        prices = list(self.price_history[symbol])
        return prices[-limit:] if len(prices) > limit else prices
    
    def get_correlation_matrix(self) -> Dict[str, float]:
        """Get correlation matrix between all symbols."""
        result = {}
        symbols = list(self.price_history.keys())
        
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                prices1 = list(self.price_history[sym1])
                prices2 = list(self.price_history[sym2])
                
                if len(prices1) == len(prices2) and len(prices1) > 0:
                    corr = utils.calculate_correlation(prices1, prices2)
                    if corr is not None:
                        key = f"{sym1}-{sym2}"
                        result[key] = corr
        
        return result
    
    def detect_anomalies(self, symbol: str, z_threshold: float = 3.0) -> List[float]:
        """Detect price anomalies using Z-score."""
        prices = list(self.price_history[symbol])
        if len(prices) < 10:
            return []
        
        mean = utils.calculate_mean(prices)
        std = utils.calculate_std(prices, mean)
        
        anomalies = []
        for price in prices:
            z = utils.calculate_z_score(price, mean, std)
            if abs(z) > z_threshold:
                anomalies.append(price)
        
        return anomalies
    
    def backtest_mean_reversion(self, symbol: str, 
                                entry_threshold: float = 2.0,
                                exit_threshold: float = 0.0) -> Dict:
        """Simple mean-reversion backtest."""
        prices = list(self.price_history[symbol])
        if len(prices) < 20:
            return {"trades": 0, "wins": 0, "losses": 0}
        
        trades = []
        position = None
        
        for i in range(20, len(prices)):
            recent = prices[i-20:i]
            mean = utils.calculate_mean(recent)
            std = utils.calculate_std(recent, mean)
            z = utils.calculate_z_score(prices[i], mean, std)
            
            # Entry signals
            if position is None:
                if z > entry_threshold:  # Overbought - short
                    position = {"type": "short", "price": prices[i], "index": i}
                elif z < -entry_threshold:  # Oversold - long
                    position = {"type": "long", "price": prices[i], "index": i}
            
            # Exit signals
            elif position and abs(z) < exit_threshold:
                pnl = 0
                if position["type"] == "long":
                    pnl = prices[i] - position["price"]
                else:
                    pnl = position["price"] - prices[i]
                
                trades.append({"pnl": pnl, "type": position["type"]})
                position = None
        
        wins = sum(1 for t in trades if t["pnl"] > 0)
        losses = sum(1 for t in trades if t["pnl"] <= 0)
        total_pnl = sum(t["pnl"] for t in trades)
        
        return {
            "trades": len(trades),
            "wins": wins,
            "losses": losses,
            "win_rate": wins / len(trades) if trades else 0.0,
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / len(trades) if trades else 0.0,
        }
    
    def cluster_by_correlation(self, min_correlation: float = 0.7) -> List[List[str]]:
        """Cluster symbols by correlation."""
        symbols = list(self.price_history.keys())
        if len(symbols) < 2:
            return [[s] for s in symbols]
        
        # Build correlation matrix
        n = len(symbols)
        corr_matrix = [[0.0] * n for _ in range(n)]
        
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols):
                if i == j:
                    corr_matrix[i][j] = 1.0
                elif i < j:
                    prices1 = list(self.price_history[sym1])
                    prices2 = list(self.price_history[sym2])
                    if len(prices1) == len(prices2) and len(prices1) > 0:
                        corr = utils.calculate_correlation(prices1, prices2)
                        if corr is not None:
                            corr_matrix[i][j] = corr_matrix[j][i] = corr
        
        # Simple clustering
        clusters = []
        assigned = set()
        
        for i, sym1 in enumerate(symbols):
            if i in assigned:
                continue
            
            cluster = [sym1]
            assigned.add(i)
            
            for j, sym2 in enumerate(symbols):
                if j not in assigned and corr_matrix[i][j] >= min_correlation:
                    cluster.append(sym2)
                    assigned.add(j)
            
            clusters.append(cluster)
        
        return clusters
