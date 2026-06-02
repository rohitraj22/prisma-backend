from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from etl import generate_daily_snapshot 

app = FastAPI(title="Spring Street Prisma API")

# Read URI from environment (Render dashboard in production, .env file locally)
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
client = AsyncIOMotorClient(MONGO_URI)
db = client["spring_street"]

# Pydantic models for Swagger UI documentation
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
    # Sort by date descending (-1) to grab the newest snapshot
    document = await db["factsheet_snapshots"].find_one(
        {"fund_id": fund_id},
        sort=[("date", -1)]
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Factsheet not found for this fund")
        
    # Remove the internal MongoDB ObjectId before returning
    document.pop("_id", None)
    return document