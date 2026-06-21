import asyncio
import websockets
import json
import psycopg2
import ssl
from stream_processor import MarketStreamProcessor

# Initialize global processor and local async ingestion queue
data_queue = asyncio.Queue()
processor = MarketStreamProcessor(window_size=20, volatility_multiplier=3.0)

def save_to_database(analytics):
    try:
        conn = psycopg2.connect(
            dbname="market_analytics",
            user="quant_engineer",
            password="liquidity_secret",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO asset_telemetry (timestamp, symbol, price, volume, vwap, market_state)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            analytics["timestamp"],
            analytics["symbol"],
            analytics["price"],
            analytics["volume"],
            analytics["vwap"],
            analytics["alert"]
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database insertion anomaly: {e}")

async def producer():
    # Multi-stream payload layout for major crypto-to-fiat anchors
    streams = "btcusdt@ticker/ethusdt@ticker/solusdt@ticker/bnbusdt@ticker"
    uri = f"wss://stream.binance.com:9443/stream?streams={streams}"
    
    # Re-build our SSL context that skips verification checks on your Mac
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    while True:
        try:
            # Re-integrate the ssl parameter into our multiplex streaming connection
            async with websockets.connect(uri, ssl=ssl_context) as websocket:
                print(f"📡 Multi-stream websocket pipeline connected to clusters...")
                async for message in websocket:
                    raw_data = json.loads(message)
                    tick = raw_data.get("data", {})
                    if tick:
                        await data_queue.put(tick)
        except Exception as e:
            print(f"Connection dropped. Re-establishing secure socket tier in 3 seconds... ({e})")
            await asyncio.sleep(3)

async def consumer():
    print("⚙️ Asynchronous pipeline analytical worker thread activated.")
    while True:
        tick = await data_queue.get()
        analytics = processor.process_tick(tick)
        if analytics:
            save_to_database(analytics)
        data_queue.task_done()

async def main():
    await asyncio.gather(producer(), consumer())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPipeline shut down gracefully.")
