# Live Quant Analytics - System Architecture

## Overview
This document provides a detailed overview of the Live Quant Analytics platform architecture.

![Architecture Diagram](image.png)

## Architecture Layers

### 1. External Layer
- **Binance Futures WebSocket**: Real-time trade data ingestion
- Endpoint: `wss://fstream.binance.com`
- Streams: BTCUSDT, ETHUSDT
- Throughput: ~1000 trades/second

### 2. Ingestion Layer
- **WebSocket Client** (`BinanceWebSocketClient`)
- Features: Auto-reconnect, event parsing, error handling
- File: `backend/data_handler.py`

### 3. Processing Layer
- **Tick Buffer**: In-memory 5-second sampling window
- **Analytics Engine**: Z-Score, RSI, SMA/EMA, GARCH, correlation
- **Alert System**: Rule-based monitoring with notifications

### 4. Storage Layer
- **SQLite Database** (`data/ticks.db`)
- Tables: ticks, sampled_windows, metrics, alerts, alert_triggers
- Retention: 7 days with hourly cleanup

### 5. API Layer
- **FastAPI Server** (Port 8000)
- 15+ REST endpoints
- HTTP/JSON with CORS enabled

### 6. Frontend Layer
- **Streamlit Dashboard** (Port 8501)
- Auto-refresh every 5 seconds
- Tabs: Price Analysis, Advanced Analytics, Alerts, Backtesting, Settings

## Data Flow

1. **T=0s**: WebSocket connects and streams trades continuously
2. **T=5s**: Tick Buffer aggregates data (VWAP calculation)
3. **T=5s+**: Analytics Engine computes metrics
4. **T=10s**: API queries database for latest data
5. **T=15s**: Dashboard refreshes with updated charts
6. **Loop continues**: Real-time monitoring

## Performance Metrics
- Ingestion Rate: ~1000 ticks/sec
- Sampling Interval: 5 seconds
- Analytics Latency: <100ms
- API Response Time: <50ms
- Dashboard Refresh: 5 seconds

## Technology Stack
- **Backend**: FastAPI, Uvicorn, asyncio, aiohttp
- **Analytics**: pandas, numpy, statsmodels, scikit-learn
- **Frontend**: Streamlit, Plotly
- **Storage**: SQLite, In-Memory Cache

## Design Decisions

### SQLite vs PostgreSQL
- ✅ Zero-config, portable, sufficient for ~1GB/week
- ❌ Limited concurrent writes

### 5-Second Sampling Window
- ✅ Balance between real-time and efficiency
- ❌ May miss sub-5s price movements

### In-Memory Buffer
- ✅ Batched writes, VWAP aggregation
- ❌ Max 5s data loss on crash

### REST vs WebSocket for Frontend
- ✅ Simpler, Streamlit-compatible
- ❌ Higher latency vs push-based updates

## Extensibility

- **New Symbols**: Add to `SYMBOLS` list in `main.py`
- **Custom Metrics**: Extend `AnalyticsEngine` class
- **Alert Channels**: Plugin architecture (Email, Slack, Discord)
- **Database**: Replace `TickDatabase` interface (PostgreSQL, TimescaleDB)
- **ML Models**: Add to analytics pipeline (LSTM, Transformers)

## Resilience Strategy

- **WebSocket Reconnection**: Exponential backoff (1s → 32s), max 5 retries
- **Dual Storage**: DB persistence + in-memory cache
- **Graceful Degradation**: Partial data on failures
- **Auto Cleanup**: Hourly pruning (7-day retention)
- **Health Monitoring**: `/health` endpoint always available

---

View the interactive architecture diagram: [architecture.drawio](image.png)
