🗂️ Data Description

All real-time and historical data used by the Live Quant Analytics Dashboard is stored locally in a lightweight SQLite database located at:

data/ticks.db

📁 How It Works

The data/ directory serves as the local storage for all collected and processed market data.

When we first start the backend (python backend/main.py or by running the Streamlit app), the folder and database are created automatically — no manual setup is required.

Database initialization and management are handled by the backend logic inside backend/data_handler.py.

📊 What’s Stored

Tick data — real-time trades streamed directly from Binance’s WebSocket (wss://fstream.binance.com/ws/...).

Sampled windows — periodic aggregations of tick data computed every few seconds.

Analytics metrics — calculated features such as moving averages, volatility, z-scores, RSI, and correlations.

Alert rules and history — alert conditions and past trigger events configured by users in the dashboard.

🔄 Data Flow

The backend connects to Binance’s live WebSocket feed.

Incoming trade ticks are buffered in memory.

Every few seconds, buffered ticks are sampled, analyzed, and stored in the SQLite database (ticks.db).

The Streamlit frontend retrieves these analytics and visualizations via FastAPI endpoints exposed by the backend.

 Notes

The database file ticks.db is generated automatically on first run.

If deleted, it will be recreated when the backend restarts.

No additional database configuration or credentials are required — all data is stored locally for simplicity and portability.
