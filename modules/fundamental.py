import yfinance as yf
from .utils import format_crores, get_session

def get_fundamental_analysis(ticker_symbol: str) -> dict:
    """
    Extracts key ratios and market cap for a given ticker.
    """
    try:
        session = get_session()
        ticker = yf.Ticker(ticker_symbol, session=session)
        info = ticker.info
        
        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info:
             # If .info fails but doesn't raise exception, it might return empty dict or generic metadata
             return {"error": "Too many requests or data unavailable"}

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
