import base64
import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import Dict
from google.cloud import storage
from google.oauth2 import service_account
import logging
from analyzer import analyze_financial_data_from_question
from enum import Enum
from constants import INCOME_STATEMENT_METRICS, BALANCE_SHEET_METRICS, CASH_FLOW_METRICS

load_dotenv()

OUTPUT_DIR = "outputs"
BUCKET_NAME = "stock_agent_financial_report"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://stonkie.netlify.app"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

class ReportType(Enum):
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"

@app.get("/api/financial-data/{ticker}/{report_type}")
async def get_financial_data(ticker: str, report_type: str) -> Dict:
    """
    Get financial data for a specific ticker and report type
    report_type can be: income_statement, balance_sheet, or cash_flow
    """
    try:
        # Validate and convert report_type to enum
        try:
            report_type_enum = ReportType(report_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid report type. Must be one of: {[rt.value for rt in ReportType]}"
            )

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
        
        # Filter columns based on report type
        metric_mapping = {
            ReportType.INCOME_STATEMENT: INCOME_STATEMENT_METRICS,
            ReportType.BALANCE_SHEET: BALANCE_SHEET_METRICS,
            ReportType.CASH_FLOW: CASH_FLOW_METRICS
        }
        
        selected_metrics = metric_mapping[report_type_enum]
        first_col_name = df.columns[0]
        df = df[df[first_col_name].str.lower().isin(selected_metrics)]
        
        # Convert the dataframe to JSON format
        return {
            "data": df.to_dict('records'),
            "columns": df.columns.tolist()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/company/analyze")
async def analyze_financial_data(request: Request):
    """
    Analyze financial statements for a given ticker symbol based on a specific question
    
    Args:
        request (Request): FastAPI request object containing the question and ticker in body
    Returns:
        dict: Analysis response and status
    """
    try:
        body = await request.json()
        question = body.get('question')
        ticker = body.get('ticker')
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required in request body")

        analysis_result = analyze_financial_data_from_question(ticker, question)

        return {
            "status": "success",
            "data": analysis_result
        }
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Something went wrong. Please try again later.")
