import yfinance as yf
from pymongo import MongoClient
from datetime import datetime, timezone
import pandas as pd

# Initialize MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["spring_street"]
snapshots_collection = db["factsheet_snapshots"]

FUND_ID = "global-growth-prisma"

# Define your custom basket and weights
HOLDINGS = [
    {"ticker": "AAPL", "weight": 0.40},
    {"ticker": "MSFT", "weight": 0.35},
    {"ticker": "RELIANCE.NS", "weight": 0.25}
]

def generate_daily_snapshot():
    print(f"Starting dynamic ETL job for {FUND_ID} using live market prices...")
    
    # 1. Extract tickers for batch processing
    tickers = [item["ticker"] for item in HOLDINGS]
    
    # 2. Batch download the latest market data
    # Period='1d' gets the current day's data. We extract the most recent 'Close' price.
    print("Fetching live price data...")
    # Fetch 5 days of data and forward-fill to handle global timezone differences
    raw_data = yf.download(tickers, period="5d", auto_adjust=False)
    price_data = raw_data["Close"].ffill().iloc[-1]
    
    sector_exposure = {}
    country_exposure = {}
    top_holdings = []
    
    # Calculate the dynamic NAV (Weighted Price Basket)
    calculated_nav = 0.0

    for item in HOLDINGS:
        symbol = item["ticker"]
        weight = item["weight"]
        
        # Get the live price from our batch download
        current_price = float(price_data[symbol])
        
        # Add to our theoretical NAV calculation
        calculated_nav += (current_price * weight)
        
        # Fetch metadata for exposures (cached by yfinance to minimize network calls)
        ticker_obj = yf.Ticker(symbol)
        info = ticker_obj.info
        
        sector = info.get("sector", "Unknown")
        country = info.get("country", "Unknown")
        name = info.get("shortName", symbol)
        
        # Aggregate Exposures
        sector_exposure[sector] = sector_exposure.get(sector, 0) + weight
        country_exposure[country] = country_exposure.get(country, 0) + weight
        
        top_holdings.append({
            "ticker": symbol,
            "name": name,
            "weight": round(weight * 100, 2)
        })

    # Format the data for MongoDB
    snapshot_document = {
        "fund_id": FUND_ID,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "nav": round(calculated_nav, 2), # Insert the dynamically calculated NAV
        "exposures": {
            "sectors": [{"name": k, "weight": round(v * 100, 2)} for k, v in sector_exposure.items()],
            "geography": [{"name": k, "weight": round(v * 100, 2)} for k, v in country_exposure.items()]
        },
        "top_holdings": sorted(top_holdings, key=lambda x: x["weight"], reverse=True)
    }

    # Upsert into MongoDB
    snapshots_collection.update_one(
        {"fund_id": FUND_ID, "date": snapshot_document["date"]},
        {"$set": snapshot_document},
        upsert=True
    )
    
    print(f"ETL job completed. Calculated NAV: ${round(calculated_nav, 2)}. Data saved to MongoDB.")

if __name__ == "__main__":
    generate_daily_snapshot()