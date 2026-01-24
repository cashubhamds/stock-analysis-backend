from textblob import TextBlob
import yfinance as yf

def get_sentiment_analysis(ticker_symbol: str) -> dict:
    """
    Scrapes the latest headlines and analyzes sentiment using TextBlob.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.news
        
        if not news:
            return {"error": "No news headlines found"}

        headlines = []
        total_polarity = 0
        
        # Take the latest 5 headlines
        for item in news[:5]:
            # Handle both old and new yfinance news structures
            content = item.get('content', {})
            title = content.get('title') or item.get('title', '')
            
            if not title:
                continue
                
            analysis = TextBlob(title)
            polarity = analysis.sentiment.polarity
            
            headlines.append({
                "headline": title,
                "sentiment_score": round(polarity, 2)
            })
            total_polarity += polarity

        avg_polarity = total_polarity / len(headlines) if headlines else 0
        
        if avg_polarity > 0.1:
            aggregated_sentiment = "Bullish"
        elif avg_polarity < -0.1:
            aggregated_sentiment = "Bearish"
        else:
            aggregated_sentiment = "Neutral"

        return {
            "headlines": headlines,
            "average_polarity": round(avg_polarity, 2),
            "aggregated_sentiment": aggregated_sentiment
        }
    except Exception as e:
        return {"error": str(e)}
