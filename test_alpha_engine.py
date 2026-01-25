import requests
import json

def test_analyze():
    url = "http://127.0.0.1:8000/analyze?ticker=RELIANCE.NS"
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2))
            
            # Validation
            required_keys = ["ticker", "price", "overall_score", "signal", "technical", "fundamental", "sentiment", "verdict", "rationale"]
            for key in required_keys:
                if key in data:
                    print(f"✅ Found key: {key}")
                else:
                    print(f"❌ Missing key: {key}")
            
            if data["ticker"] == "RELIANCE.NS":
                 print("✅ Ticker is correct")
            else:
                 print(f"❌ Ticker mismatch: {data['ticker']}")
                 
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_analyze()
