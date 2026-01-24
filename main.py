from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from modules.technical import calculate_technical_indicators
from modules.fundamental import get_fundamental_analysis
from modules.sentiment import get_sentiment_analysis
from modules.risk import get_risk_analysis
import uvicorn

app = FastAPI(title="Indian Equity Intelligence Backend")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models for Schema
class SentimentHeadline(BaseModel):
    headline: str
    sentiment_score: float

class SentimentData(BaseModel):
    headlines: List[SentimentHeadline]
    average_polarity: float
    aggregated_sentiment: str

class TechnicalData(BaseModel):
    RSI: Optional[float]
    SMA: Dict[str, Optional[float]]
    Support_6M: Optional[float]
    Resistance_6M: Optional[float]

class FundamentalData(BaseModel):
    PE_Ratio: Optional[float]
    Debt_to_Equity: Optional[float]
    Price_to_Book: Optional[float]
    ROE: Optional[float]
    Dividend_Yield: Optional[float]
    Market_Cap: str

class RiskData(BaseModel):
    Beta: Optional[float]
    Distance_from_52W_High_Percent: Optional[float]
    Distance_from_52W_Low_Percent: Optional[float]
    High_Debt_Flag: bool
    Debt_to_Equity_Raw: Optional[float]

class AnalysisResponse(BaseModel):
    ticker: str
    technical: TechnicalData
    fundamental: FundamentalData
    sentiment: SentimentData
    risk: RiskData

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Indian Equity Intelligence Backend is running"}

@app.get("/analyze", response_model=AnalysisResponse)
def analyze_stock(ticker: str = Query(..., description="Ticker symbol (e.g. RELIANCE.NS)")):
    """
    Analyzes a stock ticker and returns a 360-degree view.
    """
    try:
        # Technical Analysis
        tech_data = calculate_technical_indicators(ticker)
        if "error" in tech_data:
            raise HTTPException(status_code=404, detail=f"Technical data failed: {tech_data['error']}")
            
        # Fundamental Analysis
        fund_data = get_fundamental_analysis(ticker)
        if "error" in fund_data:
            raise HTTPException(status_code=404, detail=f"Fundamental data failed: {fund_data['error']}")

        # Sentiment Analysis
        sent_data = get_sentiment_analysis(ticker)
        # News might be empty, but we don't want to fail the whole analysis
        if "error" in sent_data:
            sent_data = {
                "headlines": [],
                "average_polarity": 0,
                "aggregated_sentiment": "N/A"
            }

        # Risk Analysis
        risk_data = get_risk_analysis(ticker)
        if "error" in risk_data:
            raise HTTPException(status_code=404, detail=f"Risk data failed: {risk_data['error']}")

        return AnalysisResponse(
            ticker=ticker.upper(),
            technical=tech_data,
            fundamental=fund_data,
            sentiment=sent_data,
            risk=risk_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
