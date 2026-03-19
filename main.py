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
import numpy as np
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Pydantic Models for v3.4 Schema

class Officer(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None

class CompanyInfo(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    summary: Optional[str] = None
    industry_pe: Optional[str] = None
    officers: Optional[List[Officer]] = []

class FinancialResult(BaseModel):
    period: str
    revenue: Optional[str] = None
    operating_profit: Optional[str] = None
    net_profit: Optional[str] = None

class TechnicalBollinger(BaseModel):
    upper: Optional[float] = None
    lower: Optional[float] = None
    position: Optional[str] = None

class TechnicalSuperTrend(BaseModel):
    signal: Optional[str] = None
    value: Optional[float] = None

class TimeframeAnalysis(BaseModel):
    daily: Optional[str] = None
    weekly: Optional[str] = None
    monthly: Optional[str] = None

class TechnicalOutput(BaseModel):
    score: int
    rsi: Optional[float] = None
    trend: Optional[str] = None
    macd: Optional[str] = None
    bollinger: Optional[TechnicalBollinger] = None
    super_trend: Optional[TechnicalSuperTrend] = None
    support: Optional[float] = None
    resistance: Optional[float] = None
    timeframe_analysis: Optional[TimeframeAnalysis] = None

class FundamentalOutput(BaseModel):
    score: int
    pe: Optional[float] = None
    industry_pe: Optional[str] = None
    peg_ratio: Optional[float] = None
    debt_equity: Optional[float] = None
    roe: Optional[float] = None
    roce: Optional[float] = None
    intrinsic_value: Optional[float] = None
    market_cap: Optional[str] = None
    dividend_yield: Optional[float] = None

class SentimentOutput(BaseModel):
    score: int
    headlines: Optional[List[str]] = []

class AnalysisResponse(BaseModel):
    success: bool
    partial: bool
    error_code: Optional[str] = None
    message: Optional[str] = None
    display_message: Optional[str] = None
    warnings: List[str] = []
    meta: Optional[Dict] = None

    ticker: str
    company_info: Optional[CompanyInfo] = None
    current_price: Optional[float] = None
    closing_price: Optional[float] = None
    overall_score: Optional[int] = None
    signal: Optional[str] = None
    technical: Optional[TechnicalOutput] = None
    fundamental: Optional[FundamentalOutput] = None
    sentiment: Optional[SentimentOutput] = None
    quarterly_results: Optional[List[FinancialResult]] = []
    annual_results: Optional[List[FinancialResult]] = []
    market_status: Optional[str] = None
    is_market_open: Optional[bool] = None
    verdict: Optional[str] = None
    rationale: Optional[str] = None

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Stock Alpha Analyst v3.4 Engine is running"}

@app.get("/analyze", response_model=AnalysisResponse)
def analyze_stock(ticker: str = Query(..., description="Ticker symbol (e.g. RELIANCE.NS)")):
    """
    Analyzes a stock ticker using the v3.4 Engine logic.
    """
    logger.info(f"Received request for ticker: {ticker}")
    ticker_original = ticker
    
    # 0. Input validation
    ticker = ticker.strip().upper()
    if not re.match(r'^[A-Z0-9\-\.]+$', ticker):
        logger.warning(f"Invalid symbol format: {ticker}")
        return AnalysisResponse(
            success=False,
            partial=False,
            ticker=ticker,
            error_code="INVALID_SYMBOL_FORMAT",
            message="Ticker format is invalid.",
            display_message=f"Invalid format for ticker '{ticker_original}'.",
            meta={"timestamp_utc": datetime.utcnow().isoformat()}
        )

    warnings = []
    partial = False
    
    try:
        # 1. Multi-source Extraction
        logger.info(f"[{ticker}] Fetching technical data...")
        tech_data = calculate_technical_indicators(ticker)
        
        if "error" in tech_data:
            logger.error(f"[{ticker}] Technical data error: {tech_data['error']}")
            return AnalysisResponse(
                success=False,
                partial=False,
                ticker=ticker,
                error_code="SYMBOL_NOT_FOUND",
                message="No market data found for this ticker.",
                display_message=f"No market data found for {ticker}",
                meta={"timestamp_utc": datetime.utcnow().isoformat()}
            )
            
        logger.info(f"[{ticker}] Fetching fundamental data...")
        fund_data = get_fundamental_analysis(ticker)
        if "error" in fund_data:
             logger.warning(f"[{ticker}] Fundamental data error: {fund_data['error']}")
             warnings.append(f"Fundamentals unavailable: {fund_data['error']}")
             partial = True
             fund_data = {}  # Default to empty structure
        
        logger.info(f"[{ticker}] Fetching sentiment data...")
        sent_data = get_sentiment_analysis(ticker)
        if "error" in sent_data:
             logger.warning(f"[{ticker}] Sentiment data error: {sent_data['error']}")
             warnings.append(f"News sentiment unavailable: {sent_data['error']}")
             partial = True
             sent_data = {}
        
        # 2. Market Environment
        m_status = is_indian_market_open()
        is_open = "Open 🟢" in m_status
        
        # 3. Financial Formatting (Crores)
        def to_cr(val):
            return f"{val/10**7:.2f} Cr" if val and not np.isnan(val) else "N/A"

        formatted_q = []
        for q in fund_data.get("quarterly_results", []):
            formatted_q.append(FinancialResult(
                period=q.get('period', 'N/A'),
                revenue=to_cr(q.get('revenue')),
                operating_profit=to_cr(q.get('operating_profit')),
                net_profit=to_cr(q.get('net_profit'))
            ))
            
        formatted_a = []
        for a in fund_data.get("annual_results", []):
            formatted_a.append(FinancialResult(
                period=a.get('period', 'N/A'),
                revenue=to_cr(a.get('revenue')),
                operating_profit=to_cr(a.get('operating_profit')),
                net_profit=to_cr(a.get('net_profit'))
            ))

        # 4. Expert Scoring Logic
        # Technical Score
        rsi = tech_data.get("RSI")
        tech_score = 50
        st_signal = tech_data.get("SuperTrend", {}).get("signal")
        if st_signal == "Bullish": tech_score += 20
        if rsi and 40 <= rsi <= 60: tech_score += 15
        
        # Fundamental Score
        metrics = fund_data.get("metrics", {})
        fund_score = 50
        de = metrics.get("debt_to_equity")
        roce = metrics.get("roce")
        if de and de < 1: fund_score += 20
        if roce and roce > 15: fund_score += 20
        
        # Sentiment
        sent_score = int((sent_data.get("average_polarity", 0) + 1) * 50)
        
        overall_score = int((tech_score * 0.4) + (fund_score * 0.4) + (sent_score * 0.2))
        overall_score = min(max(overall_score, 0), 100)
        
        if overall_score > 70: signal, verdict = "STRONG BUY", "TREASURE 💎"
        elif overall_score > 50: signal, verdict = "BUY", "TREASURE 💎"
        elif overall_score > 40: signal, verdict = "HOLD", "TRAP ⚠️"
        else: signal, verdict = "SELL", "TRAP ⚠️"

        # 5. Trading Expert Analysis (Multi-timeframe)
        tf = tech_data.get("timeframe_analysis", {})
        expert_rationale = f"Technical View: The stock is showing a {tf.get('daily', 'Neutral')} trend on the daily chart and a {tf.get('weekly', 'Neutral')} trend on the weekly chart. "
        if tf.get('daily') == tf.get('weekly') == tf.get('monthly') and tf.get('daily') not in [None, "N/A"]:
            expert_rationale += f"There is rare multi-timeframe alignment signaling a powerful {tf.get('daily')} phase. "
        elif tf.get('daily') and "Bullish" in tf.get('daily') and tf.get('weekly') and "Bearish" in tf.get('weekly'):
            expert_rationale += "We are seeing a potential bullish reversal on the short-term chart despite long-term pressure. "
        else:
            expert_rationale += f"The monthly chart remains {tf.get('monthly', 'Neutral')}, indicating overall sideways or trending behavior. "
            
        roce_val = f"{roce:.2f}%" if roce else "N/A"
        iv_val = f"{metrics.get('intrinsic_value'):.2f}" if metrics.get('intrinsic_value') else "N/A"
        
        expert_rationale += f"Fundamental View: With an ROCE of {roce_val} and an Intrinsic Value of {iv_val}, "
        expert_rationale += f"the stock is technically {st_signal}. Overall Verdict: {verdict}."

        price = metrics.get("price") or tech_data.get("current_price")

        response = AnalysisResponse(
            success=True,
            partial=partial,
            warnings=warnings,
            meta={"timestamp_utc": datetime.utcnow().isoformat()},
            ticker=ticker,
            company_info=fund_data.get("company_info"),
            current_price=price if is_open else None,
            closing_price=price if not is_open else None,
            overall_score=overall_score,
            signal=signal,
            technical=TechnicalOutput(
                score=tech_score,
                rsi=rsi,
                trend=tf.get("daily", "Neutral"),
                macd=tech_data.get("MACD_Signal"),
                bollinger=TechnicalBollinger(**tech_data.get("Bollinger", {})),
                super_trend=TechnicalSuperTrend(**tech_data.get("SuperTrend", {})),
                support=tech_data.get("Support"),
                resistance=tech_data.get("Resistance"),
                timeframe_analysis=TimeframeAnalysis(**tf)
            ),
            fundamental=FundamentalOutput(
                score=fund_score,
                pe=metrics.get("pe_ratio"),
                industry_pe=str(metrics.get("industry_pe")) if metrics.get("industry_pe") else None,
                peg_ratio=metrics.get("peg_ratio"),
                debt_equity=metrics.get("debt_to_equity"),
                roe=metrics.get("roe"),
                roce=metrics.get("roce"),
                intrinsic_value=metrics.get("intrinsic_value"),
                market_cap=metrics.get("market_cap"),
                dividend_yield=metrics.get("dividend_yield")
            ),
            sentiment=SentimentOutput(
                score=sent_score,
                headlines=[h['headline'] for h in sent_data.get("headlines", [])[:5]]
            ),
            quarterly_results=formatted_q,
            annual_results=formatted_a,
            market_status=m_status,
            is_market_open=is_open,
            verdict=verdict,
            rationale=expert_rationale
        )
        
        logger.info(f"[{ticker}] Analysis complete. Success={response.success}, Partial={response.partial}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{ticker}] Unhandled exception in analyze_stock: {e}", exc_info=True)
        # Fallback for unexpected errors instead of raw 500 if possible, but 500 is fine for true crashes 
        # as requested "500 only for true backend server failures".
        raise HTTPException(status_code=500, detail="Internal server error during analysis")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
