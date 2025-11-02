"""Utility functions for analytics calculations."""
import math
from typing import List, Optional
from collections import deque
import numpy as np


def calculate_mean(values: List[float]) -> float:
    """Calculate arithmetic mean."""
    return sum(values) / len(values) if values else 0.0


def calculate_std(values: List[float], mean: Optional[float] = None) -> float:
    """Calculate standard deviation."""
    if not values or len(values) < 2:
        return 0.0
    m = mean or calculate_mean(values)
    variance = sum((x - m) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def calculate_vwap(prices: List[float], volumes: List[float]) -> float:
    """Calculate Volume Weighted Average Price."""
    if not prices or not volumes or len(prices) != len(volumes):
        return 0.0
    num = sum(p * v for p, v in zip(prices, volumes))
    denom = sum(volumes)
    return num / denom if denom > 0 else 0.0


def calculate_sma(values: List[float], period: int = 20) -> float:
    """Calculate Simple Moving Average."""
    if len(values) < period:
        return calculate_mean(values)
    return calculate_mean(values[-period:])


def calculate_ema(values: List[float], period: int = 20) -> float:
    """Calculate Exponential Moving Average."""
    if not values:
        return 0.0
    if len(values) < period:
        return calculate_mean(values)
    
    k = 2.0 / (period + 1)
    ema = values[0]
    for val in values[1:]:
        ema = val * k + ema * (1 - k)
    return ema


def calculate_rsi(values: List[float], period: int = 14) -> float:
    """Calculate Relative Strength Index."""
    if len(values) < period + 1:
        return 50.0
    
    changes = [values[i] - values[i-1] for i in range(1, len(values))]
    gains = [max(c, 0) for c in changes[-period:]]
    losses = [abs(min(c, 0)) for c in changes[-period:]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def calculate_z_score(value: float, mean: float, std: float) -> float:
    """Calculate Z-score."""
    if std == 0:
        return 0.0
    return (value - mean) / std


def calculate_correlation(x: List[float], y: List[float]) -> Optional[float]:
    """Calculate Pearson correlation coefficient."""
    if len(x) < 2 or len(y) < 2 or len(x) != len(y):
        return None
    
    x_mean = calculate_mean(x)
    y_mean = calculate_mean(y)
    
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    x_std = calculate_std(x, x_mean)
    y_std = calculate_std(y, y_mean)
    
    if x_std == 0 or y_std == 0:
        return None
    
    denominator = len(x) * x_std * y_std
    return numerator / denominator if denominator != 0 else None


def detect_trend(sma: float, ema: float, current_price: float) -> str:
    """Detect trend based on price and moving averages."""
    if current_price > sma and sma > ema:
        return "uptrend"
    elif current_price < sma and sma < ema:
        return "downtrend"
    else:
        return "neutral"


def check_alert_condition(value: float, condition: str, threshold: float) -> bool:
    """Check if alert condition is met."""
    if condition == ">":
        return value > threshold
    elif condition == "<":
        return value < threshold
    elif condition == ">=":
        return value >= threshold
    elif condition == "<=":
        return value <= threshold
    elif condition == "==":
        return abs(value - threshold) < 1e-6
    elif condition == "!=":
        return abs(value - threshold) >= 1e-6
    return False


def calculate_adf_test_simple(values: List[float]) -> Optional[float]:
    """
    Simplified ADF test p-value calculation.
    Returns approximation: lower = more stationary.
    """
    if len(values) < 10:
        return None
    
    # Simple approach: if autocorr is high, it's non-stationary
    mean = calculate_mean(values)
    autocov = sum((values[i] - mean) * (values[i-1] - mean) for i in range(1, len(values))) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    
    if var == 0:
        return 1.0
    
    autocorr = autocov / var
    p_value = 1.0 / (1.0 + abs(autocorr))  # Heuristic
    return p_value


def calculate_garch_volatility_forecast(returns: List[float], horizon: int = 1) -> Optional[float]:
    """
    Simplified GARCH(1,1) volatility forecast.
    Real implementation would use statsmodels.
    """
    if len(returns) < 10:
        return None
    
    # Simple approximation: exponential weighted variance
    alpha = 0.1
    beta = 0.85
    
    current_return = returns[-1]
    current_vol_sq = calculate_std(returns) ** 2
    
    # GARCH(1,1): sigma_t^2 = omega + alpha*epsilon_{t-1}^2 + beta*sigma_{t-1}^2
    long_term_var = np.var(returns) if returns else current_vol_sq
    omega = (1 - alpha - beta) * long_term_var
    
    forecast_vol_sq = omega + alpha * (current_return ** 2) + beta * current_vol_sq
    return math.sqrt(max(forecast_vol_sq, 0.0))


def exponential_backoff(attempt: int, base: float = 1.0, max_wait: float = 60.0) -> float:
    """Calculate exponential backoff time."""
    wait = min(base * (2 ** attempt), max_wait)
    return wait + np.random.uniform(0, 1)  # Add jitter
