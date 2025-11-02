"""Alert components and notifications for Streamlit dashboard."""
import streamlit as st
from typing import List, Dict
from datetime import datetime


def render_alert_banner(alert: Dict) -> None:
    """Render a single alert banner."""
    symbol = alert.get("symbol", "N/A")
    metric = alert.get("metric", "N/A")
    actual = alert.get("actual_value", 0)
    threshold = alert.get("threshold", 0)
    
    st.markdown(f"""
    <div class="alert-banner">
        <strong>🚨 Alert Triggered!</strong><br>
        <strong>Symbol:</strong> {symbol} | 
        <strong>Metric:</strong> {metric.upper()} | 
        <strong>Value:</strong> {actual:.4f} vs Threshold: {threshold:.4f}
    </div>
    """, unsafe_allow_html=True)


def render_alert_history(alerts: List[Dict], limit: int = 10) -> None:
    """Render alert history table."""
    st.subheader("📋 Recent Alerts")
    
    if not alerts:
        st.info("No alerts triggered yet.")
        return
    
    # Display latest alerts
    recent_alerts = alerts[-limit:]
    
    alert_data = []
    for alert in recent_alerts:
        alert_data.append({
            "Time": datetime.fromtimestamp(alert["timestamp"] / 1000).strftime("%H:%M:%S"),
            "Symbol": alert["symbol"],
            "Metric": alert["metric"].upper(),
            "Actual": f"{alert['actual_value']:.4f}",
            "Threshold": f"{alert['threshold']:.4f}",
        })
    
    st.dataframe(alert_data, use_container_width=True, hide_index=True)


def render_alert_rules(rules: List[Dict]) -> None:
    """Render active alert rules."""
    st.subheader("⚙️ Active Alert Rules")
    
    if not rules:
        st.info("No alert rules configured.")
        return
    
    rule_data = []
    for rule in rules:
        rule_data.append({
            "Rule ID": rule["rule_id"][:8] + "...",
            "Symbol": rule["symbol"],
            "Metric": rule["metric"].upper(),
            "Condition": rule["condition"],
            "Threshold": rule["threshold"],
            "Triggered": rule["triggered_count"],
            "Status": "✅ Enabled" if rule["enabled"] else "❌ Disabled",
        })
    
    st.dataframe(rule_data, use_container_width=True, hide_index=True)


def create_alert_sound_css() -> None:
    """Inject CSS for alert animations."""
    st.markdown("""
    <style>
        .pulse-animation {
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }
        
        .bounce-animation {
            animation: bounce 1s infinite;
        }
        
        @keyframes bounce {
            0%, 100% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-5px);
            }
        }
        
        .flash-animation {
            animation: flash 0.5s infinite;
        }
        
        @keyframes flash {
            0%, 100% {
                background-color: #ef4444;
            }
            50% {
                background-color: #dc2626;
            }
        }
        
        .alert-sound-toggle {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 999;
        }
    </style>
    """, unsafe_allow_html=True)


def render_alert_manager() -> None:
    """Render alert rule manager."""
    st.subheader("🎯 Alert Rule Manager")
    
    with st.expander("➕ Create New Alert Rule"):
        col1, col2 = st.columns(2)
        
        with col1:
            alert_symbol = st.selectbox(
                "Symbol",
                ["BTCUSDT", "ETHUSDT"],
                key="new_alert_symbol"
            )
            alert_metric = st.selectbox(
                "Metric",
                ["z_score", "volatility", "price", "rsi"],
                key="new_alert_metric"
            )
        
        with col2:
            alert_condition = st.selectbox(
                "Condition",
                [">", "<", ">=", "<=", "=="],
                key="new_alert_condition"
            )
            alert_threshold = st.number_input(
                "Threshold",
                value=2.0,
                step=0.1,
                key="new_alert_threshold"
            )
        
        if st.button("🔔 Create Alert", use_container_width=True):
            st.success(f"Alert created: {alert_symbol} {alert_metric} {alert_condition} {alert_threshold}")


def render_alert_statistics(alerts: List[Dict]) -> None:
    """Render alert statistics."""
    st.subheader("📊 Alert Statistics")
    
    if not alerts:
        st.info("No alerts to display.")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Alerts", len(alerts))
    
    with col2:
        unique_symbols = len(set(a["symbol"] for a in alerts))
        st.metric("Unique Symbols", unique_symbols)
    
    with col3:
        unique_metrics = len(set(a["metric"] for a in alerts))
        st.metric("Alert Types", unique_metrics)
    
    with col4:
        if alerts:
            latest_time = max(a["timestamp"] for a in alerts)
            from datetime import datetime, timedelta
            mins_ago = (datetime.now().timestamp() * 1000 - latest_time) / 60000
            st.metric("Latest Alert", f"{mins_ago:.0f}m ago")


def render_notification_sound_control() -> bool:
    """Render notification sound toggle."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("🔊 **Sound Notifications**")
    
    with col2:
        sound_enabled = st.checkbox("Enable", value=True, key="sound_toggle")
    
    return sound_enabled
