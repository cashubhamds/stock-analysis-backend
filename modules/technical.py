import yfinance as yf
import numpy as np
import pandas as pd

def calculate_technical_indicators(ticker_symbol: str, period: str = "1y") -> dict:
    """
    Calculates RSI, MACD, Bollinger Bands, and SMA for a given ticker.
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

        # Calculate MACD
        exp1 = history['Close'].ewm(span=12, adjust=False).mean()
        exp2 = history['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()
        current_macd = macd.iloc[-1]
        current_signal = signal_line.iloc[-1]

        # Calculate Bollinger Bands
        history['SMA_20'] = history['Close'].rolling(window=20).mean()
        history['STD_20'] = history['Close'].rolling(window=20).std()
        history['Upper_BB'] = history['SMA_20'] + (history['STD_20'] * 2)
        history['Lower_BB'] = history['SMA_20'] - (history['STD_20'] * 2)
        
        current_price = history['Close'].iloc[-1]
        upper_bb = history['Upper_BB'].iloc[-1]
        lower_bb = history['Lower_BB'].iloc[-1]
        
        # BB Position
        if current_price > upper_bb:
            bb_pos = "Overbought"
        elif current_price < lower_bb:
            bb_pos = "Oversold"
        else:
            bb_pos = "Neutral"

        # SMA Trend (last 50 vs last 200)
        sma_50 = history['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = history['Close'].rolling(window=200).mean().iloc[-1]
        sma_trend = "Bullish" if sma_50 > sma_200 else "Bearish"

        return {
            "RSI": round(current_rsi, 2) if not np.isnan(current_rsi) else None,
            "MACD_Signal": "Buy" if current_macd > current_signal else "Sell",
            "SMA_Trend": sma_trend,
            "BB_Position": bb_pos,
            "current_price": current_price
        }
    except Exception as e:
        return {"error": str(e)}
