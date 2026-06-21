import streamlit as st
import psycopg2
import pandas as pd
import plotly.graph_objects as go
import time
import warnings
from datetime import datetime, timedelta, date

warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="Market Liquidity Engine", layout="wide")
st.title("📊 Market Liquidity Engine — Executive Telemetry Hub")

# ─── SIDEBAR FILTER ENGINE ───
st.sidebar.header("🎛️ Operational Control Panel")

selected_market = st.sidebar.selectbox(
    "Select Target Market Instrument",
    ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"],
    index=0
)

time_frame = st.sidebar.radio(
    "Historical Looking Window Preset",
    ["Live Stream (Default)", "Past 24 Hours", "Past 7 Days", "Custom Date Range"]
)

start_time_ms = 0
end_time_ms = int(time.time() * 1000)

if time_frame == "Past 24 Hours":
    start_time_ms = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
elif time_frame == "Past 7 Days":
    start_time_ms = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
elif time_frame == "Custom Date Range":
    date_bounds = st.sidebar.date_input(
        "Select Active Boundaries",
        value=(date.today() - timedelta(days=7), date.today())
    )
    if isinstance(date_bounds, tuple) and len(date_bounds) == 2:
        start_time_ms = int(datetime.combine(date_bounds[0], datetime.min.time()).timestamp() * 1000)
        end_time_ms = int(datetime.combine(date_bounds[1], datetime.max.time()).timestamp() * 1000)

def fetch_filtered_data(symbol, start_ms, end_ms, use_live_limit=False):
    conn = psycopg2.connect(
        dbname="market_analytics", user="quant_engineer", password="liquidity_secret", host="localhost", port="5432"
    )
    
    if use_live_limit:
        query = """
        SELECT timestamp, symbol, price, volume, vwap, market_state 
        FROM asset_telemetry 
        WHERE symbol = %s
        ORDER BY timestamp DESC 
        LIMIT 150;
        """
        df = pd.read_sql(query, conn, params=(symbol,))
    else:
        query = """
        SELECT timestamp, symbol, price, volume, vwap, market_state 
        FROM asset_telemetry 
        WHERE symbol = %s AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp DESC;
        """
        df = pd.read_sql(query, conn, params=(symbol, start_ms, end_ms))
        
    conn.close()
    
    # Crucial Fix: Only attempt column transformations if rows actually exist
    if not df.empty and 'timestamp' in df.columns:
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df.sort_values('time')
    return pd.DataFrame() # Return clean empty structure instead of crashing

try:
    is_live = (time_frame == "Live Stream (Default)")
    df = fetch_filtered_data(selected_market, start_time_ms, end_time_ms, use_live_limit=is_live)
    
    if not df.empty:
        latest = df.iloc[-1]
        alerts_df = df[df['market_state'] == 'LIQUIDITY_SPIKE']
        
        # ─── METRIC CARDS ROW ───
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Active Node Anchor", latest['symbol'])
        col2.metric("Current Execution Value", f"${float(latest['price']):,.2f}")
        col3.metric("Institutional Volume VWAP", f"${float(latest['vwap']):,.2f}")
        col4.metric("Anomalies Flagged", len(alerts_df))
        
        # ─── REAL-TIME CHART LAYER ───
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['time'], y=df['price'], name='Execution Path', line=dict(color='#00ffcc', width=2)))
        fig.add_trace(go.Scatter(x=df['time'], y=df['vwap'], name='Anchor Baseline (VWAP)', line=dict(color='#ff9900', width=1.5, dash='dash')))
        
        if not alerts_df.empty:
            fig.add_trace(go.Scatter(
                x=alerts_df['time'], y=alerts_df['price'],
                mode='markers', name='Liquidity Sweep Trigger',
                marker=dict(color='#ff3333', size=11, symbol='triangle-up')
            ))
        
        fig.update_layout(
            title=f"Time Series Telemetry Grid Mapping: {selected_market}",
            template="plotly_dark",
            xaxis_title="System Execution Timeline",
            yaxis_title="Asset Valuation ($)",
            height=520,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, width="stretch", key="market_chart_node")
        
        # ─── DATA TABLE BUFFER ───
        st.subheader("Granular Transmission Log Index")
        st.dataframe(df[['time', 'price', 'volume', 'vwap', 'market_state']].tail(15), width="stretch", key="data_grid_node")
    else:
        st.warning(f"🔍 No logged telemetry data found for {selected_market} within the selected timeframe. Start the ingestion engine or adjust your historical boundaries.")

    if is_live:
        time.sleep(1)
        st.rerun()

except (KeyboardInterrupt, SystemExit, RuntimeError):
    pass
except Exception as e:
    st.error(f"Operational pipeline interruption: {e}")
