"""Streamlit dashboard for Binance Live Quant Analytics."""
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from typing import Dict, Optional
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.components import charts, controls, alerts

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title=" Quant Analytics",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
controls.apply_custom_css()
alerts.create_alert_sound_css()

# Session state
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if "alerts_cache" not in st.session_state:
    st.session_state.alerts_cache = []
if "rules_cache" not in st.session_state:
    st.session_state.rules_cache = []

# API configuration
API_BASE_URL = "http://localhost:8000"

def get_api_data(endpoint: str, params: Dict = None) -> Optional[Dict]:
    """Fetch data from backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API error: {e}")
        return None


def post_api_data(endpoint: str, data: Dict) -> Optional[Dict]:
    """Post data to backend API."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API error: {e}")
        return None


def delete_api_data(endpoint: str) -> bool:
    """Delete via API."""
    try:
        response = requests.delete(f"{API_BASE_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"API error: {e}")
        return False


# ==============================================================================
# MAIN DASHBOARD
# ==============================================================================

def main():
    """Main dashboard function."""
    
    # Header
    controls.render_header()
    
    # Top controls
    symbol, refresh_rate, z_threshold = controls.render_top_controls()
    
    # Status bar
    status = get_api_data("/status")
    if status:
        controls.render_status_bar(status)
    else:
        st.error("⚠️ Backend not responding. Make sure to run: `python backend/main.py`")
        st.stop()
    
    st.markdown("---")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Price Analysis",
        "🧮 Advanced Analytics",
        "🚨 Alerts",
        "📊 Backtesting",
        "⚙️ Settings"
    ])
    
    # ==================================================================
    # TAB 1: PRICE ANALYSIS
    # ==================================================================
    with tab1:
        st.subheader(f"💹 {symbol} Price Analysis")
        
        # Metrics
        analytics = get_api_data(f"/analytics/{symbol}")
        if analytics:
            controls.render_metrics_cards(analytics)
            st.divider()
            controls.render_moving_averages_metrics(analytics)
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Price chart
            ticks = get_api_data("/ticks/latest", {"symbol": symbol, "limit": 100})
            if ticks and len(ticks) > 0:
                timestamps = [datetime.fromtimestamp(t["timestamp"]/1000).strftime("%H:%M:%S") for t in ticks]
                prices = [t["mean_price"] for t in ticks]
                fig = charts.create_price_chart(prices, timestamps, symbol)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # RSI chart
            if analytics and len(prices) > 0:
                rsi_values = [analytics.get("rsi", 50)] * len(prices)
                fig = charts.create_rsi_chart(rsi_values, timestamps)
                st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Z-Score chart
            if analytics and ticks:
                z_scores = [analytics.get("z_score", 0)] * len(prices)
                fig = charts.create_zscore_chart(z_scores, timestamps, prices)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Volatility chart
            if analytics and ticks:
                volatility = [analytics.get("volatility", 0)] * len(prices)
                fig = charts.create_volatility_chart(volatility, timestamps)
                st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Moving averages
        if analytics and ticks:
            sma = [analytics.get("sma_20", 0)] * len(prices)
            ema = [analytics.get("ema_20", 0)] * len(prices)
            fig = charts.create_moving_averages_chart(prices, sma, ema, timestamps)
            st.plotly_chart(fig, use_container_width=True, key="ma_chart")
    
    # ==================================================================
    # TAB 2: ADVANCED ANALYTICS
    # ==================================================================
    with tab2:
        st.subheader("🔬 Advanced Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Statistical Metrics")
            analytics = get_api_data(f"/analytics/{symbol}")
            if analytics:
                controls.render_advanced_metrics(analytics)
        
        with col2:
            st.write("### Correlation Matrix")
            corr_data = get_api_data("/correlations")
            if corr_data:
                correlations = corr_data.get("correlations", {})
                fig = charts.create_correlation_heatmap(correlations)
                st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Clustering
        st.write("### Symbol Clustering")
        clustering = get_api_data("/clustering")
        if clustering:
            clusters = clustering.get("clusters", [])
            for i, cluster in enumerate(clusters):
                st.info(f"**Cluster {i+1}:** {', '.join(cluster)}")
        
        st.divider()
        
        # Price history
        st.write("### Price History")
        history = get_api_data(f"/price-history/{symbol}", {"limit": 50})
        if history and history.get("prices"):
            history_df = pd.DataFrame({
                "Index": range(len(history["prices"])),
                "Price": history["prices"]
            })
            st.line_chart(history_df.set_index("Index"), use_container_width=True)
    
    # ==================================================================
    # TAB 3: ALERTS
    # ==================================================================
    with tab3:
        st.subheader("🚨 Alert Management")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            alerts.render_alert_manager()
        
        with col2:
            alerts.render_notification_sound_control()
        
        st.divider()
        
        # Alert rules
        rules_response = get_api_data("/alerts/rules")
        if rules_response:
            alerts.render_alert_rules(rules_response)
        
        st.divider()
        
        # Alert history
        history_response = get_api_data("/alerts/history")
        if history_response:
            alert_list = history_response.get("alerts", [])
            if alert_list:
                alerts.render_alert_history(alert_list)
                alerts.render_alert_statistics(alert_list)
            else:
                st.info("No alerts triggered yet.")
    
    # ==================================================================
    # TAB 4: BACKTESTING
    # ==================================================================
    with tab4:
        st.subheader("📊 Mean-Reversion Backtest")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            backtest_symbol = st.selectbox(
                "Select Symbol",
                ["BTCUSDT", "ETHUSDT"],
                key="backtest_symbol"
            )
            
            if st.button("▶️ Run Backtest", use_container_width=True):
                with st.spinner("Running backtest..."):
                    result = get_api_data(f"/backtest/{backtest_symbol}")
                    if result:
                        st.success("Backtest completed!")
                        
                        col1_bt, col2_bt, col3_bt = st.columns(3)
                        with col1_bt:
                            st.metric("Total Trades", result.get("trades", 0))
                        with col2_bt:
                            st.metric("Win Rate", f"{result.get('win_rate', 0)*100:.1f}%")
                        with col3_bt:
                            st.metric("Total PnL", f"${result.get('total_pnl', 0):.2f}")
                        
                        st.divider()
                        
                        col1_bt, col2_bt = st.columns(2)
                        with col1_bt:
                            st.metric("Wins", result.get("wins", 0))
                            st.metric("Losses", result.get("losses", 0))
                        with col2_bt:
                            st.metric("Avg PnL per Trade", f"${result.get('avg_pnl', 0):.2f}")
        
        with col2:
            st.info("""
            ### Mean-Reversion Strategy
            - **Entry Signal**: Z-Score > 2.0 (SHORT) or Z-Score < -2.0 (LONG)
            - **Exit Signal**: Z-Score = 0 (mean)
            - **Backtest Window**: Last 60 sampling periods (5 minutes)
            
            ### Key Metrics
            - **Win Rate**: % of profitable trades
            - **Total PnL**: Sum of all trade profits/losses
            - **Avg PnL**: Average profit/loss per trade
            """)
    
    # ==================================================================
    # TAB 5: SETTINGS
    # ==================================================================
    with tab5:
        st.subheader("⚙️ Dashboard Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Data Export")
            export_symbol = st.selectbox("Export Symbol", ["BTCUSDT", "ETHUSDT"])
            export_hours = st.slider("Export Period (hours)", 1, 24, 1)
            
            if st.button("📥 Export to CSV", use_container_width=True):
                try:
                    response = requests.get(
                        f"{API_BASE_URL}/export/csv",
                        params={"symbol": export_symbol, "hours": export_hours},
                        timeout=10
                    )
                    if response.status_code == 200:
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=response.text,
                            file_name=f"{export_symbol}_analytics_{datetime.now().isoformat()}.csv",
                            mime="text/csv"
                        )
                        st.success("Export ready!")
                except Exception as e:
                    st.error(f"Export failed: {e}")
        
        with col2:
            st.write("### API Information")
            st.info(f"""
            **Backend URL:** {API_BASE_URL}
            **Status:** {'🟢 Connected' if status else '🔴 Disconnected'}
            **API Version:** v1.0
            """)
        
        st.divider()
        
        st.write("### Dashboard Info")
        st.markdown("""
        - **Real-time Data:** Updated every 5 seconds
        - **Data Source:** Binance Futures WebSocket
        - **Database:** SQLite (data/ticks.db)
        - **Analytics Engine:** Python (pandas, statsmodels, scikit-learn)
        """)
    
    # Footer
    st.divider()
    controls.render_footer()


if __name__ == "__main__":
    main()
