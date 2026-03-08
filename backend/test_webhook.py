import requests
import json

def simulate_message(text_claim):
    url = "http://localhost:8000/webhook"
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "919876543210",
                        "type": "text",
                        "text": { "body": text_claim }
                    }]
                }
            }]
        }]
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("\n✅ Check your Dashboard now! The claim should appear there.")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure your backend is running (python main.py)")

if __name__ == "__main__":
    claim = input("Enter a factual claim to test: ")
    if not claim:
        claim = "Drinking hot water cures COVID-19."
    simulate_message(claim)
