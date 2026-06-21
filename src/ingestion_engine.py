import asyncio
import json
import websockets
import os
import ssl
from stream_processor import MarketStreamProcessor

STREAM_URL = "wss://stream.binance.com:9443/ws/btcusdt@ticker"

# Initialize our in-memory data stream queue and analytical processor
data_stream_queue = asyncio.Queue(maxsize=5000)
processor = MarketStreamProcessor(window_size=50, volatility_multiplier=2.5)

async def market_data_producer(queue):
    """
    Producer: High-speed WebSocket ingestion layer that captures live market ticks
    and injects them immediately into our processing stream buffer queue.
    """
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    async with websockets.connect(STREAM_URL, ssl=ssl_context) as websocket:
        print("[PRODUCER] Pipeline active. Connected to live financial stream.")
        while True:
            try:
                raw_payload = await websocket.recv()
                tick_data = json.loads(raw_payload)
                
                # Push tick data directly to the pipeline buffer queue (non-blocking)
                try:
                    queue.put_nowait(tick_data)
                except asyncio.QueueFull:
                    # Drop old data safely if backpressure spikes heavily
                    queue.get_nowait()
                    queue.put_nowait(tick_data)
                    
            except websockets.exceptions.ConnectionClosed:
                print("[PRODUCER] Stream disconnected. Reconnecting...")
                await asyncio.sleep(5)
                break

async def market_data_consumer(queue):
    """
    Consumer: Background analytical listener that continuously drains the buffer queue,
    calculates real-time financial metrics, and checks for market volatility.
    """
    print("[CONSUMER] Analytical listener active. Awaiting processing metrics...")
    while True:
        tick_data = await queue.get()
        
        # Route the live tick through our mathematical engine
        analytics = processor.process_tick(tick_data)
        
        if analytics:
            alert_prefix = "🔥 [VOLATILITY ALERT]" if analytics['alert'] == "LIQUIDITY_SPIKE" else "📊 [NORMAL]"
            print(f"{alert_prefix} {analytics['symbol']} | Price: {analytics['price']} | VWAP: {analytics['vwap']} | Vol: {analytics['volume']}")
            
        queue.task_done()

async def main():
    # Spin up the concurrent Producer and Consumer tasks simultaneously
    await asyncio.gather(
        market_data_producer(data_stream_queue),
        market_data_consumer(data_stream_queue)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SYSTEM] Live quantitative pipeline safely terminated.")
