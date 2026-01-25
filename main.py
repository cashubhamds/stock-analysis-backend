from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from modules.technical import calculate_technical_indicators
from modules.fundamental import get_fundamental_analysis
from modules.sentiment import get_sentiment_analysis
from modules.risk import get_risk_analysis
from datetime import datetime, time
import pytz
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

def is_indian_market_open():
    """Checks if the Indian stock market (NSE/BSE) is currently open."""
    # Market hours: 9:15 AM - 3:30 PM IST, Mon-Fri
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Weekends (Saturday=5, Sunday=6)
    if now.weekday() >= 5:
        return "Closed (Weekend)"
    
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    if market_start <= now <= market_end:
        return "Open 🟢"
    else:
        return "Closed (Market Hours: 9:15 AM - 3:30 PM IST)"

# Pydantic Models for v3.1 Schema
class TechnicalOutput(BaseModel):
    score: int
    rsi: Optional[float]
    trend: str
    macd: Optional[str]
    sma_trend: Optional[str]
    bb_position: Optional[str]
    support: Optional[float]
    resistance: Optional[float]

class FundamentalOutput(BaseModel):
    score: int
    pe: Optional[float]
    peg_ratio: Optional[float]
    debt_equity: Optional[float]
    roe: Optional[float]

class SentimentOutput(BaseModel):
    score: int
    headlines: List[str]

class AnalysisResponse(BaseModel):
    ticker: str
    price: Optional[float]
    overall_score: int
    signal: str
    technical: TechnicalOutput
    fundamental: FundamentalOutput
    sentiment: SentimentOutput
    market_status: str
    verdict: str
    rationale: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Stock Alpha Analyst v3.1 Engine is running"}

@app.get("/analyze", response_model=AnalysisResponse)
def analyze_stock(ticker: str = Query(..., description="Ticker symbol (e.g. RELIANCE.NS)")):
    """
    Analyzes a stock ticker using the v3.1 Engine logic.
    """
    try:
        # 1. Extraction
        tech_data = calculate_technical_indicators(ticker)
        fund_data = get_fundamental_analysis(ticker)
        sent_data = get_sentiment_analysis(ticker)
        
        # Validation: If both major sources fail, the ticker likely doesn't exist
        if "error" in tech_data and ("error" in fund_data or fund_data.get("price") is None):
            raise HTTPException(
                status_code=404, 
                detail=f"Stock ticker '{ticker.upper()}' not found. Please check the symbol (e.g., RELIANCE.NS for NSE stocks)."
            )
        
        # 2. Logic & Scoring
        
        # Technical Score
        rsi = tech_data.get("RSI")
        tech_score = 40
        trend = "Neutral"
        if rsi is not None:
            if 40 <= rsi <= 60:
                tech_score = 80
                trend = "Bullish"
            elif rsi > 60:
                trend = "Overbought"
            else:
                trend = "Oversold"
        
        # Fundamental Score
        de_ratio = fund_data.get("Debt_to_Equity")
        fund_score = 50
        if de_ratio is not None and de_ratio < 1:
            fund_score = 90
            
        # Sentiment Score
        headlines = [h['headline'] for h in sent_data.get("headlines", [])]
        avg_polarity = sent_data.get("average_polarity", 0)
        sent_score = int((avg_polarity + 1) * 50) # Scale -1 to 1 to 0 to 100
        
        # Overall Score
        overall_score = int((tech_score * 0.4) + (fund_score * 0.4) + (sent_score * 0.2))
        
        # Signal & Verdict
        if overall_score > 80:
            signal = "STRONG BUY"
            verdict = "TREASURE 💎"
        elif overall_score > 60:
            signal = "BUY"
            verdict = "TREASURE 💎"
        elif overall_score > 40:
            signal = "HOLD"
            verdict = "TRAP ⚠️"
        else:
            signal = "SELL"
            verdict = "TRAP ⚠️"
            
        # Rationale (CA-style)
        pe = fund_data.get("PE_Ratio")
        peg = fund_data.get("PEG_Ratio")
        roe = fund_data.get("ROE")
        rationale = f"Based on our analysis, {ticker.upper()} currently shows a {trend} technical trend with an RSI of {rsi if rsi else 'N/A'}. "
        rationale += f"Fundamentally, the company carries a Debt-to-Equity ratio of {de_ratio if de_ratio else 'N/A'}, "
        if de_ratio is not None and de_ratio < 1:
            rationale += "indicating a healthy balance sheet. "
        else:
            rationale += "which warrants caution regarding leverage. "
        if pe:
            rationale += f"The P/E ratio stands at {pe}, reflecting current market valuation. "
        rationale += f"Combining these factors with a sentiment score of {sent_score}, our professional verdict is that this stock is a {verdict}."

        return AnalysisResponse(
            ticker=ticker.upper(),
            price=fund_data.get("price") or tech_data.get("current_price"),
            overall_score=overall_score,
            signal=signal,
            technical=TechnicalOutput(
                score=tech_score, 
                rsi=rsi, 
                trend=trend,
                macd=tech_data.get("MACD_Signal"),
                sma_trend=tech_data.get("SMA_Trend"),
                bb_position=tech_data.get("BB_Position"),
                support=tech_data.get("Support"),
                resistance=tech_data.get("Resistance")
            ),
            fundamental=FundamentalOutput(
                score=fund_score, 
                pe=pe, 
                peg_ratio=peg,
                debt_equity=de_ratio,
                roe=roe
            ),
            sentiment=SentimentOutput(score=sent_score, headlines=headlines[:5]),
            market_status=is_indian_market_open(),
            verdict=verdict,
            rationale=rationale
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
