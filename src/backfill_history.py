import requests
import psycopg2
import time
from datetime import datetime, timedelta

# Target configurations
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
DB_PARAMS = {
    "dbname": "market_analytics",
    "user": "quant_engineer",
    "password": "liquidity_secret",
    "host": "localhost",
    "port": "5432"
}

def get_connection():
    return psycopg2.connect(**DB_PARAMS)

def backfill_symbol(symbol, days_back=365):
    """
    Fetches historical daily close prices for the asset and passes them directly to Postgres.
    """
    print(f"⏳ Backfilling historical data for {symbol} over the past {days_back} days...")
    
    # Binance REST API for historical K-lines (candlesticks)
    url = "https://api.binance.com/api/v3/klines"
    
    # Calculate intervals
    start_time = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)
    
    params = {
        "symbol": symbol,
        "interval": "1d",
        "startTime": start_time,
        "limit": 1000
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        inserted_rows = 0
        for bar in data:
            # Extract historical nodes: open time, close price, volume
            timestamp = bar[0]
            close_price = float(bar[4])
            volume = float(bar[5])
            
            # For historical data, VWAP mirrors close price since we are compiling day chunks
            vwap = close_price 
            
            insert_query = """
            INSERT INTO asset_telemetry (timestamp, symbol, price, volume, vwap, market_state)
            VALUES (%s, %s, %s, %s, %s, 'NORMAL')
            ON CONFLICT DO NOTHING;
            """
            cursor.execute(insert_query, (timestamp, symbol, close_price, volume, vwap))
            inserted_rows += 1
            
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Successfully backfilled {inserted_rows} historical daily nodes for {symbol}.")
        
    except Exception as e:
        print(f"❌ Error historical mining for {symbol}: {e}")

if __name__ == "__main__":
    # Backfill the past 3 years (approx 1095 days) for each configured asset
    for symbol in SYMBOLS:
        backfill_symbol(symbol, days_back=1095)
        time.sleep(1) # Polite API spacing interval
