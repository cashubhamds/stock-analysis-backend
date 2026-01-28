import yfinance as yf
import numpy as np
import pandas as pd

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift())
    low_cp = np.abs(df['Low'] - df['Close'].shift())
    df_tr = pd.concat([high_low, high_cp, low_cp], axis=1)
    true_range = np.max(df_tr, axis=1)
    atr = true_range.rolling(period).mean()
    return atr

def calculate_supertrend(df, period=10, multiplier=3):
    atr = calculate_atr(df, period)
    hl2 = (df['High'] + df['Low']) / 2
    final_ub = hl2 + (multiplier * atr)
    final_lb = hl2 - (multiplier * atr)
    
    supertrend = [True] * len(df)
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > final_ub.iloc[i-1]:
            supertrend[i] = True
        elif df['Close'].iloc[i] < final_lb.iloc[i-1]:
            supertrend[i] = False
        else:
            supertrend[i] = supertrend[i-1]
            if supertrend[i] and final_lb.iloc[i] < final_lb.iloc[i-1]:
                final_lb.iloc[i] = final_lb.iloc[i-1]
            if not supertrend[i] and final_ub.iloc[i] > final_ub.iloc[i-1]:
                final_ub.iloc[i] = final_ub.iloc[i-1]
    
    return supertrend[-1], final_ub.iloc[-1], final_lb.iloc[-1]

def get_trend_signal(df):
    if df.empty or len(df) < 20:
        return "N/A"
    sma_20 = df['Close'].rolling(window=20).mean().iloc[-1]
    current_price = df['Close'].iloc[-1]
    if current_price > sma_20 * 1.05:
        return "Strong Bullish"
    elif current_price > sma_20:
        return "Bullish"
    elif current_price < sma_20 * 0.95:
        return "Strong Bearish"
    else:
        return "Bearish"

def calculate_technical_indicators(ticker_symbol: str) -> dict:
    """
    Calculates detailed technical indicators for v3.4 Engine.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # 1. Multi-timeframe Analysis
        # Daily
        d_hist = ticker.history(period="60d", interval="1d")
        # Weekly
        w_hist = ticker.history(period="6mo", interval="1wk")
        # Monthly
        m_hist = ticker.history(period="2y", interval="1mo")
        
        if d_hist.empty:
            return {"error": "No historical data found"}

        # 2. Indicators (on Daily)
        # RSI
        delta = d_hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        d_hist['RSI'] = 100 - (100 / (1 + rs))
        current_rsi = d_hist['RSI'].iloc[-1]

        # MACD
        exp1 = d_hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = d_hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_signal = "Buy" if macd.iloc[-1] > signal_line.iloc[-1] else "Sell"

        # Bollinger Bands
        sma_20 = d_hist['Close'].rolling(window=20).mean()
        std_20 = d_hist['Close'].rolling(window=20).std()
        upper_bb = sma_20 + (std_20 * 2)
        lower_bb = sma_20 - (std_20 * 2)
        current_price = d_hist['Close'].iloc[-1]
        
        # SuperTrend
        st_signal, st_ub, st_lb = calculate_supertrend(d_hist)

        # 3. Support & Resistance
        support = d_hist['Low'].tail(30).min()
        resistance = d_hist['High'].tail(30).max()

        # 4. Expert Multi-timeframe Summary
        timeframe_signals = {
            "daily": get_trend_signal(d_hist),
            "weekly": get_trend_signal(w_hist),
            "monthly": get_trend_signal(m_hist)
        }

        return {
            "RSI": round(current_rsi, 2) if not np.isnan(current_rsi) else None,
            "MACD_Signal": macd_signal,
            "Bollinger": {
                "upper": round(upper_bb.iloc[-1], 2),
                "lower": round(lower_bb.iloc[-1], 2),
                "position": "Overbought" if current_price > upper_bb.iloc[-1] else "Oversold" if current_price < lower_bb.iloc[-1] else "Neutral"
            },
            "SuperTrend": {
                "signal": "Bullish" if st_signal else "Bearish",
                "value": round(st_lb if st_signal else st_ub, 2)
            },
            "Support": round(support, 2),
            "Resistance": round(resistance, 2),
            "current_price": current_price,
            "timeframe_analysis": timeframe_signals
        }
    except Exception as e:
        return {"error": str(e)}
