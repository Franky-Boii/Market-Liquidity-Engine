import numpy as np

class MarketStreamProcessor:
    def __init__(self, window_size=30, z_score_threshold=2.5):
        self.window_size = window_size
        self.threshold = z_score_threshold
        # Maintain separate rolling memory buffers for our monitored asset nodes
        self.buffers = {}

    def process_tick(self, tick):
        try:
            symbol = tick.get("s") # Asset symbol (e.g., BTCUSDT)
            price = float(tick.get("c")) # Current close price
            volume = float(tick.get("v")) # Traded volume chunk
            timestamp = int(tick.get("E")) # System event epoch time

            if symbol not in self.buffers:
                self.buffers[symbol] = {"prices": [], "volumes": []}

            # Append fresh telemetry into our tracking arrays
            self.buffers[symbol]["prices"].append(price)
            self.buffers[symbol]["volumes"].append(volume)

            # Enforce sliding memory window boundary limits
            if len(self.buffers[symbol]["prices"]) > self.window_size:
                self.buffers[symbol]["prices"].pop(0)
                self.buffers[symbol]["volumes"].pop(0)

            # Convert sliding lists directly to high-performance NumPy arrays
            price_array = np.array(self.buffers[symbol]["prices"])
            volume_array = np.array(self.buffers[symbol]["volumes"])

            # Vectorized VWAP: sum(Price * Volume) / sum(Volume)
            vwap = np.sum(price_array * volume_array) / np.sum(volume_array)

            # NumPy Dynamic Vector Math Model: Rolling Volatility Standard Deviation Z-Score
            market_state = "NORMAL"
            if len(price_array) >= 5:
                mean_price = np.mean(price_array)
                std_price = np.std(price_array)
                
                if std_price > 0:
                    # Calculate how many standard deviations the current tick is from the mean
                    z_score = np.abs(price - mean_price) / std_price
                    if z_score > self.threshold:
                        market_state = "LIQUIDITY_SPIKE"

            return {
                "timestamp": timestamp,
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "vwap": round(float(vwap), 2),
                "alert": market_state
            }
        except Exception as e:
            print(f"Mathematical processing anomaly: {e}")
            return None
