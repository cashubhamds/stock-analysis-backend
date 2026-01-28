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

# Pydantic Models for v3.4 Schema (Ultra Financials & Master Analysis)

class Officer(BaseModel):
    name: str
    title: str

class CompanyInfo(BaseModel):
    name: str
    full_name: Optional[str] = None
    industry: Optional[str]
    sector: Optional[str]
    summary: Optional[str]
    industry_pe: Optional[str]
    officers: List[Officer]

class FinancialResult(BaseModel):
    period: str
    revenue: str
    operating_profit: str
    net_profit: str

class TechnicalBollinger(BaseModel):
    upper: float
    lower: float
    position: str

class TechnicalSuperTrend(BaseModel):
    signal: str
    value: float

class TimeframeAnalysis(BaseModel):
    daily: str
    weekly: str
    monthly: str

class TechnicalOutput(BaseModel):
    score: int
    rsi: Optional[float]
    trend: str
    macd: str
    bollinger: TechnicalBollinger
    super_trend: TechnicalSuperTrend
    support: float
    resistance: float
    timeframe_analysis: TimeframeAnalysis

class FundamentalOutput(BaseModel):
    score: int
    pe: Optional[float]
    industry_pe: Optional[str]
    peg_ratio: Optional[float]
    debt_equity: Optional[float]
    roe: Optional[float]
    roce: Optional[float]
    intrinsic_value: Optional[float]
    market_cap: str
    dividend_yield: Optional[float]

class SentimentOutput(BaseModel):
    score: int
    headlines: List[str]

class AnalysisResponse(BaseModel):
    ticker: str
    company_info: CompanyInfo
    current_price: Optional[float]
    closing_price: Optional[float]
    overall_score: int
    signal: str
    technical: TechnicalOutput
    fundamental: FundamentalOutput
    sentiment: SentimentOutput
    quarterly_results: List[FinancialResult]
    annual_results: List[FinancialResult]
    market_status: str
    is_market_open: bool
    verdict: str
    rationale: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Stock Alpha Analyst v3.4 Engine is running"}

@app.get("/analyze", response_model=AnalysisResponse)
def analyze_stock(ticker: str = Query(..., description="Ticker symbol (e.g. RELIANCE.NS)")):
    """
    Analyzes a stock ticker using the v3.4 Engine logic.
    """
    try:
        # 1. Multi-source Extraction
        tech_data = calculate_technical_indicators(ticker)
        fund_data = get_fundamental_analysis(ticker)
        sent_data = get_sentiment_analysis(ticker)
        
        # Validation
        if "error" in fund_data:
             raise HTTPException(status_code=404, detail=f"Stock ticker '{ticker.upper()}' not found.")
        
        # 2. Market Environment
        m_status = is_indian_market_open()
        is_open = "Open 🟢" in m_status
        
        # 3. Financial Formatting (Crores)
        def to_cr(val):
            return f"{val/10**7:.2f} Cr" if val and not np.isnan(val) else "N/A"

        formatted_q = [
            FinancialResult(
                period=q['period'],
                revenue=to_cr(q['revenue']),
                operating_profit=to_cr(q['operating_profit']),
                net_profit=to_cr(q['net_profit'])
            ) for q in fund_data.get("quarterly_results", [])
        ]
        
        formatted_a = [
            FinancialResult(
                period=a['period'],
                revenue=to_cr(a['revenue']),
                operating_profit=to_cr(a['operating_profit']),
                net_profit=to_cr(a['net_profit'])
            ) for a in fund_data.get("annual_results", [])
        ]

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
        expert_rationale = f"Technical View: The stock is showing a {tf.get('daily')} trend on the daily chart and a {tf.get('weekly')} trend on the weekly chart. "
        if tf.get('daily') == tf.get('weekly') == tf.get('monthly'):
            expert_rationale += f"There is rare multi-timeframe alignment signaling a powerful {tf.get('daily')} phase. "
        elif "Bullish" in tf.get('daily') and "Bearish" in tf.get('weekly'):
            expert_rationale += "We are seeing a potential bullish reversal on the short-term chart despite long-term pressure. "
        else:
            expert_rationale += f"The monthly chart remains {tf.get('monthly')}, indicating overall sideways or trending behavior. "
            
        expert_rationale += f"Fundamental View: With an ROCE of {roce:.2f}% if available else N/A and an Intrinsic Value of {metrics.get('intrinsic_value'):.2f}, "
        expert_rationale += f"the stock is technically {st_signal}. Overall Verdict: {verdict}."

        price = metrics.get("price")

        return AnalysisResponse(
            ticker=ticker.upper(),
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
                bollinger=TechnicalBollinger(**tech_data.get("Bollinger")),
                super_trend=TechnicalSuperTrend(**tech_data.get("SuperTrend")),
                support=tech_data.get("Support"),
                resistance=tech_data.get("Resistance"),
                timeframe_analysis=TimeframeAnalysis(**tf)
            ),
            fundamental=FundamentalOutput(
                score=fund_score,
                pe=metrics.get("pe_ratio"),
                industry_pe=str(metrics.get("industry_pe")),
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
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
