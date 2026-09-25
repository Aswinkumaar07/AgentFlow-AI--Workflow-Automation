import asyncio
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_and_generate_workflow():
    print("\n================================================================================")
    print("        AUTHENTICATION & GENERATE WORKFLOW HTTP STATUS 200 VERIFICATION        ")
    print("================================================================================\n")

    # Step 1: Login Request
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@agentflow.ai", "password": "password123"})
    print(f"1. Login HTTP Status Code: {login_res.status_code}")
    assert login_res.status_code == 200
    token_data = login_res.json()
    print(f"2. Token Payload Received: success={token_data.get('success')}")

    token = token_data.get("data", {}).get("access_token", "demo_jwt_token_12345")
    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Generate Workflow Request with Token Header
    gen_res = client.post("/api/v1/ai/generate", json={"prompt": "Send good morning email"}, headers=headers)
    print(f"3. Generate Workflow HTTP Status Code: {gen_res.status_code}")
    assert gen_res.status_code == 200

    wf_data = gen_res.json()
    print(f"4. Generate Response Data Received:")
    print(json.dumps(wf_data, indent=2))

    print("\n================================================================================")
    print(" VERIFIED: POST /api/v1/ai/generate returns HTTP 200 OK without 401 Logout! ")
    print("================================================================================\n")

if __name__ == "__main__":
    test_auth_and_generate_workflow()
