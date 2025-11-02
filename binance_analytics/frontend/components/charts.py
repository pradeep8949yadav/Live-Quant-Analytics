"""Animated Plotly charts for Streamlit dashboard."""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Optional
import numpy as np


def create_price_chart(prices: List[float], timestamps: List[float], symbol: str = "BTCUSDT") -> go.Figure:
    """Create animated price chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=prices,
        mode='lines+markers',
        name=symbol,
        line=dict(color='#00D4FF', width=2),
        marker=dict(size=4, color='#00FFB3'),
        hovertemplate='<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>',
    ))
    
    fig.update_layout(
        title=f"<b>{symbol} Price History</b>",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='#0f172a',
        plot_bgcolor='#1e293b',
        font=dict(family="Arial, sans-serif", size=12, color='#e2e8f0'),
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    
    return fig


def create_zscore_chart(z_scores: List[float], timestamps: List[float], prices: List[float]) -> go.Figure:
    """Create animated Z-score chart with price."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Z-Score trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=z_scores,
            mode='lines',
            name='Z-Score',
            line=dict(color='#00FFB3', width=2),
            hovertemplate='<b>%{x}</b><br>Z-Score: %{y:.3f}<extra></extra>',
        ),
        secondary_y=False,
    )
    
    # Price trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=prices,
            mode='lines',
            name='Price',
            line=dict(color='#FFD700', width=1),
            hovertemplate='<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>',
        ),
        secondary_y=True,
    )
    
    # Add threshold lines
    if len(timestamps) > 0:
        fig.add_hline(y=2.0, line_dash="dash", line_color="red", annotation_text="Short Entry (Z>2)", secondary_y=False)
        fig.add_hline(y=-2.0, line_dash="dash", line_color="green", annotation_text="Long Entry (Z<-2)", secondary_y=False)
        fig.add_hline(y=0.0, line_dash="solid", line_color="grey", annotation_text="Mean", secondary_y=False)
    
    fig.update_layout(
        title="<b>Z-Score & Price</b>",
        xaxis_title="Time",
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='#0f172a',
        plot_bgcolor='#1e293b',
        font=dict(family="Arial, sans-serif", size=12, color='#e2e8f0'),
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#334155', secondary_y=False)
    fig.update_yaxes(showgrid=False, secondary_y=True)
    
    fig.update_yaxes(title_text="Z-Score", secondary_y=False)
    fig.update_yaxes(title_text="Price (USD)", secondary_y=True)
    
    return fig


def create_volatility_chart(volatility: List[float], timestamps: List[float]) -> go.Figure:
    """Create volatility over time chart."""
    colors = ['#FF6B6B' if v > 0.05 else '#4ECDC4' for v in volatility]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=timestamps,
        y=volatility,
        marker=dict(color=colors),
        name='Volatility',
        hovertemplate='<b>%{x}</b><br>Vol: %{y:.4f}<extra></extra>',
    ))
    
    fig.add_hline(y=0.05, line_dash="dash", line_color="orange", annotation_text="High Vol Threshold")
    
    fig.update_layout(
        title="<b>Price Volatility (StDev)</b>",
        xaxis_title="Time",
        yaxis_title="Volatility",
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='#0f172a',
        plot_bgcolor='#1e293b',
        font=dict(family="Arial, sans-serif", size=12, color='#e2e8f0'),
        height=350,
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=False,
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    
    return fig


def create_rsi_chart(rsi: List[float], timestamps: List[float]) -> go.Figure:
    """Create RSI chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=rsi,
        mode='lines',
        name='RSI(14)',
        line=dict(color='#FF9F43', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 159, 67, 0.2)',
        hovertemplate='<b>%{x}</b><br>RSI: %{y:.2f}<extra></extra>',
    ))
    
    # Overbought/oversold zones
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
    fig.add_hline(y=50, line_dash="solid", line_color="grey", annotation_text="Neutral")
    
    fig.update_layout(
        title="<b>Relative Strength Index (RSI)</b>",
        xaxis_title="Time",
        yaxis_title="RSI",
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='#0f172a',
        plot_bgcolor='#1e293b',
        font=dict(family="Arial, sans-serif", size=12, color='#e2e8f0'),
        height=350,
        margin=dict(l=50, r=50, t=50, b=50),
        yaxis=dict(range=[0, 100]),
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    
    return fig


def create_correlation_heatmap(correlations: Dict[str, float]) -> go.Figure:
    """Create correlation heatmap."""
    symbols = ["BTCUSDT", "ETHUSDT"]
    
    # Create matrix
    matrix = [[1.0, 0.0], [0.0, 1.0]]
    
    for key, corr in correlations.items():
        if "BTCUSDT" in key and "ETHUSDT" in key:
            matrix[0][1] = matrix[1][0] = corr
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=symbols,
        y=symbols,
        colorscale='RdBu',
        zmid=0,
        zmin=-1,
        zmax=1,
        text=matrix,
        texttemplate='%{text:.3f}',
        textfont={"size": 14},
        colorbar=dict(title="Correlation"),
    ))
    
    fig.update_layout(
        title="<b>Symbol Correlation Matrix</b>",
        hovermode='closest',
        template='plotly_dark',
        paper_bgcolor='#0f172a',
        plot_bgcolor='#1e293b',
        font=dict(family="Arial, sans-serif", size=12, color='#e2e8f0'),
        height=350,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    return fig


def create_moving_averages_chart(prices: List[float], sma: List[float], ema: List[float], timestamps: List[float]) -> go.Figure:
    """Create moving averages chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=prices,
        mode='lines',
        name='Price',
        line=dict(color='#00D4FF', width=1),
    ))
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=sma,
        mode='lines',
        name='SMA(20)',
        line=dict(color='#FFD700', width=2, dash='dash'),
    ))
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=ema,
        mode='lines',
        name='EMA(20)',
        line=dict(color='#FF9F43', width=2),
    ))
    
    fig.update_layout(
        title="<b>Price & Moving Averages</b>",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='#0f172a',
        plot_bgcolor='#1e293b',
        font=dict(family="Arial, sans-serif", size=12, color='#e2e8f0'),
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    
    return fig


def create_volume_chart(volumes: List[float], timestamps: List[float], symbol: str = "BTCUSDT") -> go.Figure:
    """Create volume chart."""
    colors = ['#00FFB3' if i % 2 == 0 else '#FF6B9D' for i in range(len(volumes))]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=timestamps,
        y=volumes,
        marker=dict(color=colors),
        name='Volume',
        hovertemplate='<b>%{x}</b><br>Volume: %{y:.2f}<extra></extra>',
    ))
    
    fig.update_layout(
        title=f"<b>{symbol} Trading Volume</b>",
        xaxis_title="Time",
        yaxis_title="Volume",
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='#0f172a',
        plot_bgcolor='#1e293b',
        font=dict(family="Arial, sans-serif", size=12, color='#e2e8f0'),
        height=350,
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=False,
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#334155')
    
    return fig
