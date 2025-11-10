from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import random, string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def mock_resolve_customer(token: str):
    fake_customer_id = "cust-" + "".join(random.choices(string.ascii_lowercase, k=6))
    fake_account_id = "".join(random.choices("0123456789", k=12))
    fake_product_code = "prod-" + "".join(random.choices(string.ascii_lowercase, k=4))

    return {
        "CustomerIdentifier": fake_customer_id,
        "ProductCode": fake_product_code,
        "AccountId": fake_account_id,
        "TokenReceived": token
    }

@app.post("/resolve-customer")
async def resolve_customer(x_amzn_marketplace_token: str = Form(...)):
    aws_info = mock_resolve_customer(x_amzn_marketplace_token)
    return JSONResponse(content={"status": "resolved", "aws_customer": aws_info})

@app.post("/submit-form")
async def submit_form(request: Request):
    data = await request.json()
    print("Received form submission:", data)
    sf_response = {
        "status": "success",
        "message": "Data received by mock Salesforce endpoint",
        "received_data": data
    }
    return JSONResponse(content=sf_response)

@app.get("/")
def home():
    return {"message": "Backend running successfully!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
