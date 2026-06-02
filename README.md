# Prisma Backend

FastAPI + MongoDB backend for serving the latest factsheet snapshot of the **Spring Street Prisma** fund.

This repository has two runtime components:
- `etl.py` - pulls live market data, computes snapshot metrics (NAV + exposures), and stores the result in MongoDB
- `main.py` - serves REST endpoints that read the latest snapshot for a fund

---

## Tech Stack

- Python
- FastAPI
- Uvicorn
- MongoDB
- Motor (async MongoDB client)
- PyMongo
- yfinance

## Architecture and Approach

This project follows a simple ETL + API read model:

1. **Extract + Transform (`etl.py`)**
   - Fetches latest close prices using `yfinance` for a fixed holdings basket
   - Pulls metadata per ticker (sector, country, display name)
   - Computes weighted NAV and aggregate exposure percentages

2. **Load (`etl.py`)**
   - Writes to MongoDB database `spring_street`, collection `factsheet_snapshots`
   - Uses upsert on `{ fund_id, date }` so rerunning ETL for the same day updates existing data instead of duplicating

3. **Serve (`main.py`)**
   - FastAPI endpoint reads the latest document by sorting snapshots by `date` descending
   - Returns `404` when no factsheet exists for the requested fund

## Prerequisites

- Python 3.9+
- MongoDB running locally at `mongodb://localhost:27017/`
- Internet access (required by `yfinance` in the ETL job)

## Environment Variables and Configuration

There are **no required environment variables** in the current implementation (since it's local)

## Setup (Step-by-Step)

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

## Validation Checklist

After setup, confirm all 3 checks pass:

1. `python etl.py` completes without errors
2. `http://127.0.0.1:8000/docs` opens Swagger UI
3. `GET /api/v1/funds/global-growth-prisma/factsheet/latest` returns `200` with JSON payload

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