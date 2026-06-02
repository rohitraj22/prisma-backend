# Prisma Backend

FastAPI + MongoDB backend for serving the latest factsheet snapshot of the **Spring Street Prisma** fund.

**Live API Deployment:** https://prisma-backend-api.onrender.com/docs

---

## Overview

This repository has two runtime components:

* **`etl.py`** – Pulls live market data, computes snapshot metrics (NAV + exposures), and stores the result in MongoDB.
* **`main.py`** – Serves REST endpoints that read the latest snapshot for a fund.

---

## Tech Stack

### Core

* Python
* FastAPI
* Uvicorn

### Database

* MongoDB Atlas (Cloud)
* Motor (Async Client)
* PyMongo

### Data Ingestion

* yfinance
* pandas

### Environment & Deployment

* python-dotenv
* Render

---

## Architecture and Approach

This project follows an **ETL + API Read Model** designed for both local development and cloud deployment.

### 1. Extract + Transform (`etl.py`)

* Fetches latest close prices using `yfinance` for a fixed holdings basket.
* Pulls metadata per ticker (sector, country, display name).
* Computes weighted NAV and aggregate exposure percentages.

### 2. Load (`etl.py` → MongoDB Atlas)

* Writes data to a MongoDB cluster:
  * Database: `spring_street`
  * Collection: `factsheet_snapshots`

* Uses an upsert on `{ fund_id, date }` so rerunning the ETL for the same day updates the existing document rather than creating duplicates.

### 3. Serve (`main.py`)

* FastAPI endpoints read the latest document by sorting snapshots by date in descending order.
* Includes an Admin POST endpoint to manually trigger the ETL pipeline remotely.

---

## Cloud Testing (Quickest Way)

The API is fully deployed on Render and connected to a MongoDB Atlas cluster.

You can test the application without downloading the code.

### Steps

1. Open the Swagger UI:

   ```
   https://prisma-backend-api.onrender.com/docs
   ```

2. Expand the **Factsheet GET endpoint**.

3. Click **Try it out**.

4. Enter the following `fund_id`:

   ```text
   global-growth-prisma
   ```

5. Click **Execute**.

> **Note:** A POST endpoint (`/api/v1/admin/run-etl`) exists to trigger the ETL pipeline in production. However, because free-tier shared IPs are occasionally rate-limited by Yahoo Finance, the cloud database is routinely hydrated via local script execution.

---

## Local Development Setup

### Prerequisites

* Python 3.9+
* MongoDB (Local instance or Atlas connection string)
* Internet connection (required by `yfinance`)

---

### 1. Clone the Repository

```bash
git clone https://github.com/rohitraj22/prisma-backend.git
cd prisma-backend
```

---

### 2. Create and Activate a Virtual Environment

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file in the project root.

```bash
touch .env
```

Add your MongoDB connection string:

```env
MONGODB_URI=mongodb://localhost:27017/
```

Or use MongoDB Atlas:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0...
```

---

### 5. Run the ETL Pipeline

Generate the latest factsheet snapshot and populate the database.

```bash
python etl.py
```

This will:

* Fetch live market data for:
  * AAPL
  * MSFT
  * RELIANCE.NS
* Calculate NAV
* Compute exposure breakdowns
* Upsert the snapshot into MongoDB

---

### 6. Run the API Server

Start the FastAPI application:

```bash
uvicorn main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### Health Check

**GET /**

#### Response

```json
{
  "status": "operational",
  "message": "Spring Street API is running"
}
```

---

### Latest Factsheet by Fund

**GET /api/v1/funds/{fund_id}/factsheet/latest**

#### Example Response

```json
{
  "fund_id": "global-growth-prisma",
  "date": "2026-06-02",
  "nav": 608.11,
  "exposures": {
    "sectors": [
      {
        "name": "Technology",
        "weight": 75.0
      }
    ],
    "geography": [
      {
        "name": "United States",
        "weight": 75.0
      }
    ]
  },
  "top_holdings": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "weight": 40.0
    }
  ]
}
```

#### Error Response

Returns:

```http
404 Not Found
```

if the ETL has not been run for the requested fund.

---

### Trigger ETL (Admin)

**POST /api/v1/admin/run-etl**

Executes:

```python
generate_daily_snapshot()
```

to refresh the latest factsheet snapshot.

---

## Database Details

| Property   | Value                 |
| ---------- | --------------------- |
| Database   | `spring_street`       |
| Collection | `factsheet_snapshots` |
| Upsert Key | `{ fund_id, date }`   |

---

## License

This project is intended for educational and assessment purposes.

---

## Author

**Rohit Raj**