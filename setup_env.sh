
echo "Starting self-contained database architecture..."
if [ ! -d "postgres_data" ]; then
    echo "Initializing fresh postgres data cluster..."
    initdb -D postgres_data
fi

pg_ctl -D postgres_data -l postgres_server.log start 2>/dev/null || echo "PostgreSQL server process is already active."

echo "Creating local time-series data caches..."
mkdir -p data/raw_ticks
mkdir -p data/processed_analytics

echo "Native storage environment is optimized and ready."
