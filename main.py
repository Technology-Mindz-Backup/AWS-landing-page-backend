from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Allow your WordPress domain to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace * with your WordPress domain later for security
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1️⃣ Handle POST — when user submits the form
@app.post("/api/salesforce")
async def receive_form(request: Request):
    data = await request.json()
    print("✅ Received form data:", data)

    # Example: send data to Salesforce API (pseudo example)
    try:
        salesforce_url = "https://your-instance.salesforce.com/services/data/vXX.X/sobjects/Lead"
        headers = {
            "Authorization": "Bearer YOUR_SF_ACCESS_TOKEN",
            "Content-Type": "application/json"
        }

        response = requests.post(salesforce_url, json=data, headers=headers)

        return {
            "message": "Form data received and sent to Salesforce!",
            "salesforce_status": response.status_code
        }

    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}

# 2️⃣ Handle GET — if AWS sends data or you need to regenerate something
@app.get("/api/aws-data")
def get_aws_data():
    try:
        # Example call to AWS API (replace with real AWS endpoint)
        aws_url = "https://your-aws-endpoint.amazonaws.com/data"
        response = requests.get(aws_url)
        data = response.json()
        return {"message": "Data fetched from AWS", "aws_data": data}
    except Exception as e:
        return {"error": str(e)}
