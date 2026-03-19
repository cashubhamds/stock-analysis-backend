import yfinance as yf
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def calculate_atr(df, period=14):
    if len(df) < period:
        return pd.Series(index=df.index, dtype=float)
    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift())
    low_cp = np.abs(df['Low'] - df['Close'].shift())
    df_tr = pd.concat([high_low, high_cp, low_cp], axis=1)
    true_range = np.max(df_tr, axis=1)
    atr = true_range.rolling(period).mean()
    return atr

def calculate_supertrend(df, period=10, multiplier=3):
    if len(df) < period:
        return None, None, None
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

        # Defensive check for minimum days
        if len(d_hist) < 20:
             logger.warning(f"[{ticker_symbol}] Less than 20 days of data found, some indicators may be null.")

        # 2. Indicators (on Daily)
        # RSI
        current_rsi = None
        if len(d_hist) >= 15:
            delta = d_hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            d_hist['RSI'] = 100 - (100 / (1 + rs))
            current_rsi = d_hist['RSI'].iloc[-1]

        # MACD
        macd_signal = "Neutral"
        if len(d_hist) >= 26:
            exp1 = d_hist['Close'].ewm(span=12, adjust=False).mean()
            exp2 = d_hist['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=9, adjust=False).mean()
            macd_signal = "Buy" if macd.iloc[-1] > signal_line.iloc[-1] else "Sell"

        # Bollinger Bands
        upper_bb_val = None
        lower_bb_val = None
        bb_pos = "Neutral"
        current_price = d_hist['Close'].iloc[-1]

        if len(d_hist) >= 20:
            sma_20 = d_hist['Close'].rolling(window=20).mean()
            std_20 = d_hist['Close'].rolling(window=20).std()
            upper_bb = sma_20 + (std_20 * 2)
            lower_bb = sma_20 - (std_20 * 2)
            upper_bb_val = upper_bb.iloc[-1]
            lower_bb_val = lower_bb.iloc[-1]
            bb_pos = "Overbought" if current_price > upper_bb_val else "Oversold" if current_price < lower_bb_val else "Neutral"
        
        # SuperTrend
        st_signal, st_ub, st_lb = calculate_supertrend(d_hist)

        # 3. Support & Resistance
        support = d_hist['Low'].tail(30).min() if not d_hist.empty else None
        resistance = d_hist['High'].tail(30).max() if not d_hist.empty else None

        # 4. Expert Multi-timeframe Summary
        timeframe_signals = {
            "daily": get_trend_signal(d_hist),
            "weekly": get_trend_signal(w_hist),
            "monthly": get_trend_signal(m_hist)
        }

        return {
            "RSI": round(current_rsi, 2) if current_rsi is not None and not np.isnan(current_rsi) else None,
            "MACD_Signal": macd_signal,
            "Bollinger": {
                "upper": round(upper_bb_val, 2) if upper_bb_val is not None and not np.isnan(upper_bb_val) else None,
                "lower": round(lower_bb_val, 2) if lower_bb_val is not None and not np.isnan(lower_bb_val) else None,
                "position": bb_pos
            },
            "SuperTrend": {
                "signal": "Bullish" if st_signal else "Bearish" if st_signal is False else "Neutral",
                "value": round(st_lb if st_signal else st_ub, 2) if st_signal is not None and not np.isnan(st_lb if st_signal else st_ub) else None
            },
            "Support": round(support, 2) if support is not None and not np.isnan(support) else None,
            "Resistance": round(resistance, 2) if resistance is not None and not np.isnan(resistance) else None,
            "current_price": current_price,
            "timeframe_analysis": timeframe_signals
        }
    except Exception as e:
        logger.error(f"[{ticker_symbol}] Technical fetch error: {e}", exc_info=True)
        return {"error": str(e)}
