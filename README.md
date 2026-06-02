# Prisma Backend

FastAPI + MongoDB backend for serving the latest factsheet snapshot of the **Spring Street Prisma** fund.

The project has two main parts:
- `etl.py`: fetches live market data with `yfinance`, builds a daily snapshot, and upserts it into MongoDB.
- `main.py`: exposes a REST API to retrieve the latest factsheet snapshot for a fund.

## Tech Stack

- Python
- FastAPI
- Uvicorn
- MongoDB
- Motor (async MongoDB client)
- PyMongo
- yfinance

## Prerequisites

- Python 3.9+
- MongoDB running locally at `mongodb://localhost:27017/`
- Internet access (required by `yfinance` in the ETL job)

## Setup

1. Clone the repository:

```bash
git clone https://github.com/rohitraj22/prisma-backend.git
cd prisma-backend
```

2. (Recommended) Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the ETL Job

Generate (or update) the daily factsheet snapshot in MongoDB:

```bash
python etl.py
```

What this does:
- Uses the configured holdings basket:
  - `AAPL` (40%)
  - `MSFT` (35%)
  - `RELIANCE.NS` (25%)
- Downloads recent close prices via `yfinance`
- Calculates a weighted NAV
- Builds sector and geography exposure breakdowns
- Upserts into `spring_street.factsheet_snapshots`

## Run the API

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Default URL:
- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

## API Endpoints

### Health Check

`GET /`

Sample response:

```json
{
  "status": "operational",
  "message": "Spring Street API is running"
}
```

### Latest Factsheet by Fund

`GET /api/v1/funds/{fund_id}/factsheet/latest`

Example:

```bash
curl http://127.0.0.1:8000/api/v1/funds/global-growth-prisma/factsheet/latest
```

Success response shape:

```json
{
  "fund_id": "global-growth-prisma",
  "date": "2026-06-02",
  "nav": 123.45,
  "exposures": {
    "sectors": [
      { "name": "Technology", "weight": 75.0 }
    ],
    "geography": [
      { "name": "United States", "weight": 75.0 }
    ]
  },
  "top_holdings": [
    { "ticker": "AAPL", "name": "Apple Inc.", "weight": 40.0 }
  ]
}
```

If no snapshot exists for the requested fund, the API returns `404`.

## Database Details

- Database: `spring_street`
- Collection: `factsheet_snapshots`
- Document key used for upsert: `{ fund_id, date }`

## Notes

- Run the ETL job before calling the factsheet endpoint, otherwise the API may return `404`.
- The ETL currently writes snapshots only for:
  - `fund_id = global-growth-prisma`
- MongoDB connection strings are currently hardcoded in both `main.py` and `etl.py` as local URLs.