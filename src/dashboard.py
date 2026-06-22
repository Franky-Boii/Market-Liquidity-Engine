import streamlit as st
import psycopg2
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm
import time
import warnings
from datetime import datetime, timedelta, date, time as dt_time

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

chart_style = st.sidebar.radio(
    "Select Visual Representation",
    ["Standard Line Chart", "Financial Candlestick", "NumPy Volatility Distribution Graph"]
)

time_frame = st.sidebar.radio(
    "Historical Looking Window Preset",
    ["Live Stream (Default)", "Precision Custom Time Boundary"]
)

# Initialize boundary metrics
start_time_ms = 0
end_time_ms = int(time.time() * 1000)

# Perfect Date & Time Filter Implementation
if time_frame == "Precision Custom Time Boundary":
    st.sidebar.subheader("📅 Precise Date-Time Anchors")
    
    col_d1, col_d2 = st.sidebar.columns(2)
    start_date = col_d1.date_input("Start Date", date.today() - timedelta(days=3))
    end_date = col_d2.date_input("End Date", date.today())
    
    start_hour, start_min = st.sidebar.slider("Start Time Window", 0, 23, 0), st.sidebar.slider("Start Minute", 0, 59, 0)
    end_hour, end_min = st.sidebar.slider("End Time Window", 0, 23, 23), st.sidebar.slider("End Minute", 0, 59, 59)
    
    # Compile inputs into precise datetime timestamps
    dt_start = datetime.combine(start_date, dt_time(start_hour, start_min))
    dt_end = datetime.combine(end_date, dt_time(end_hour, end_min))
    
    start_time_ms = int(dt_start.timestamp() * 1000)
    end_time_ms = int(dt_end.timestamp() * 1000)

def fetch_filtered_data(symbol, start_ms, end_ms, use_live_limit=False):
    conn = psycopg2.connect(
        dbname="market_analytics", user="quant_engineer", password="liquidity_secret", host="localhost", port="5432"
    )
    if use_live_limit:
        query = """
        SELECT timestamp, symbol, price, volume, vwap, market_state 
        FROM asset_telemetry 
        WHERE symbol = %s ORDER BY timestamp DESC LIMIT 400;
        """
        df = pd.read_sql(query, conn, params=(symbol,))
    else:
        query = """
        SELECT timestamp, symbol, price, volume, vwap, market_state 
        FROM asset_telemetry 
        WHERE symbol = %s AND timestamp BETWEEN %s AND %s ORDER BY timestamp DESC;
        """
        df = pd.read_sql(query, conn, params=(symbol, start_ms, end_ms))
    conn.close()
    
    if not df.empty and 'timestamp' in df.columns:
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['price'] = df['price'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['vwap'] = df['vwap'].astype(float)
        return df.sort_values('time')
    return pd.DataFrame()

try:
    is_live = (time_frame == "Live Stream (Default)")
    df = fetch_filtered_data(selected_market, start_time_ms, end_time_ms, use_live_limit=is_live)
    
    if not df.empty:
        latest = df.iloc[-1]
        alerts_df = df[df['market_state'] == 'LIQUIDITY_SPIKE']
        
        # ─── METRIC CARDS ROW ───
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Active Node Anchor", latest['symbol'])
        col2.metric("Current Value", f"${latest['price']:,.2f}")
        col3.metric("Vector VWAP Anchor", f"${latest['vwap']:,.2f}")
        col4.metric("Anomalies Flagged", len(alerts_df))
        
        fig = go.Figure()
        
        # ─── VISUAL RENDER ROUTER ───
        if chart_style == "Standard Line Chart":
            fig.add_trace(go.Scatter(x=df['time'], y=df['price'], name='Price Path', line=dict(color='#2962FF', width=2)))
            fig.add_trace(go.Scatter(x=df['time'], y=df['vwap'], name='Rolling Vector VWAP', line=dict(color='#FF9800', width=1.5, dash='dash')))
            fig.update_layout(yaxis_title="Asset Valuation ($)")

        elif chart_style == "Financial Candlestick":
            df_candlestick = df.copy()
            df_candlestick.set_index('time', inplace=True)
            interval = "1Min" if is_live else "1D"
            ohlc = df_candlestick['price'].resample(interval).ohlc()
            volume_resampled = df_candlestick['volume'].resample(interval).sum()
            ohlc = ohlc.join(volume_resampled).dropna().reset_index()
            
            fig.add_trace(go.Candlestick(
                x=ohlc['time'], open=ohlc['open'], high=ohlc['high'], low=ohlc['low'], close=ohlc['close'],
                name='Market Candles',
                increasing=dict(fillcolor='#089981', line=dict(color='#089981', width=1.5)),
                decreasing=dict(fillcolor='#F23645', line=dict(color='#F23645', width=1.5))
            ))
            fig.update_layout(xaxis_rangeslider_visible=False, yaxis_title="Candle Valuation ($)")

        elif chart_style == "NumPy Volatility Distribution Graph":
            # NumPy Processing: Compute log returns to model market volatility distribution
            prices = df['price'].to_numpy()
            if len(prices) > 2:
                log_returns = np.diff(np.log(prices))
                
                # Render empirical data distribution histogram bars
                fig.add_trace(go.Histogram(
                    x=log_returns, nbinsx=40, name='Empirical Returns Density',
                    histnorm='probability density', marker_color='#2962FF', opacity=0.65
                ))
                
                # NumPy Model Evaluation: Overlap ideal Gaussian normal bell curve
                x_axis_line = np.linspace(np.min(log_returns), np.max(log_returns), 200)
                mean, std = np.mean(log_returns), np.std(log_returns)
                if std > 0:
                    y_axis_line = norm.pdf(x_axis_line, mean, std)
                    fig.add_trace(go.Scatter(
                        x=x_axis_line, y=y_axis_line, name='Gaussian Normal Curve Model',
                        line=dict(color='#FF9800', width=2.5)
                    ))
                fig.update_layout(yaxis_title="Probability Density Frequency", xaxis_title="Log Return Shifts")
            else:
                st.info("Gathering additional market nodes to generate distribution metrics...")

        fig.update_layout(
            title=f"{chart_style} Workspace Matrix: {selected_market}",
            template="plotly_dark", height=580, margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='#131722', plot_bgcolor='#131722',
            xaxis=dict(gridcolor='#1f222e'), yaxis=dict(gridcolor='#1f222e')
        )
        st.plotly_chart(fig, width="stretch", key="market_chart_node")
        
        st.subheader("Granular Transmission Log Index")
        st.dataframe(df[['time', 'price', 'volume', 'vwap', 'market_state']].tail(15), width="stretch", key="data_grid_node")
    else:
        st.warning(f"🔍 No logged telemetry data found for {selected_market} within the selected date-time boundaries.")

    if is_live:
        time.sleep(1)
        st.rerun()

except (KeyboardInterrupt, SystemExit, RuntimeError):
    pass
except Exception as e:
    st.error(f"Operational pipeline interruption: {e}")
