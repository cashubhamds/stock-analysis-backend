from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def run_tests():
    out_dir = r"C:\Users\HP\.gemini\antigravity\brain\4a48ccae-538a-4903-8611-6437b8290ad8\\"
    
    # 1. Valid
    response_valid = client.get("/analyze?ticker=RELIANCE.NS")
    with open(out_dir + "success_sample.json", "w") as f:
        json.dump(response_valid.json(), f, indent=2)

    # 2. Invalid
    response_invalid = client.get("/analyze?ticker=INVALID TICKER")
    with open(out_dir + "error_sample.json", "w") as f:
        json.dump(response_invalid.json(), f, indent=2)

    # 3. Partial / Empty Data
    response_empty = client.get("/analyze?ticker=INVALIDTICKER123.NS")
    with open(out_dir + "partial_sample.json", "w") as f:
        json.dump(response_empty.json(), f, indent=2)

if __name__ == "__main__":
    run_tests()
