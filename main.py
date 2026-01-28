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

# Pydantic Models for v3.3 Schema (Max Compatibility)
class QuarterlyResult(BaseModel):
    period: str
    revenue: str
    operating_profit: str
    net_profit: str
    # Aliases for different frontend expectations
    revenue_cr: Optional[str] = None
    profit_cr: Optional[str] = None

class TechnicalZones(BaseModel):
    support: Optional[float]
    resistance: Optional[float]

class TechnicalOutput(BaseModel):
    score: int
    rsi: Optional[float]
    trend: str
    macd: Optional[str]
    sma_trend: Optional[str]
    bb_position: Optional[str]
    zones: TechnicalZones
    # Legacy top-level fields for compatibility
    support: Optional[float] = None
    resistance: Optional[float] = None

class FundamentalOutput(BaseModel):
    score: int
    pe: Optional[float]
    peg_ratio: Optional[float]
    debt_equity: Optional[float]
    roe: Optional[float]
    # Aliases
    pegRatio: Optional[float] = None
    debtEquity: Optional[float] = None
    peRatio: Optional[float] = None

class SentimentOutput(BaseModel):
    score: int
    headlines: List[str]

class AnalysisResponse(BaseModel):
    ticker: str
    price: Optional[float] # Restored legacy field
    current_price: Optional[float]
    closing_price: Optional[float]
    overall_score: int
    signal: str
    technical: TechnicalOutput
    fundamental: FundamentalOutput
    sentiment: SentimentOutput
    quarterly_results: List[QuarterlyResult]
    quarterlyResults: Optional[List[QuarterlyResult]] = None # CamelCase alias
    market_status: str
    is_market_open: bool
    verdict: str
    rationale: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Stock Alpha Analyst v3.3 Engine is running"}

@app.get("/analyze", response_model=AnalysisResponse)
def analyze_stock(ticker: str = Query(..., description="Ticker symbol (e.g. RELIANCE.NS)")):
    """
    Analyzes a stock ticker using the v3.3 Engine logic (Compatible with all UI versions).
    """
    try:
        # 1. Extraction
        tech_data = calculate_technical_indicators(ticker)
        fund_data = get_fundamental_analysis(ticker)
        sent_data = get_sentiment_analysis(ticker)
        
        # Validation
        if "error" in tech_data and ("error" in fund_data or fund_data.get("price") is None):
            raise HTTPException(
                status_code=404, 
                detail=f"Stock ticker '{ticker.upper()}' not found."
            )
        
        # 2. Market Info
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        is_open = False
        m_status = "Closed"
        
        if now.weekday() < 5:
            m_start = now.replace(hour=9, minute=15, second=0)
            m_end = now.replace(hour=15, minute=30, second=0)
            if m_start <= now <= m_end:
                is_open = True
                m_status = "Open 🟢"
            else:
                m_status = "Closed"
        else:
            m_status = "Closed (Weekend)"

        # 3. Logic & Scoring
        
        # Technical
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
        
        # Fundamental
        de_ratio = fund_data.get("Debt_to_Equity")
        fund_score = 50
        if de_ratio is not None and de_ratio < 1:
            fund_score = 90
            
        # Sentiment
        headlines = [h['headline'] for h in sent_data.get("headlines", [])]
        avg_polarity = sent_data.get("average_polarity", 0)
        sent_score = int((avg_polarity + 1) * 50)
        
        overall_score = int((tech_score * 0.4) + (fund_score * 0.4) + (sent_score * 0.2))
        
        if overall_score > 60:
            signal, verdict = "BUY", "TREASURE 💎"
        elif overall_score > 40:
            signal, verdict = "HOLD", "TRAP ⚠️"
        else:
            signal, verdict = "SELL", "TRAP ⚠️"
            
        # Quarterly Results Formatting (to Crores)
        formatted_q = []
        raw_q = fund_data.get("quarterly_results", [])
        for q in raw_q:
            rev_cr = f"{q['revenue']/10**7:.2f} Cr" if q['revenue'] else "N/A"
            profit_cr = f"{q['net_profit']/10**7:.2f} Cr" if q['net_profit'] else "N/A"
            formatted_q.append(QuarterlyResult(
                period=q['period'],
                revenue=rev_cr,
                operating_profit=f"{q['operating_profit']/10**7:.2f} Cr" if q['operating_profit'] else "N/A",
                net_profit=profit_cr,
                revenue_cr=rev_cr,
                profit_cr=profit_cr
            ))

        price = fund_data.get("price") or tech_data.get("current_price")
        support = tech_data.get("Support")
        resistance = tech_data.get("Resistance")
        
        return AnalysisResponse(
            ticker=ticker.upper(),
            price=price, # Legacy price field
            current_price=price if is_open else None,
            closing_price=price if not is_open else None,
            overall_score=overall_score,
            signal=signal,
            technical=TechnicalOutput(
                score=tech_score, 
                rsi=rsi, 
                trend=trend,
                macd=tech_data.get("MACD_Signal"),
                sma_trend=tech_data.get("SMA_Trend"),
                bb_position=tech_data.get("BB_Position"),
                zones=TechnicalZones(support=support, resistance=resistance),
                support=support, # Legacy
                resistance=resistance # Legacy
            ),
            fundamental=FundamentalOutput(
                score=fund_score, 
                pe=fund_data.get("PE_Ratio"), 
                peg_ratio=fund_data.get("PEG_Ratio"),
                debt_equity=de_ratio,
                roe=fund_data.get("ROE"),
                pegRatio=fund_data.get("PEG_Ratio"),
                debtEquity=de_ratio,
                peRatio=fund_data.get("PE_Ratio")
            ),
            sentiment=SentimentOutput(score=sent_score, headlines=headlines[:5]),
            quarterly_results=formatted_q,
            quarterlyResults=formatted_q, # Legacy/Alias
            market_status=m_status,
            is_market_open=is_open,
            verdict=verdict,
            rationale=f"Based on our analysis, {ticker.upper()} currently shows a {trend} technical trend. Fundamentally, the company carries a Debt-to-Equity ratio of {de_ratio if de_ratio else 'N/A'}. Verdict: {verdict}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
