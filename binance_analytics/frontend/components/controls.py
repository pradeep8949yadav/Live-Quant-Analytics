"""UI controls and components for Streamlit dashboard."""
import streamlit as st
from typing import Tuple, Dict


def render_header() -> None:
    """Render dashboard header."""
    st.markdown("""
    <style>
        .header-title {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00D4FF, #00FFB3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .header-subtitle {
            font-size: 1.1rem;
            color: #a0aec0;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="header-title">📊 Binance Live Quant Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-subtitle">Real-time Trading Dashboard with Advanced Analytics</div>', unsafe_allow_html=True)
    st.markdown("---")


def render_top_controls() -> Tuple[str, int, float]:
    """Render top control bar."""
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
    
    with col1:
        symbol = st.selectbox(
            "📈 Select Symbol",
            ["BTCUSDT", "ETHUSDT"],
            key="symbol_select"
        )
    
    with col2:
        refresh_rate = st.selectbox(
            "🔄 Refresh Rate",
            [2, 5, 10, 30],
            index=1,
            help="Dashboard refresh interval in seconds",
            key="refresh_select"
        )
    
    with col3:
        window_size = st.selectbox(
            "⏱ Window Size",
            [10, 20, 60],
            index=1,
            help="Analytics window size in seconds",
            key="window_select"
        )
    
    with col4:
        z_threshold = st.slider(
            "⚡ Z-Threshold",
            1.0, 5.0, 2.0, 0.1,
            help="Z-score alert threshold",
            key="z_threshold"
        )
    
    return symbol, refresh_rate, z_threshold


def render_status_bar(status: Dict) -> None:
    """Render connection status bar."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = "🟢" if status.get("status") == "connected" else "🔴"
        st.metric(
            "Connection",
            f"{status_color} {status.get('status', 'unknown')}",
            "Live" if status.get("status") == "connected" else "Offline"
        )
    
    with col2:
        uptime_minutes = status.get("uptime_seconds", 0) / 60
        st.metric(
            "Uptime",
            f"{uptime_minutes:.1f}m",
            f"{status.get('uptime_seconds', 0):.0f}s"
        )
    
    with col3:
        st.metric(
            "Ticks Received",
            f"{status.get('ticks_received', 0):,}",
            "Live feed"
        )
    
    with col4:
        if status.get('last_tick_timestamp'):
            import time
            elapsed = (time.time() * 1000 - status['last_tick_timestamp']) / 1000
            st.metric(
                "Last Tick",
                f"{elapsed:.1f}s ago",
                "Real-time"
            )


def render_metrics_cards(metrics: Dict) -> None:
    """Render metric cards."""
    if not metrics:
        st.warning("⏳ Awaiting data...")
        return
    
    m = metrics
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        price_color = "🟢" if m["trend"] == "uptrend" else "🔴" if m["trend"] == "downtrend" else "🟡"
        st.metric(
            "Current Price",
            f"${m['mean_price']:.2f}",
            f"{price_color} {m['trend'].upper()}"
        )
    
    with col2:
        st.metric(
            "Volatility (StDev)",
            f"{m['volatility']:.4f}",
            f"{'🔴 HIGH' if m['volatility'] > 0.05 else '🟢 LOW'}"
        )
    
    with col3:
        z_color = "🔴 SHORT" if m["z_score"] > 2 else "🟢 LONG" if m["z_score"] < -2 else "🟡 NEUTRAL"
        st.metric(
            "Z-Score",
            f"{m['z_score']:.3f}",
            z_color
        )
    
    with col4:
        st.metric(
            "RSI(14)",
            f"{m['rsi']:.2f}",
            f"{'🔴 OVERBOUGHT' if m['rsi'] > 70 else '🟢 OVERSOLD' if m['rsi'] < 30 else '🟡 NEUTRAL'}"
        )


def render_moving_averages_metrics(metrics: Dict) -> None:
    """Render moving averages metrics."""
    if not metrics:
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "SMA(20)",
            f"${metrics['sma_20']:.2f}",
            f"${metrics['mean_price'] - metrics['sma_20']:.2f}"
        )
    
    with col2:
        st.metric(
            "EMA(20)",
            f"${metrics['ema_20']:.2f}",
            f"${metrics['mean_price'] - metrics['ema_20']:.2f}"
        )
    
    with col3:
        if metrics.get('garch_forecast'):
            st.metric(
                "GARCH Vol Forecast",
                f"{metrics['garch_forecast']:.4f}",
                "Volatility prediction"
            )


def render_advanced_metrics(metrics: Dict) -> None:
    """Render advanced analytics metrics."""
    if not metrics:
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if metrics.get('correlation_btc_eth') is not None:
            corr = metrics['correlation_btc_eth']
            st.metric(
                "BTC-ETH Correlation",
                f"{corr:.3f}",
                f"{'Strong' if abs(corr) > 0.7 else 'Moderate' if abs(corr) > 0.5 else 'Weak'}"
            )
    
    with col2:
        if metrics.get('adf_pvalue') is not None:
            is_stationary = metrics['adf_pvalue'] < 0.05
            st.metric(
                "ADF Stationarity",
                f"{metrics['adf_pvalue']:.4f}",
                f"{'Stationary' if is_stationary else 'Non-Stationary'}"
            )
    
    with col3:
        st.metric(
            "Trend",
            metrics['trend'].upper(),
            "Mean price vs SMA/EMA"
        )


def render_alert_panel() -> Tuple[str, str, float]:
    """Render alert configuration panel."""
    st.subheader("🚨 Create Alert Rule")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        symbol = st.selectbox(
            "Alert Symbol",
            ["BTCUSDT", "ETHUSDT"],
            key="alert_symbol"
        )
    
    with col2:
        metric = st.selectbox(
            "Alert Metric",
            ["z_score", "volatility", "price", "rsi"],
            key="alert_metric"
        )
    
    with col3:
        condition = st.selectbox(
            "Condition",
            [">", "<", ">=", "<=", "=="],
            key="alert_condition"
        )
    
    threshold = st.slider(
        "Threshold Value",
        min_value=-10.0,
        max_value=10.0,
        value=2.0,
        step=0.1,
        key="alert_threshold"
    )
    
    return symbol, metric, condition, threshold


def render_backtest_panel() -> str:
    """Render backtest panel."""
    st.subheader("📊 Mean-Reversion Backtest")
    
    symbol = st.selectbox(
        "Backtest Symbol",
        ["BTCUSDT", "ETHUSDT"],
        key="backtest_symbol"
    )
    
    return symbol


def render_footer() -> None:
    """Render footer."""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🔌 Connected to: Binance Futures WebSocket")
    
    with col2:
        st.caption("⚡ Backend: FastAPI + SQLite")
    
    with col3:
        st.caption("💡 Data updated every 5 seconds")


def apply_custom_css() -> None:
    """Apply custom CSS styling."""
    st.markdown("""
    <style>
        :root {
            --primary: #00D4FF;
            --secondary: #00FFB3;
            --accent: #FFD700;
            --danger: #FF6B6B;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
        }
        
        * {
            font-family: 'Inter', 'Rubik', sans-serif;
        }
        
        .stMetric {
            background-color: var(--bg-card);
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid #334155;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .stMetric label {
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #a0aec0;
        }
        
        .stButton button {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: var(--bg-dark);
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 212, 255, 0.3);
        }
        
        .alert-banner {
            background: #ef4444;
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .connection-status {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background-color: var(--bg-card);
            border-radius: 0.5rem;
            border: 1px solid var(--secondary);
        }
        
        .connection-status.connected {
            border-color: var(--secondary);
        }
        
        .connection-status.disconnected {
            border-color: var(--danger);
        }
    </style>
    """, unsafe_allow_html=True)
