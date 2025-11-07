from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from dotenv import load_dotenv

# Load environment variables (for Salesforce creds)
load_dotenv()

app = FastAPI()

# Allow your WordPress domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://staging-da31-prachitglobal.wpcomstaging.com",  # your WP site
        "https://prachitglobal.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FastAPI backend is live on Render!"}


@app.post("/form")
async def handle_form(request: Request):
    data = await request.json()
    print("Received form data:", data)

    # Extract form data
    name = data.get("name")
    zip_code = data.get("zip")
    phone = data.get("phone")
    company = data.get("company")
    email = data.get("email")
    preferences = data.get("preferences")

    # Optional: validation
    if not name or not email:
        return {"status": "error", "message": "Name and email are required."}

    # Prepare Salesforce data payload
    salesforce_payload = {
        "Name": name,
        "Email": email,
        "Phone": phone,
        "Company": company,
        "ZIP_Code__c": zip_code,
        "Product_Preferences__c": preferences
    }

    try:
        # Example Salesforce API call (replace with your real endpoint + token)
        sf_url = os.getenv("SALESFORCE_API_URL")  # e.g. https://your-instance.salesforce.com/services/data/vXX.X/sobjects/Lead/
        sf_token = os.getenv("SALESFORCE_ACCESS_TOKEN")

        headers = {
            "Authorization": f"Bearer {sf_token}",
            "Content-Type": "application/json"
        }

        # Send data to Salesforce
        response = requests.post(sf_url, headers=headers, json=salesforce_payload)

        if response.status_code in [200, 201]:
            return {"status": "success", "message": "Data sent to Salesforce successfully!"}
        else:
            return {
                "status": "error",
                "message": "Salesforce API failed",
                "details": response.text
            }

    except Exception as e:
        print("Error:", e)
        return {"status": "error", "message": str(e)}
