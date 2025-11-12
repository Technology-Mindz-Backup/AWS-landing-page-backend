import requests

BASE_URL = "http://localhost:8000"

def test_homepage_with_token():
    """Step 1: Simulate AWS redirect with a token"""
    token = "mock-token-abc123"
    url = f"{BASE_URL}/?x-amzn-marketplace-token={token}"
    response = requests.get(url)
    print("\n--- Step 1: Homepage ---")
    print("Status:", response.status_code)
    assert response.status_code == 200
    assert token in response.text  # the token should appear in the HTML

    return token


def test_resolve_customer(token):
    """Step 2: Send token to /resolve-customer and receive AWS customer info"""
    form_data = {"x_amzn_marketplace_token": token}
    response = requests.post(f"{BASE_URL}/resolve-customer", data=form_data)
    print("\n--- Step 2: Resolve Customer ---")
    print("Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert "aws_customer" in data

    return data["aws_customer"]


def test_submit_form(aws_customer):
    """Step 3: Submit mock user info + AWS customer details to /submit-form"""
    payload = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "company": "ExampleCorp",
        "aws_customer": aws_customer
    }
    response = requests.post(f"{BASE_URL}/submit-form", json=payload)
    print("\n--- Step 3: Submit Form ---")
    print("Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "received_data" in data

    return data


def run_full_flow_test():
    print("🚀 Running AWS Marketplace → Salesforce full integration test")
    token = test_homepage_with_token()
    aws_info = test_resolve_customer(token)
    final_response = test_submit_form(aws_info)
    print("\n✅ Flow completed successfully!")
    return final_response


if __name__ == "__main__":
    run_full_flow_test()
