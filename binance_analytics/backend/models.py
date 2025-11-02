"""Data models and Pydantic schemas for the Quant Analytics system."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


@dataclass
class Tick:
    """Raw tick from Binance WebSocket."""
    timestamp: float
    symbol: str
    price: float
    quantity: float
    
    @property
    def iso_timestamp(self) -> str:
        return datetime.fromtimestamp(self.timestamp / 1000).isoformat()


@dataclass
class SampledWindow:
    """5-second aggregated data window."""
    timestamp: float
    symbol: str
    mean_price: float
    std_price: float
    min_price: float
    max_price: float
    total_volume: float
    tick_count: int
    vwap: float


@dataclass
class AnalyticsMetrics:
    """Computed analytics for a symbol."""
    timestamp: float
    symbol: str
    mean_price: float
    std_price: float
    volatility: float
    z_score: float
    sma_20: float
    ema_20: float
    rsi: float
    correlation_btc_eth: Optional[float] = None
    garch_forecast: Optional[float] = None
    adf_pvalue: Optional[float] = None
    trend: str = "neutral"


class TickResponse(BaseModel):
    timestamp: float
    symbol: str
    price: float
    quantity: float
    iso_timestamp: str


class SampledWindowResponse(BaseModel):
    timestamp: float
    symbol: str
    mean_price: float
    std_price: float
    min_price: float
    max_price: float
    total_volume: float
    tick_count: int
    vwap: float


class AnalyticsResponse(BaseModel):
    timestamp: float
    symbol: str
    mean_price: float
    std_price: float
    volatility: float
    z_score: float
    sma_20: float
    ema_20: float
    rsi: float
    correlation_btc_eth: Optional[float] = None
    garch_forecast: Optional[float] = None
    adf_pvalue: Optional[float] = None
    trend: str


class AlertRuleRequest(BaseModel):
    symbol: str
    metric: str
    condition: str
    threshold: float
    enabled: bool = True


class AlertRuleResponse(BaseModel):
    rule_id: str
    symbol: str
    metric: str
    condition: str
    threshold: float
    enabled: bool
    triggered_count: int


class ConnectionStatusResponse(BaseModel):
    status: str
    uptime_seconds: float
    ticks_received: int
    last_tick_timestamp: Optional[float] = None
