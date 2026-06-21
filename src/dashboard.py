import streamlit as st
import psycopg2
import pandas as pd
import plotly.graph_objects as go
import time
import warnings

# Suppress database connection warnings for cleaner production logs
warnings.filterwarnings("ignore", category=UserWarning)

st.set_page_config(page_title="Market Liquidity Engine", layout="wide")
st.title("📊 Market Liquidity Engine — Real-Time Telemetry Dashboard")

def fetch_live_data():
    conn = psycopg2.connect(
        dbname="market_analytics",
        user="quant_engineer",
        password="liquidity_secret",
        host="localhost",
        port="5432"
    )
    query = """
    SELECT timestamp, symbol, price, volume, vwap, market_state 
    FROM asset_telemetry 
    ORDER BY timestamp DESC 
    LIMIT 100;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    if not df.empty:
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df.sort_values('time')

# Wrap the execution loop cleanly to prevent closed event loop race conditions on exit
try:
    df = fetch_live_data()
    
    if not df.empty:
        latest = df.iloc[-1]
        alerts_df = df[df['market_state'] == 'LIQUIDITY_SPIKE']
        
        # ─── METRIC CARDS ROW ───
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Asset Pair", latest['symbol'])
        col2.metric("Live Market Price", f"${float(latest['price']):,.2f}")
        col3.metric("Volume Weighted Avg (VWAP)", f"${float(latest['vwap']):,.2f}")
        col4.metric("Total Spikes Tracked", len(alerts_df))
        
        # ─── REAL-TIME CHART LAYER ───
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['time'], y=df['price'], name='Live Price', line=dict(color='#00ffcc', width=2)))
        fig.add_trace(go.Scatter(x=df['time'], y=df['vwap'], name='Rolling VWAP', line=dict(color='#ff9900', width=1.5, dash='dash')))
        
        if not alerts_df.empty:
            fig.add_trace(go.Scatter(
                x=alerts_df['time'], y=alerts_df['price'],
                mode='markers', name='Liquidity Spike',
                marker=dict(color='red', size=10, symbol='triangle-up')
            ))
        
        fig.update_layout(
            title="High-Frequency Price vs. Institutional VWAP Node Mapping",
            template="plotly_dark",
            xaxis_title="Time Execution Stream",
            yaxis_title="Asset Valuation ($)",
            height=500,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, width="stretch", key="market_chart_node")
        
        # ─── DATA TABLE BUFFER ───
        st.subheader("Raw Transmission Log Buffer")
        st.dataframe(df[['time', 'price', 'volume', 'vwap', 'market_state']].tail(10), width="stretch", key="data_grid_node")
    else:
        st.info("Awaiting streaming telemetry database synchronization...")

    time.sleep(1)
    st.rerun()

except (KeyboardInterrupt, SystemExit, RuntimeError):
    # Intercept event loop terminations quietly
    pass
except Exception as e:
    st.error(f"Database sync pause: {e}")
    time.sleep(2)
    try:
        st.rerun()
    except RuntimeError:
        pass
