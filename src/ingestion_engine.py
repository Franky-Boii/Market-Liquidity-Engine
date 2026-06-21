import asyncio
import json
import websockets
import os
import ssl

STREAM_URL = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
OUTPUT_DIR = "data/raw_ticks"

async def stream_market_data():
    print(f"Connecting to live financial market feed: {STREAM_URL}...")
    
    # Create an SSL context that skips certificate verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    async with websockets.connect(STREAM_URL, ssl=ssl_context) as websocket:
        print("Connection established. Streaming real-time tick logs...")
        
        while True:
            try:
                raw_payload = await websocket.recv()
                tick_data = json.loads(raw_payload)
                
                symbol = tick_data.get('s')
                price = tick_data.get('c')
                volume = tick_data.get('v')
                timestamp = tick_data.get('E')
                
                print(f"[{timestamp}] {symbol} | Price: {price} | Vol: {volume}")
                
            except websockets.exceptions.ConnectionClosed:
                print("Connection broken. Attempting reconnection protocol...")
                await asyncio.sleep(5)
                break
            except Exception as e:
                print(f"Streaming anomaly detected: {e}")

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        asyncio.run(stream_market_data())
    except KeyboardInterrupt:
        print("\nIngestion engine safely shut down by quantitative engineer.")
