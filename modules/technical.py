import yfinance as yf
import numpy as np

def calculate_technical_indicators(ticker_symbol: str, period: str = "1y") -> dict:
    """
    Calculates RSI, Support/Resistance levels, and SMA for a given ticker.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        history = ticker.history(period=period)
        
        if history.empty:
            return {"error": "No historical data found"}

        # Calculate RSI (14)
        delta = history['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        history['RSI'] = 100 - (100 / (1 + rs))
        current_rsi = history['RSI'].iloc[-1]

        # Calculate SMAs
        history['SMA_20'] = history['Close'].rolling(window=20).mean()
        history['SMA_50'] = history['Close'].rolling(window=50).mean()
        history['SMA_200'] = history['Close'].rolling(window=200).mean()
        
        current_smas = {
            "SMA_20": history['SMA_20'].iloc[-1],
            "SMA_50": history['SMA_50'].iloc[-1],
            "SMA_200": history['SMA_200'].iloc[-1]
        }

        # Calculate Support & Resistance (Windowed Min/Max over 6 months approx 126 days)
        # Using a simple window approach to find local min/max
        
        # We'll take the last 6 months of data
        six_month_data = history.tail(126)
        
        # Simple algorithm: Find local mins and maxs
        # A more robust way for "zones" might be grouping, but for now we'll take
        # the absolute min and max of the last 6 months as major support/resistance
        support_level = six_month_data['Low'].min()
        resistance_level = six_month_data['High'].max()

        return {
            "RSI": current_rsi if not np.isnan(current_rsi) else None,
            "SMA": {k: v if not np.isnan(v) else None for k, v in current_smas.items()},
            "Support_6M": support_level,
            "Resistance_6M": resistance_level
        }
    except Exception as e:
        return {"error": str(e)}
