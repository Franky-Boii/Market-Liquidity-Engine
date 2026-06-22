# Real-Time Financial Market Ingestion & Liquidity Engine

An extraordinary, high-throughput, low-latency data engineering platform designed to ingest live, high-frequency tick-by-tick financial market data, process structural volatility metrics on the fly, backfill macro market histories, and persist data optimized for advanced time-series analysis.

## 🏗️ System Architecture & Framework Data Flow

The engine decouples structural network input streams from analytic processing loops to completely avoid message drop-offs or bottleneck friction during peak high-frequency volatility windows.

* **Ingestion Core (Producer):** Asynchronous multi-market WebSocket client managing concurrent data channels (`wss://`) across key asset indices (`BTC`, `ETH`, `SOL`, `BNB`) with a custom non-blocking SSL bypass layer.
* **Buffer Layer (Queue):** Thread-safe asynchronous execution buffer (`asyncio.Queue`) engineered to handle data backpressure seamlessly.
* **Stream Analytics (Consumer):** Compute engine calculating rolling Volume-Weighted Average Price (VWAP) variables and instantly flagging real-time institutional liquidity sweeps.
* **Historical Mining Core:** Isolated REST backfiller microservice that queries historical candlestick matrices from global exchanges to populate decades of historical macro time-series trends.
* **Persistence Layer (Sink):** PostgreSQL repository using precise indexing architectures tailored for rapid date-range query scans.
* **Operational Telemetry Hub:** High-fidelity Streamlit interface with smart auto-resampling time arrays that switches seamlessly between standard trend charts, rich TradingView-style financial candles, and standalone volume histograms.

---

## 🚀 Enterprise Installation & System Execution Guide

### 1. Initialize and Activate the Virtual Workspace
```bash
# Clone the repository and enter the directory
cd market-liquidity-engine

# Build an isolated virtual environment shell
python3 -m venv env
source env/bin/activate

# Install required high-performance streaming dependencies
pip install websockets psycopg2-binary pandas streamlit plotly requests

#Seeding Years of Historical Market Metrics
python src/backfill_history.py

#Activating the Live Multi-Market Ingestion Stream (Terminal 1)
python src/ingestion_engine.py

#Launching the Financial Telemetry Hub (Terminal 2)
streamlit run src/dashboard.py