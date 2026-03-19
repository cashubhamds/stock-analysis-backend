from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def run_tests():
    print("Testing Valid Ticker: RELIANCE.NS")
    response_valid = client.get("/analyze?ticker=RELIANCE.NS")
    print(f"Status: {response_valid.status_code}")
    print(json.dumps(response_valid.json(), indent=2))
    print("="*50)

    print("Testing Invalid Ticker Format: INVALID TICKER")
    response_invalid = client.get("/analyze?ticker=INVALID TICKER")
    print(f"Status: {response_invalid.status_code}")
    print(json.dumps(response_invalid.json(), indent=2))
    print("="*50)

    print("Testing Empty/Unsupported Ticker: PREMIERENE.NS")
    response_empty = client.get("/analyze?ticker=PREMIERENE.NS")
    print(f"Status: {response_empty.status_code}")
    print(json.dumps(response_empty.json(), indent=2))
    print("="*50)

if __name__ == "__main__":
    run_tests()
