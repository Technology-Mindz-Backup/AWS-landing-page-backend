from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import random, string, os, uuid, time, threading, json, requests

# --- FastAPI setup ---
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Setup static + templates
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Session management ---
SESSION_FILE = "sessions.json"
SESSION_EXPIRATION = 3600  

if not os.path.exists(SESSION_FILE):
    with open(SESSION_FILE, "w") as f:
        json.dump({}, f)

def load_sessions():
    with open(SESSION_FILE, "r") as f:
        return json.load(f)

def save_sessions(sessions):
    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f)

def add_session(session_id, token):
    sessions = load_sessions()
    sessions[session_id] = {"token": token, "created_at": time.time()}
    save_sessions(sessions)

def get_session(session_id):
    sessions = load_sessions()
    session = sessions.get(session_id)
    if not session:
        return None
    if time.time() - session["created_at"] > SESSION_EXPIRATION:
        delete_session(session_id)
        return None
    return session

def delete_session(session_id):
    sessions = load_sessions()
    if session_id in sessions:
        del sessions[session_id]
        save_sessions(sessions)

def cleanup_sessions():
    while True:
        sessions = load_sessions()
        now = time.time()
        changed = False
        for sid, sdata in list(sessions.items()):
            if now - sdata["created_at"] > SESSION_EXPIRATION:
                del sessions[sid]
                changed = True
        if changed:
            save_sessions(sessions)
        time.sleep(600)

threading.Thread(target=cleanup_sessions, daemon=True).start()

# --- AWS Customer Resolve ---
def resolve_customer(token: str):
    """Simulates AWS ResolveCustomer API."""
    customer_id = "cust-" + "".join(random.choices(string.ascii_lowercase, k=6))
    account_id = "".join(random.choices("0123456789", k=12))
    product_code = "prod-" + "".join(random.choices(string.ascii_lowercase, k=4))
    return {
        "CustomerIdentifier": customer_id,
        "ProductCode": product_code,
        "AccountId": account_id,
        "TokenReceived": token
    }

@app.post("/resolve-customer")
async def resolve_customer_api(x_amzn_marketplace_token: str = Form(...)):
    aws_info = resolve_customer(x_amzn_marketplace_token)
    return JSONResponse(content={"status": "resolved", "aws_customer": aws_info})

# --- Salesforce Submission ---
@app.post("/submit-form")
async def submit_form(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    if not session_id:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Missing session_id"}
        )

    session = get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid or expired session_id"}
        )

    print(f"✅ Received form submission for session {session_id}")

    # Resolve AWS data using stored token
    aws_data = resolve_customer(session["token"])

    # Format JSON to Salesforce structure
    sf_payload = {
        "awsCustomerId": aws_data["CustomerIdentifier"],
        "awsAccountId": aws_data["AccountId"],
        "productCode": aws_data["ProductCode"],
        "subscriptionStatus": "Active",
        "zipCode": data.get("zip"),
        "phoneNumber": data.get("phone"),
        "companyInformation": data.get("company"),
        "email": data.get("email"),
        "productSetupPreferences": data.get("preferences")
    }

    print("📦 Sending data to Salesforce:", json.dumps(sf_payload, indent=2))

    # Salesforce endpoint
    SF_ENDPOINT = "https://technologymindz-dev-ed.my.site.com/awspublicapi/services/apexrest/TechnologyMindz/aws/receiveData"

    try:
        sf_response = requests.post(SF_ENDPOINT, json=sf_payload, timeout=10)
        sf_response.raise_for_status()
        response_data = sf_response.json() if sf_response.text else {"message": "No JSON returned"}
    except Exception as e:
        print("❌ Error sending data to Salesforce:", e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Failed to send data to Salesforce: {str(e)}"}
        )

    # Delete session after success
    delete_session(session_id)

    return JSONResponse(
        content={
            "status": "success",
            "message": "Data sent to Salesforce successfully!",
            "salesforce_response": response_data
        }
    )

# --- Homepage ---
@app.get("/", response_class=HTMLResponse)
async def homepage(
    request: Request,
    x_amzn_marketplace_token: str = Query(None, alias="x-amzn-marketplace-token")
):
    session_id = str(uuid.uuid4())

    print(f"Session ID: {session_id}, Token received: {x_amzn_marketplace_token}")

    if x_amzn_marketplace_token:
        add_session(session_id, x_amzn_marketplace_token)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "token": x_amzn_marketplace_token or "",
            "session_id": session_id,
            "title": "AWS Marketplace Subscription Landing"
        }
    )

# --- Run app ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
