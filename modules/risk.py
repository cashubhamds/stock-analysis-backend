import yfinance as yf

def get_risk_analysis(ticker_symbol: str) -> dict:
    """
    Calculates Beta, 52-Week High/Low distance, and Debt flag.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        fifty_two_week_high = info.get('fiftyTwoWeekHigh')
        fifty_two_week_low = info.get('fiftyTwoWeekLow')
        beta = info.get('beta')
        debt_to_equity = info.get('debtToEquity') # yfinance often gives this in % (e.g. 150 = 1.5)

        high_distance = None
        low_distance = None
        
        if current_price and fifty_two_week_high:
            high_distance = ((fifty_two_week_high - current_price) / fifty_two_week_high) * 100
            
        if current_price and fifty_two_week_low:
            low_distance = ((current_price - fifty_two_week_low) / fifty_two_week_low) * 100

        high_debt_flag = False
        if debt_to_equity is not None:
            # yfinance info['debtToEquity'] is usually (Total Debt / Equity) * 100.
            # Example: 35.65 means 0.3565 ratio.
            # The requirement says "High Debt" if Debt/Equity > 2.0.
            # So if debt_to_equity (from yfinance) > 200, it's High Debt.
            if debt_to_equity > 200:
                high_debt_flag = True
            # Also handle if yfinance returns it as a direct ratio (rare)
            elif 2.0 < debt_to_equity < 10: 
                # This is ambiguous, but let's assume if it's small but > 2.0, 
                # it's the direct ratio.
                high_debt_flag = True

        return {
            "Beta": beta,
            "Distance_from_52W_High_Percent": round(high_distance, 2) if high_distance is not None else None,
            "Distance_from_52W_Low_Percent": round(low_distance, 2) if low_distance is not None else None,
            "High_Debt_Flag": high_debt_flag,
            "Debt_to_Equity_Raw": debt_to_equity
        }
    except Exception as e:
        return {"error": str(e)}
