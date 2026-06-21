import collections
import time

class MarketStreamProcessor:
    def __init__(self, window_size=100, volatility_multiplier=2.0):
        # Sliding window buffer to track recent ticks
        self.tick_window = collections.deque(maxlen=window_size)
        self.volatility_multiplier = volatility_multiplier

    def process_tick(self, tick_data):
        """
        Ingests a raw market tick and applies streaming metrics on the fly.
        """
        try:
            price = float(tick_data['c'])
            volume = float(tick_data['v'])
            timestamp = tick_data['E']
            symbol = tick_data['s']
        except (KeyError, ValueError) as e:
            return None

        # Append current tick to our moving window
        self.tick_window.append((price, volume))

        # Calculate Rolling VWAP: Sum(Price * Volume) / Sum(Volume)
        total_pv = sum(p * v for p, v in self.tick_window)
        total_volume = sum(v for p, v in self.tick_window)
        vwap = total_pv / total_volume if total_volume > 0 else price

        # Detect Volatility Spikes: Flag if current volume is significantly higher than the window average
        avg_volume = total_volume / len(self.tick_window)
        is_volatility_spike = len(self.tick_window) > 10 and volume > (avg_volume * self.volatility_multiplier)

        # Structure out our enriched, processed analytical package
        analytics_payload = {
            "timestamp": timestamp,
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "vwap": round(vwap, 2),
            "alert": "LIQUIDITY_SPIKE" if is_volatility_spike else "NORMAL"
        }

        return analytics_payload
