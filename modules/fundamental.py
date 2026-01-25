import yfinance as yf
from .utils import format_crores, get_session

def get_fundamental_analysis(ticker_symbol: str) -> dict:
    """
    Extracts key ratios and market cap for a given ticker.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info:
             # If .info fails but doesn't raise exception, it might return empty dict or generic metadata
             return {"error": "Too many requests or data unavailable"}

        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        # yfinance debtToEquity is usually in percentage (e.g. 150.0 for 1.5 ratio)
        raw_debt_equity = info.get('debtToEquity')
        debt_equity_ratio = raw_debt_equity / 100.0 if raw_debt_equity is not None else None

        return {
            "price": current_price,
            "PE_Ratio": info.get('trailingPE'),
            "PEG_Ratio": info.get('pegRatio'),
            "Debt_to_Equity": debt_equity_ratio,
            "Price_to_Book": info.get('priceToBook'),
            "ROE": info.get('returnOnEquity'),
            "Dividend_Yield": info.get('dividendYield'),
            "Market_Cap": format_crores(info.get('marketCap'))
        }
    except Exception as e:
        return {"error": str(e)}
