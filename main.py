from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Dict
import os
from dotenv import load_dotenv

# Import your ETL function so the API can trigger it
from etl import generate_daily_snapshot 

load_dotenv()

app = FastAPI(title="Spring Street Prisma API")

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
client = AsyncIOMotorClient(MONGO_URI)
db = client["spring_street"]

class ExposureItem(BaseModel):
    name: str
    weight: float

class HoldingItem(BaseModel):
    ticker: str
    name: str
    weight: float

class FactsheetSnapshot(BaseModel):
    fund_id: str
    date: str
    nav: float
    exposures: Dict[str, List[ExposureItem]]
    top_holdings: List[HoldingItem]

@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "operational", "message": "Spring Street API is running"}

@app.get("/api/v1/funds/{fund_id}/factsheet/latest", response_model=FactsheetSnapshot, tags=["Factsheet"])
async def get_latest_factsheet(fund_id: str):
    """
    Fetches the most recent factsheet data for a specific fund to populate the UI.
    """
    document = await db["factsheet_snapshots"].find_one(
        {"fund_id": fund_id},
        sort=[("date", -1)]
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Factsheet not found for this fund")
        
    document.pop("_id", None)
    return document

# --- ADD THIS MISSING ADMIN SECTION ---
@app.post("/api/v1/admin/run-etl", tags=["Admin"])
async def trigger_etl():
    """
    Manually triggers the ETL pipeline to fetch live Yahoo Finance data 
    and populate the MongoDB Atlas database.
    """
    try:
        generate_daily_snapshot()
        return {"status": "success", "message": "ETL pipeline executed successfully and data saved to Atlas."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ETL failed: {str(e)}")