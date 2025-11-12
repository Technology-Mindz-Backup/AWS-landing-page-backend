from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import random, string, os, uuid, time, threading, json

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

# Ensure session file exists
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
    sessions[session_id] = {
        "token": token,
        "created_at": time.time()
    }
    save_sessions(sessions)

def get_session(session_id):
    sessions = load_sessions()
    session = sessions.get(session_id)
    if not session:
        return None
    # Check expiration
    if time.time() - session["created_at"] > SESSION_EXPIRATION:
        delete_session(session_id)
        return None
    return session

def delete_session(session_id):
    sessions = load_sessions()
    if session_id in sessions:
        del sessions[session_id]
        save_sessions(sessions)

# Background cleanup thread
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
        time.sleep(600)  # every 10 minutes

threading.Thread(target=cleanup_sessions, daemon=True).start()


# --- Mock AWS Customer Resolve ---
def mock_resolve_customer(token: str):
    """Mock AWS resolve call (simulates AWS ResolveCustomer API)."""
    fake_customer_id = "cust-" + "".join(random.choices(string.ascii_lowercase, k=6))
    fake_account_id = "".join(random.choices("0123456789", k=12))
    fake_product_code = "prod-" + "".join(random.choices(string.ascii_lowercase, k=4))
    return {
        "CustomerIdentifier": fake_customer_id,
        "ProductCode": fake_product_code,
        "AccountId": fake_account_id,
        "TokenReceived": token
    }


# --- AWS Resolve Endpoint ---
@app.post("/resolve-customer")
async def resolve_customer(x_amzn_marketplace_token: str = Form(...)):
    aws_info = mock_resolve_customer(x_amzn_marketplace_token)
    return JSONResponse(content={"status": "resolved", "aws_customer": aws_info})


# --- Salesforce Submission  ---
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

    print(f"Received Salesforce submission for session {session_id}: {data}")

    # Combine stored token with submitted data
    combined_data = {
        **data,
        "aws_customer": mock_resolve_customer(session["token"])
    }

    # Delete session after successful submission
    delete_session(session_id)

    sf_response = {
        "status": "success",
        "message": "Data received successfully!",
        "combined_data": combined_data
    }
    return JSONResponse(content=sf_response)


# --- Homepage ---
@app.get("/", response_class=HTMLResponse)
async def homepage(
    request: Request,
    session_id: str = Query(None),  # Optional now
    x_amzn_marketplace_token: str = Query(None, alias="x-amzn-marketplace-token")
):
    # Generate a unique session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    print(f"Session ID: {session_id}, Token received: {x_amzn_marketplace_token}")

    # Store token per session if provided
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
