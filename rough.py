from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import random, string

app = FastAPI(title="Mock AWS Marketplace")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# The URL of your *real* backend (the one with /resolve-customer and /submit-form)
REAL_BACKEND_URL = "http://localhost:8000"

def generate_mock_token():
    """Generate a fake AWS marketplace token"""
    return "mock-token-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=12))


@app.get("/", response_class=HTMLResponse)
async def aws_home():
    return """
    <h2>Mock AWS Marketplace</h2>
    <form action="/subscribe" method="post">
      <label>Name:</label><br>
      <input name="name"><br><br>
      <label>Email:</label><br>
      <input name="email"><br><br>
      <button type="submit">Subscribe Now</button>
    </form>
    """

@app.post("/subscribe")
async def subscribe(name: str = Form(...), email: str = Form(...)):
    token = generate_mock_token()
    print(f"Generated token for {name}: {token}")
    
    # ✅ This is the critical line — must match exactly
    redirect_url = f"http://localhost:8001/?x-amzn-marketplace-token={token}"
    
    print(f"Redirecting user to {redirect_url}")
    return RedirectResponse(url=redirect_url, status_code=302)


@app.get("/health")
async def health():
    return {"status": "ok", "message": "Mock AWS running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
