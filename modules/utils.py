import requests

def get_session():
    """
    Returns a requests session with a User-Agent to prevent rate-limiting by Yahoo Finance.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

def format_crores(value: float) -> str:
    """
    Formats a large number into Crores.
    """
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value / 10**7:.2f} Cr"
