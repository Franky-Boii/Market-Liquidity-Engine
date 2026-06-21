import psycopg2
from psycopg2.extras import execute_values
import datetime

class MarketDatabaseSink:
    def __init__(self):
        # Database connection configuration mapped to your native credentials
        self.conn_params = {
            "dbname": "market_analytics",
            "user": "quant_engineer",
            "password": "liquidity_secret",
            "host": "localhost",
            "port": "5432"
        }
        self.initialize_schema()

    def get_connection(self):
        return psycopg2.connect(**self.conn_params)

    def initialize_schema(self):
        """
        Executes a schema migration to build our high-performance analytical storage table.
        """
        query = """
        CREATE TABLE IF NOT EXISTS asset_telemetry (
            id SERIAL PRIMARY KEY,
            timestamp BIGINT NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            symbol VARCHAR(20) NOT NULL,
            price NUMERIC(18, 4) NOT NULL,
            volume NUMERIC(18, 4) NOT NULL,
            vwap NUMERIC(18, 4) NOT NULL,
            market_state VARCHAR(20) NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON asset_telemetry (timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_telemetry_symbol ON asset_telemetry (symbol);
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query)
            conn.commit()
            print("[DATABASE] Telemetry storage tables initialized and indexed.")
        except Exception as e:
            conn.rollback()
            print(f"[DATABASE ERROR] Schema initialization failed: {e}")
        finally:
            conn.close()

    def save_analytics(self, analytics_payload):
        """
        Persists a calculated streaming analytics package securely to PostgreSQL.
        """
        query = """
        INSERT INTO asset_telemetry (timestamp, symbol, price, volume, vwap, market_state)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (
                    analytics_payload['timestamp'],
                    analytics_payload['symbol'],
                    float(analytics_payload['price']),
                    float(analytics_payload['volume']),
                    float(analytics_payload['vwap']),
                    analytics_payload['alert']
                ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[DATABASE ERROR] Failed to persist telemetry row: {e}")
        finally:
            conn.close()
