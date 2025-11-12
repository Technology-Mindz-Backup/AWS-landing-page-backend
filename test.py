import requests
import json

# --- Salesforce Endpoint ---
SF_ENDPOINT = "https://technologymindz-dev-ed.my.site.com/awspublicapi/services/apexrest/TechnologyMindz/aws/receiveData"

# --- Example Salesforce Payload ---
sf_payload = {
    "awsCustomerId": "cust-abc123",
    "awsAccountId": "123456789012",
    "productCode": "prod-demo1",
    "subscriptionStatus": "Active",
    "zipCode": "94107",
    "phoneNumber": "+1-555-123-4567",
    "companyInformation": "TechnologyMindz Test Company",
    "email": "testuser@example.com"
}

# --- Optional Headers (Salesforce may require these) ---
headers = {
    "Content-Type": "application/json",
}

# --- Send POST Request ---
print(f"📤 Sending data to Salesforce: {SF_ENDPOINT}\n")
print(json.dumps(sf_payload, indent=2))

try:
    response = requests.post(SF_ENDPOINT, headers=headers, json=sf_payload, timeout=15)
    response.raise_for_status()

    print("\n✅ Successfully received response from Salesforce!")
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:\n", json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print("Response Text:\n", response.text)

except requests.exceptions.HTTPError as e:
    print("❌ HTTP error:", e)
    print("Response text:", response.text)
except requests.exceptions.RequestException as e:
    print("❌ Request failed:", e)
