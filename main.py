import base64
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import Dict
from google.cloud import storage
from google.oauth2 import service_account

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

OUTPUT_DIR = "outputs"
BUCKET_NAME = "stock_agent_financial_report"

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://stock-agent.netlify.app"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/financial-data/{ticker}/{report_type}")
async def get_financial_data(ticker: str, report_type: str) -> Dict:
    """
    Get financial data for a specific ticker and report type
    report_type can be: income_statement, balance_sheet, or cash_flow
    """
    try:
        # Get the CSV from google cloud storage
        credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if not credentials:
            print("❌ Google credentials not found in environment variables")
            return {
                "data": [],
            }

        credentials_dict = json.loads(base64.b64decode(credentials).decode('utf-8'))
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        storage_client = storage.Client(credentials=credentials)

        csv_blob = storage_client.bucket(BUCKET_NAME).blob(f"{ticker.lower()}_{report_type}.csv")
        
        # If the CSV doesn't exist, return an empty data object
        if not csv_blob.exists():
            return {
                "data": [],
                "columns": []
            }
        
        # Download the blob as string and convert to bytes
        csv_content = csv_blob.download_as_string()
        
        # Use pandas to read the CSV content from the string
        df = pd.read_csv(pd.io.common.BytesIO(csv_content))
        
        # Convert the dataframe to JSON format
        return {
            "data": df.to_dict('records'),  # Each row becomes a dictionary
            "columns": df.columns.tolist()   # List of column names
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))