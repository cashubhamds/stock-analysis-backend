import yfinance as yf
from .utils import format_crores

def get_fundamental_analysis(ticker_symbol: str) -> dict:
    """
    Extracts key ratios and market cap for a given ticker.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        return {
            "PE_Ratio": info.get('trailingPE'),
            "Debt_to_Equity": info.get('debtToEquity'),
            "Price_to_Book": info.get('priceToBook'),
            "ROE": info.get('returnOnEquity'),
            "Dividend_Yield": info.get('dividendYield'),
            "Market_Cap": format_crores(info.get('marketCap'))
        }
    except Exception as e:
        return {"error": str(e)}
