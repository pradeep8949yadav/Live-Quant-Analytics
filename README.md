# Live Quant Analytics Dashboard

A **production-ready, real-time trading analytics system** that ingests live Binance tick data, performs advanced analytics, and displays results in a stunning interactive dashboard.

---

 
##  Quick Start

### 1️ Prerequisites
- Python 3.9+
- pip

### 2️ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️ Run Backend

```bash
python backend/main.py
```
 
### 4️ Run Frontend (New Terminal)

```bash
streamlit run frontend/app.py
```

Dashboard opens automatically at **http://localhost:8501**
 
## Architecture

```
## Project Structure


binance_analytics/
├── backend/
│   ├── main.py              # FastAPI server (port 8000)
│   ├── data_handler.py      # Binance WebSocket + SQLite
│   ├── analytics.py         # Advanced analytics engine
│   ├── models.py            # Pydantic schemas
│   └── utils.py             # Math utilities
├── frontend/
│   ├── app.py               # Streamlit dashboard (port 8501)
│   └── components/
│       ├── charts.py        # Plotly visualizations
│       ├── controls.py      # UI controls
│       └── alerts.py        # Alert components
├── data/
│   └── ticks.db             # SQLite database (auto-created)
├── requirements.txt
├── run.bat
├── run.sh
└── README.md


```

 

##  API Endpoints

### Status & Health
- `GET /health` → Health check
- `GET /status` → Connection status, uptime, tick count

### Data
- `GET /ticks/latest?symbol=BTCUSDT&limit=50` → Recent sampled windows
- `GET /price-history/{symbol}?limit=100` → Price history

### Analytics
- `GET /analytics` → All symbols latest metrics
- `GET /analytics/{symbol}` → Single symbol metrics
- `GET /correlations` → BTC-ETH correlation
- `GET /clustering` → Symbol clusters by correlation
- `GET /backtest/{symbol}` → Mean-reversion backtest results

### Alerts
- `POST /alerts/rules` → Create alert rule
- `GET /alerts/rules` → List all rules
- `PUT /alerts/rules/{rule_id}` → Update rule
- `DELETE /alerts/rules/{rule_id}` → Delete rule
- `GET /alerts/history?limit=100` → Alert trigger history

### Export
- `GET /export/csv?symbol=BTCUSDT&hours=1` → Export as CSV

---

##  Dashboard Tabs

###  Price Analysis
- Real-time price chart with VWAP
- RSI indicator (14-period)
- Z-Score with entry/exit thresholds
- Volatility visualization
- Moving averages (SMA + EMA)

###  Advanced Analytics
- Statistical summary (mean, std, vol)
- Correlation heatmap (BTC-ETH)
- Stationarity test (ADF p-value)
- GARCH volatility forecast
- Symbol clustering
- Price history plot

### Alerts
- Alert rule creator
- Active rules list with trigger count
- Alert history with timestamps
- Sound notification toggle
- Alert statistics

###  Backtesting
- Mean-reversion strategy test
- Trade count, win rate, PnL
- Entry: Z > 2.0 (SHORT) or Z < -2.0 (LONG)
- Exit: Z = 0 (mean)

###  Settings
- CSV export with date range
- API information
- Dashboard info

---
## Methodology

The analytics engine applies both **statistical** and **machine learning-based** techniques on live market data:

### 1. Z-Score Analysis
Detects price deviations from the mean to identify potential mean-reversion opportunities.

### 2. RSI (Relative Strength Index)
Measures market momentum to determine overbought and oversold conditions.

### 3. Volatility Metrics
Calculated using rolling standard deviation and **GARCH (Generalized Autoregressive Conditional Heteroskedasticity)** models to forecast price volatility.

### 4. Correlation Matrix
Analyzes inter-symbol relationships (e.g., BTC–ETH) to understand asset dependencies and co-movements.

### 5. Clustering
Groups assets based on their correlation behavior to identify similar market patterns and dynamics.

### 6. Backtesting Engine
Simulates mean-reversion and other strategies on historical tick data to evaluate profitability, trade frequency, and risk metrics.

Each computation runs continuously on sampled tick data, ensuring near real-time updates of statistical indicators and strategy performance.

##  Example Analytics Output

```json
{
  "BTCUSDT": {
    "timestamp": 1699564800000,
    "symbol": "BTCUSDT",
    "mean_price": 42650.50,
    "std_price": 45.20,
    "volatility": 0.00106,
    "z_score": 2.15,
    "sma_20": 42500.00,
    "ema_20": 42600.00,
    "rsi": 65.3,
    "correlation_btc_eth": 0.78,
    "garch_forecast": 0.00125,
    "adf_pvalue": 0.045,
    "trend": "uptrend"
  }
}
```

---

##  Testing the System

### 1️ Check Backend Health

```bash
curl http://localhost:8000/health
```

### 2️ Get Status

```bash
curl http://localhost:8000/status
```

### 3️ Get Latest Analytics

```bash
curl http://localhost:8000/analytics/BTCUSDT
```

### 4️ Create Alert Rule

```bash
curl -X POST http://localhost:8000/alerts/rules \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "metric": "z_score",
    "condition": ">",
    "threshold": 2.0,
    "enabled": true
  }'
```

---

##  Configuration

### Backend (`backend/main.py`)
- **SYMBOLS** → Modify monitored symbols
- **SAMPLING_INTERVAL** → Change sampling frequency (default: 5s)
- **MAX_ALERT_HISTORY** → Alert history retention

### Frontend (`frontend/app.py`)
- **API_BASE_URL** → Backend URL (default: http://localhost:8000)
- **Refresh Rate** → Adjustable via dashboard control
- **Window Size** → Analytics window slider (10s, 20s, 60s)

### Database (`data/ticks.db`)
- Auto-created on first run
- Cleanup of data older than 7 days runs hourly
- Indexed for fast queries

---

##  Troubleshooting

###  "Backend not responding"
1. Ensure `python backend/main.py` is running
2. Check http://localhost:8000/health
3. Verify port 8000 is not in use

###  "No alerts triggered"
1. Check Z-Score threshold (default: 2.0)
2. View alert rules at `/alerts/rules` endpoint
3. Monitor alert history in dashboard

###  "No price data"
1. Verify Binance WebSocket is connected: `/status` endpoint
2. Check network/firewall allows WebSocket (wss://fstream.binance.com)
3. View logs in terminal running backend

###  "Dashboard crashes on refresh"
1. Restart Streamlit: `streamlit run frontend/app.py`
2. Clear cache: `streamlit cache clear`
3. Verify backend is still running

---

##  Data Storage

### Tables in `data/ticks.db`

| Table | Purpose |
|-------|---------|
| `ticks` | Raw tick data (timestamp, symbol, price, qty) |
| `sampled_windows` | 5-sec aggregated VWAP windows |
| `metrics` | Computed analytics (Z-score, RSI, etc) |
| `alerts` | Alert rules configuration |
| `alert_triggers` | Alert trigger history log |

---

##  Production Deployment

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD python backend/main.py & streamlit run frontend/app.py
```

### Environment Variables
```bash
export BACKEND_PORT=8000
export FRONTEND_PORT=8501
export DATABASE_PATH=data/ticks.db
export KEEP_DATA_DAYS=7
```

### Monitoring
- Backend logs → Terminal output
- Alert triggers → SQLite + API
- Dashboard health → WebSocket status indicator

---

##  Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI, Uvicorn, asyncio |
| **Data Ingestion** | Binance WebSocket, aiohttp |
| **Analytics** | pandas, numpy, statsmodels, scikit-learn |
| **Storage** | SQLite3, SQLAlchemy |
| **Frontend** | Streamlit, Plotly |
| **Language** | Python 3.9+ |

---

##  License

MIT License - Free to use and modify

---

##  Support

For issues or questions:
1. Check terminal output for error messages
2. Verify all dependencies installed: `pip check`
3. Ensure ports 8000 and 8501 are available
4. Test API endpoints with curl

---

##  Features Roadmap

- [ ] Additional symbols (BNBUSDT, XRPUSDT, etc)
- [ ] Machine learning predictions
- [ ] Paper trading simulation
- [ ] Telegram/Email alerts
- [ ] Real-time P&L tracking
- [ ] Portfolio analytics
- [ ] Advanced charting (TradingView integration)

---

 
