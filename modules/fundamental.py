import yfinance as yf
import numpy as np
import math
from .utils import format_crores

def get_fundamental_analysis(ticker_symbol: str) -> dict:
    """
    Extracts comprehensive fundamental data for v3.4 Engine.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        if not info or ('regularMarketPrice' not in info and 'currentPrice' not in info):
            return {"error": "Too many requests or data unavailable"}

        current_price = info.get('current_price') or info.get('currentPrice') or info.get('regularMarketPrice')
        
        # 1. Company Metadata
        company_data = {
            "name": info.get('longName'),
            "ticker": ticker_symbol.upper(),
            "industry": info.get('industry'),
            "sector": info.get('sector'),
            "summary": info.get('longBusinessSummary'),
            "industry_pe": info.get('industryKey'), # Some tickers have industryKey or industry
            "officers": []
        }
        
        if info.get('companyOfficers'):
            for officer in info.get('companyOfficers')[:3]: # Top 3
                company_data["officers"].append({
                    "name": officer.get('name'),
                    "title": officer.get('title')
                })

        # 2. Key Ratios (v3.4 additions)
        # yfinance debtToEquity is in percentage (e.g. 150 = 1.5)
        raw_de = info.get('debtToEquity')
        de_ratio = raw_de / 100.0 if raw_de is not None else None
        
        # Intrinsic Value (Graham Number) = sqrt(22.5 * EPS * BVPS)
        eps = info.get('trailingEps')
        bvps = info.get('bookValue')
        intrinsic_value = None
        if eps and bvps and eps > 0 and bvps > 0:
            intrinsic_value = math.sqrt(22.5 * eps * bvps)

        # ROCE Calculation = EBIT / (Total Assets - Current Liabilities)
        roce = None
        try:
            ebit = ticker.financials.loc['EBIT'].iloc[0] if 'EBIT' in ticker.financials.index else None
            assets = ticker.balance_sheet.loc['Total Assets'].iloc[0] if 'Total Assets' in ticker.balance_sheet.index else None
            curr_liab = ticker.balance_sheet.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in ticker.balance_sheet.index else 0
            
            if ebit and assets and (assets - curr_liab) > 0:
                roce = (ebit / (assets - curr_liab)) * 100
        except:
            pass

        # 3. Quarterly (4 Quarters)
        quarterly_results = []
        qf = ticker.quarterly_financials
        if not qf.empty:
            qf_t = qf.T.head(4)
            for index, row in qf_t.iterrows():
                quarterly_results.append({
                    "period": index.strftime('%b %Y'),
                    "revenue": row.get('Total Revenue'),
                    "operating_profit": row.get('Operating Income'),
                    "net_profit": row.get('Net Income')
                })

        # 4. Annual (3 Years)
        annual_results = []
        af = ticker.financials
        if not af.empty:
            af_t = af.T.head(3)
            for index, row in af_t.iterrows():
                annual_results.append({
                    "period": index.strftime('%Y'),
                    "revenue": row.get('Total Revenue'),
                    "operating_profit": row.get('Operating Income'),
                    "net_profit": row.get('Net Income')
                })

        return {
            "company_info": company_data,
            "metrics": {
                "price": current_price,
                "pe_ratio": info.get('trailingPE'),
                "industry_pe": info.get('trailingPE'), # Placeholder if industry specific PE not found
                "peg_ratio": info.get('pegRatio'),
                "debt_to_equity": de_ratio,
                "roe": info.get('returnOnEquity'),
                "roce": roce,
                "intrinsic_value": intrinsic_value,
                "market_cap": format_crores(info.get('marketCap')),
                "dividend_yield": info.get('dividendYield')
            },
            "quarterly_results": quarterly_results,
            "annual_results": annual_results
        }
    except Exception as e:
        return {"error": str(e)}
